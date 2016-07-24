import click


@click.group()
def dev():
    pass


@click.command()
def shell(*args, **kwargs):
    from yajuu.cli.dev.shell import shell as _shell
    _shell(*args, **kwargs)


@click.command()
@click.option('-t', '--type', type=click.Choice([
    'extractor', 'unshortener'
]), required=True)
def generate(*args, **kwargs):
    from yajuu.cli.dev.generate import generate as _generate
    _generate(*args, **kwargs)


dev.add_command(shell)
dev.add_command(generate)
