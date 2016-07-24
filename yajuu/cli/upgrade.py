import click


@click.command()
@click.option('--branch', default='master')
def upgrade(branch):
    import pip

    pip.main([
        'install', '--upgrade',
        'git+https://github.com/vivescere/yajuu@{}'.format(branch)
    ])
