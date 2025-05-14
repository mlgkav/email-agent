"""Email CLI tool for querying emails using RAG."""

import click
import os
from imap_tools import MailBox
from dotenv import load_dotenv
from prettytable import PrettyTable
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()


def get_env_var(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def fetch_emails(unread=False, limit=10, include_body=False):
    host = get_env_var("IMAP_HOST")
    user = get_env_var("IMAP_USER")
    password = get_env_var("IMAP_PASSWORD")

    criteria = "UNSEEN" if unread else "ALL"

    with MailBox(host).login(user, password) as mailbox:
        emails = list(mailbox.fetch(criteria, limit=limit, reverse=True))
        if include_body:
            return [(email, email.text or email.html) for email in emails]
        return emails


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


def summarize_with_gpt(emails_with_content):
    """Summarize emails using GPT."""
    try:
        client = OpenAI(api_key=get_env_var("OPENAI_API_KEY"))

        # Prepare email content for summarization
        email_texts = []
        for email, content in emails_with_content:
            email_texts.append(
                f"Date: {email.date}\n"
                f"From: {email.from_}\n"
                f"Subject: {email.subject}\n"
                f"Content: {content[:1000]}..."  # Truncate content to avoid token limits
            )

        combined_emails = "\n\n---\n\n".join(email_texts)

        response = client.chat.completions.create(
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
    "--limit", default=10, show_default=True, help="Limit the number of emails to list"
)
def list_emails(unread, limit):
    """List emails from the inbox with options for unread and limit."""
    try:
        emails = fetch_emails(unread=unread, limit=limit)
        display_emails(emails)
    except ValueError as e:
        click.echo(click.style(f"Config Error: {e}", fg="red"))
    except Exception as e:
        click.echo(click.style(f"An error occurred: {e}", fg="red"))


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
        emails_with_content = fetch_emails(
            unread=unread, limit=limit, include_body=True
        )

        if not emails_with_content:
            click.echo("No emails found to summarize.")
            return

        click.echo("Generating summary...")
        summary = summarize_with_gpt(emails_with_content)

        click.echo("\nEmail Summary:")
        click.echo("-------------")
        click.echo(summary)

    except ValueError as e:
        click.echo(click.style(f"Config Error: {e}", fg="red"))
    except Exception as e:
        click.echo(click.style(f"An error occurred: {e}", fg="red"))


if __name__ == "__main__":
    cli()
