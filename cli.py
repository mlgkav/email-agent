"""Email CLI tool for querying emails using RAG."""
from typing import List
import click
import json, click, logging
from datetime import datetime
from imap_tools import MailBox, MailMessage
from prettytable import PrettyTable
import rich
from config import get_env_var, OPENAI_CLIENT, STORE_NAME
from vector_db import EmailVectorStoreManager, OpenAIVectorBackend

log = logging.getLogger(__name__)

def fetch_emails(unread: bool = False, limit: int = 50) -> List[MailMessage]:
    """Pull *limit* messages from the inbox and return them as ``MailMessage`` objects."""
    host = get_env_var("IMAP_HOST")
    user = get_env_var("IMAP_USER")
    password = get_env_var("IMAP_PASSWORD")

    criteria = "UNSEEN" if unread else "ALL"
    with MailBox(host).login(user, password) as mailbox:
        return list(mailbox.fetch(criteria, limit=limit, reverse=True))

def display_emails(msgs: List[MailMessage]):
    if not msgs:
        click.echo("No emails found.")
        return

    tbl = PrettyTable()
    tbl.field_names = ["Date", "From", "Subject", "Size"]
    for k in tbl.field_names:
        tbl.align[k] = "l"

    for msg in msgs:
        date = msg.date.strftime("%Y-%m-%d %H:%M") if isinstance(msg.date, datetime) else "?"
        size = f"{msg.size / 1024:.1f} KB"
        subject = (msg.subject or "(no subject)")
        if len(subject) > 50:
            subject = subject[:47] + "…"
        tbl.add_row([date, msg.from_, subject, size])

    click.echo(tbl)

def summarize_with_gpt(emails_with_content):
    """Summarize emails using GPT."""
    try:
        # Prepare email content for summarization
        email_texts = []
        for email in emails_with_content:
            email_texts.append(
                f"Date: {email.date}\n"
                f"From: {email.from_}\n"
                f"Subject: {email.subject}\n"
                f"Content: {email.txt or email.html or ''}"
            )

        combined_emails = "\n\n---\n\n".join(email_texts)

        response = OPENAI_CLIENT.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes emails. Provide concise summaries focusing on key points and action items.",
                },
                {
                    "role": "user",
                    "content": f"Please summarize these emails:\n\n{combined_emails}",
                },
            ],
        )

        return response.choices[0].message.content
    except Exception as e:
        raise click.ClickException(f"Error summarizing emails: {str(e)}")


@click.group()
def cli():
    """Email CLI tool for reading and managing emails."""
    pass


@cli.command()
def hello():
    """Print a greeting message."""
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
        display_emails(emails)

    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

@cli.command("ingest")
@click.option("--unread", is_flag=True, help="Ingest only unread messages")
@click.option("--limit", default=50, show_default=True, help="Maximum messages to ingest")
def ingest_emails(unread: bool, limit: int):
    """Fetch e‑mails and upload them into the vector store (deduplicated)."""
    click.echo(f"✉️  Fetching up to {limit} message(s) from IMAP …")
    msgs = fetch_emails(unread=unread, limit=limit)
    if not msgs:
        click.echo("Nothing to ingest – inbox empty.")
        return

    manager = EmailVectorStoreManager(store_name=STORE_NAME)

    added = 0
    for msg in msgs:
        metadata = {
            "from": msg.from_,
            "subject": msg.subject,
            "date": msg.date.isoformat() if isinstance(msg.date, datetime) else "",
        }
        manager.add_message(msg, metadata=metadata)
        added += 1

    click.echo(
        click.style(
            f"✅  Ingestion complete – {added} message(s) stored in vector store “{STORE_NAME}” (ID={manager.get_vector_store_id()}).",
            fg="green",
        )
    )

@cli.command("query")
@click.argument("prompt", nargs=-1)
def query_emails(prompt: tuple[str, ...]):
    """Ask questions about the *already‑ingested* email corpus.

    Example::

        email‑cli query "show marketing emails with lunch coupons from the past month"
    """
    if not prompt:
        raise click.ClickException("Please provide a query prompt.")
    user_prompt = " ".join(prompt)
    print(user_prompt)

    manager = EmailVectorStoreManager(store_name=STORE_NAME)
    vs_id = manager.get_vector_store_id()

    click.echo("🤖  Running RAG query against vector store …")
    try:
        response = OPENAI_CLIENT.responses.create(
            model="o3-mini",
            input=f"{user_prompt}. Return these emails in a table and cite the emails you reference.",
            tools=[{"type": "file_search", "vector_store_ids": [vs_id]}],
        )
        rich.print_json(data=json.loads(response.model_dump_json()))
    except Exception as exc:
        raise click.ClickException(f"Query failed: {exc}") from exc


@cli.command("store-list")
def list_store():
    """Display all files currently stored in the selected vector store."""
    manager = EmailVectorStoreManager(store_name=STORE_NAME)
    backend = manager.backend

    if not isinstance(backend, OpenAIVectorBackend):
        raise click.ClickException("Listing is only supported for the OpenAI backend.")

    vs_id = manager.get_vector_store_id()
    files = backend.client.vector_stores.files.list(vector_store_id=vs_id, limit=100).data

    if not files:
        click.echo("Vector store is empty.")
        return

    tbl = PrettyTable()
    tbl.field_names = ["File ID", "From", "Subject", "Date"]
    for k in tbl.field_names:
        tbl.align[k] = "l"

    for f in files:
        meta = getattr(f, "metadata", {}) or {}
        tbl.add_row([
            f.id,
            meta.get("from", ""),
            meta.get("subject", ""),
            meta.get("date", ""),
        ])

    click.echo(tbl)

@cli.command()
@click.option("--unread", is_flag=True, help="Summarize only unread emails")
@click.option(
    "--limit",
    default=5,
    show_default=True,
    help="Limit the number of emails to summarize",
)
def summarize(unread, limit):
    """Summarize emails using GPT."""
    try:
        click.echo("Fetching emails...")
        emails = fetch_emails(unread=unread, limit=limit)

        if not emails:
            click.echo("No emails found to summarize.")
            return

        click.echo("Generating summary...")
        summary = summarize_with_gpt(emails)

        click.echo("\nEmail Summary:")
        click.echo("-------------")
        click.echo(summary)

    except ValueError as e:
        click.echo(click.style(f"Config Error: {e}", fg="red"))
    except Exception as e:
        click.echo(click.style(f"An error occurred: {e}", fg="red"))


if __name__ == "__main__":
    cli()
