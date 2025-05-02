import click

@click.group()
def cli():
    """A basic CLI application."""
    pass

@cli.command()
def hello():
    """Print a greeting."""
    click.echo("Hello, World!")

if __name__ == '__main__':
    cli() 