"""Command-line interface for the email agent."""

import click
from prettytable import PrettyTable
from email_agent.core.email_handler import EmailHandler
from email_agent.storage.vector_store import VectorStore
from email_agent.rag.query_engine import QueryEngine
from email_agent.utils.config import get_env_var, get_db_connection_string


def display_emails(emails):
    """Display emails in a formatted table."""
    if not emails:
        click.echo("No emails found.")
        return

    table = PrettyTable()
    table.field_names = ["Date", "From", "Subject", "Size", "Human"]
    table.align["Date"] = "l"
    table.align["Subject"] = "l"
    table.align["From"] = "l"
    table.align["Size"] = "r"
    table.align["Human"] = "c"

    for email in emails:
        date = email.date.strftime("%Y-%m-%d %H:%M")
        size = f"{email.size / 1024:.1f} KB"
        subject = (
            email.subject[:50] + "..." if len(email.subject) > 50 else email.subject
        )
        human = "✓" if email.is_human else "✗"

        table.add_row([date, email.from_, subject, size, human])

    click.echo(table)


@click.group()
def cli():
    """Email CLI tool for intelligent email management."""
    pass


@cli.command(name="list")
@click.option("--unread", is_flag=True, help="List only unread emails")
@click.option("--human-only", is_flag=True, help="List only emails from humans")
@click.option(
    "--limit", default=10, show_default=True, help="Limit the number of emails to list"
)
def list_emails(unread, human_only, limit):
    """List emails from the inbox with various filtering options."""
    try:
        handler = EmailHandler(
            host=get_env_var("IMAP_HOST"),
            user=get_env_var("IMAP_USER"),
            password=get_env_var("IMAP_PASSWORD"),
        )

        emails = handler.fetch_emails(unread=unread, limit=limit)
        if human_only:
            emails = [e for e in emails if e.is_human]

        display_emails(emails)
    except ValueError as e:
        click.echo(click.style(f"Config Error: {e}", fg="red"))
    except Exception as e:
        click.echo(click.style(f"An error occurred: {e}", fg="red"))


@cli.command(name="ingest")
@click.option(
    "--limit", default=100, show_default=True, help="Number of emails to ingest"
)
def ingest_emails(limit):
    """Ingest emails into the vector database for future querying."""
    try:
        # Initialize components
        handler = EmailHandler(
            host=get_env_var("IMAP_HOST"),
            user=get_env_var("IMAP_USER"),
            password=get_env_var("IMAP_PASSWORD"),
        )
        vector_store = VectorStore(get_db_connection_string())

        # Fetch and store emails
        emails = handler.fetch_emails(limit=limit)
        stored_count = 0

        for email in emails:
            if vector_store.store_email(email):
                stored_count += 1

        click.echo(f"Successfully ingested {stored_count} emails")
    except Exception as e:
        click.echo(click.style(f"An error occurred during ingestion: {e}", fg="red"))


@cli.command(name="query")
@click.argument("query_text")
@click.option(
    "--limit", default=5, show_default=True, help="Number of results to return"
)
def query_emails(query_text, limit):
    """Query emails using natural language."""
    try:
        vector_store = VectorStore(get_db_connection_string())
        query_engine = QueryEngine(vector_store)

        response = query_engine.query(query_text)
        click.echo(response)
    except Exception as e:
        click.echo(click.style(f"An error occurred during query: {e}", fg="red"))


if __name__ == "__main__":
    cli()
