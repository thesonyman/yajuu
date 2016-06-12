from setuptools import setup, find_packages


__version__ = '0.2.0'

with open('README.rst', 'rb') as f:
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
    author='Vivescere Discere'
)
