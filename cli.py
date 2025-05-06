"""Email CLI tool for querying emails using RAG."""

import click
import os
from imap_tools import MailBox
from dotenv import load_dotenv
from prettytable import PrettyTable

# Load environment variables from .env file
load_dotenv()


def get_env_var(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def fetch_emails(unread=False, limit=10):
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


if __name__ == "__main__":
    cli()
