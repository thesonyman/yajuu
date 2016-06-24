from setuptools import setup, find_packages
from pip.req import parse_requirements


__version__ = '0.2.0'

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

with open('README.md', 'rb') as f:
    long_descr = f.read().decode('utf-8')

setup(
    name='yajuu',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['yajuu=yajuu.yajuu:main']
    },
    version=__version__,
    description='An automated media downloader.',
    long_description=long_descr,
    author='Vivescere Discere',
    install_requires=reqs
)
