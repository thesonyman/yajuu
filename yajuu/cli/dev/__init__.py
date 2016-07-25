import click
import logging


@click.group()
def dev():
    pass


@click.group()
def generate():
    pass


@click.command()
def generate_extractor():
    from yajuu.cli.dev.generate import generate_extractor as gen
    gen()


@click.command()
def generate_unshortener():
    from yajuu.cli.dev.generate import generate_unshortener as gen
    gen()


generate.add_command(generate_extractor, name='extractor')
generate.add_command(generate_unshortener, name='unshortener')


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
def run_extractor(media_type, media, file_name, class_name, search_index):
    from yajuu.cli.dev.run import run_extractor
    from yajuu.media.types import MEDIA_TYPES

    media = MEDIA_TYPES[media_type.lower()][0](media)

    run_extractor(media, media_type, file_name, class_name, search_index)


@click.command()
@click.option('-u', '--url', required=True)
@click.option('-q', '--quality', type=click.INT)
def run_unshortener(url, quality):
    from yajuu.cli.dev.run import run_unshortener
    run_unshortener(url, quality)


run.add_command(run_extractor, name='extractor')
run.add_command(run_unshortener, name='unshortener')


dev.add_command(generate)
dev.add_command(run)
