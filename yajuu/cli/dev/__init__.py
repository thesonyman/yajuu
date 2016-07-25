import click
import logging


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
def run():
    logger = logging.getLogger('yajuu')
    logger.setLevel(logging.DEBUG)


@click.command()
@click.option('-mt', '--media-type', required=True)
@click.option('-m', '--media', required=True)
@click.option('-f', '--file-name', required=True)
@click.option('-c', '--class-name', required=True)
@click.option('-i', '--search-index', type=click.INT)
def extractor(media_type, media, file_name, class_name, search_index):
    from yajuu.cli.dev.run import run_extractor
    from yajuu.media.types import MEDIA_TYPES

    media = MEDIA_TYPES[media_type.lower()][0](media)

    run_extractor(media, media_type, file_name, class_name, search_index)


@click.command()
@click.option('-u', '--url', required=True)
@click.option('-q', '--quality', type=click.INT)
def unshortener(url, quality):
    from yajuu.cli.dev.run import run_unshortener
    run_unshortener(url, quality)


run.add_command(extractor)
run.add_command(unshortener)


dev.add_command(shell)
dev.add_command(generate)
dev.add_command(run)
