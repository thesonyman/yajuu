from setuptools import setup, find_packages
from pip.req import parse_requirements
import platform


__version__ = '0.3.0'

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

if platform.system() == 'Windows':
    excluded_packages = ['inquirer', 'readchar']
    reqs = [x for x in reqs if x.split('==')[0] not in excluded_packages]

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
