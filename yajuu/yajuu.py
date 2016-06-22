import click

from .cli import download


@click.group()
def main():
    pass


main.add_command(download)
