import click
import logging

from yajuu.media.types import MEDIA_TYPES


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


@click.group()
@click.pass_context
@click.option('-mt', '--media-type', required=True)
@click.option('-m', '--media', required=True)
def run(ctx, media_type, media):
    logger = logging.getLogger('yajuu')
    logger.setLevel(logging.DEBUG)

    ctx.obj['MEDIA'] = MEDIA_TYPES[media_type.lower()][0](media)
    ctx.obj['MEDIA_TYPE'] = media_type


@click.command()
@click.pass_context
@click.option('-f', '--file-name', required=True)
@click.option('-c', '--class-name', required=True)
@click.option('-i', '--search-index', type=click.INT)
def extractor(ctx, file_name, class_name, search_index):
    from yajuu.cli.dev.run import run_extractor as _run_extractor
    _run_extractor(
        ctx.obj['MEDIA'], ctx.obj['MEDIA_TYPE'], file_name, class_name,
        search_index
    )

run.add_command(extractor)


dev.add_command(shell)
dev.add_command(generate)
dev.add_command(run)
