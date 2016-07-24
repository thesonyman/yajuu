import click


@click.group()
def configure():
    pass


@click.command()
@click.option(
    '--only-print', is_flag=True,
    help='Only print the configuration as yaml, does not save it.'
)
def plex(*args, **kwargs):
    from yajuu.cli.configure.plex import plex as _plex
    _plex(*args, **kwargs)


configure.add_command(plex)
