import click


@click.group()
def dev():
    pass


@click.command()
def shell(*args, **kwargs):
    from yajuu.cli.dev.shell import shell as _shell
    _shell(*args, **kwargs)


dev.add_command(shell)
