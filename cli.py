import click
import json, os, tempfile, click, logging
from imap_tools import MailBox
from dotenv import load_dotenv
from prettytable import PrettyTable
from datetime import datetime
from openai import OpenAI
import json, rich, streamlit as st



LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)5s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

client = OpenAI(max_retries=6, timeout=600)


def extract_body(msg):
    """
    Return a reasonably clean text body for a MailMessage.
    • Prefer the plain‑text part if present.
    • Otherwise strip tags from the HTML part
    """
    if msg.text:
        return msg.text.strip()
    else:
        return msg.html.strip()

def build_database(emails):
    """
    • Creates a vector‑store named "email_db_<timestamp>".
    • Serialises each message into its own JSON file (no JSONL).
    • Uploads all the files in one batch and waits until indexing is done.
    • Cleans up temporary files and returns the vector‑store ID.
    """
    if not emails:
        raise ValueError("No email messages supplied")

    # 1. Create an empty store
    vstore = client.vector_stores.create(name="email_db")

    # 2. Write every email into an individual temp file
    tmp_paths = []
    for m in emails:
        body = extract_body(m)
        record = {
            "text": (
                f"Subject: {m.subject}\n"
                f"From: {m.from_}\n"
                f"Date: {m.date}\n\n"
                f"{body}"
            ),
            "metadata": {
                "subject": m.subject,
                "from":    m.from_,
                "date":    m.date.isoformat(),
            },
        }
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
            json.dump(record, tmp)
            tmp_paths.append(tmp.name)           # keep path for later reopen

    # 3. Open all files → hand the streams to the helper
    file_streams = [open(p, "rb") for p in tmp_paths]
    try:
        client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vstore.id,
            files=file_streams,
        )
    finally:
        # 4‑A. Close file handles
        for fs in file_streams:
            fs.close()
        # 4‑B. Remove temp files from disk
        for p in tmp_paths:
            try:
                os.remove(p)
            except OSError:
                pass

    return vstore.id

def get_env_var(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def fetch_emails(unread=False, limit=50):
    """Connect to the inbox and fetch emails based on filters."""
    host = get_env_var("IMAP_HOST")
    user = get_env_var("IMAP_USER")
    password = get_env_var("IMAP_PASSWORD")

    criteria = "UNSEEN" if unread else "ALL"

    with MailBox(host).login(user, password) as mailbox:
        return list(mailbox.fetch(criteria, limit=limit, reverse=True))


def display_emails(emails):
    if not emails:
        click.echo("No emails found.")
    else:
        # Create table
        table = PrettyTable()
        table.field_names = ["Date", "From", "Subject", "Size"]
        table.align["Date"] = "l"
        table.align["Subject"] = "l"  # Left align subject
        table.align["From"] = "l"  # Left align from
        table.align["Size"] = "l"  # Right align size

        for email in emails:
            print(email)
            # Format date
            date = email.date.strftime("%Y-%m-%d %H:%M")
            # Format size (convert bytes to KB)
            size = f"{email.size / 1024:.1f} KB"
            # Truncate subject if too long
            subject = (
                email.subject[:50] + "..." if len(email.subject) > 50 else email.subject
            )

            table.add_row([date, email.from_, subject, size])

        # Print table
        click.echo(table)


@click.group()
def cli():
    """A basic CLI application."""
    pass


@cli.command()
def hello():
    """Print a greeting."""
    click.echo("Hello, World!")


@cli.command(name="list")
@click.option("--unread", is_flag=True, help="List only unread emails")
@click.option(
    "--limit", default=50, show_default=True, help="Limit the number of emails to list"
)
def list_emails(unread, limit):
    """List emails from the inbox with options for unread and limit."""
    try:
        emails = fetch_emails(unread=unread, limit=limit)
        log.info("Retrieved emails.")
        v_id = build_database(emails)
        log.info("Built database.")
        resp = client.responses.create(
            model="o3-mini",
            input="I am a hungry student. Give me emails related to promotions that will give me discounts on food. Return these emails in a table and cite the emails you reference.",
            tools=[{"type": "file_search",
                    "vector_store_ids": [v_id]}]
        )

        
        display_emails(emails)

        resp_json = json.loads(resp.model_dump_json())
        rich.print_json(data=resp_json)        # terminal
        # or
        st.json(resp_json)   
        files = client.vector_stores.files.list(vector_store_id=v_id).data
        for f in files:
            client.vector_stores.files.delete(vector_store_id=v_id, file_id=f.id)
            client.files.delete(f.id) 

    except ValueError as e:
        click.echo(click.style(f"Config Error: {e}", fg="red"))
    except Exception as e:
        click.echo(click.style(f"An error occurred: {e}", fg="red"))


if __name__ == "__main__":
    cli()
