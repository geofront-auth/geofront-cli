import os.path
import sys

try:
    from setuptools import find_packages, setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import find_packages, setup

from geofrontcli.version import VERSION


def readme():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
            return f.read()
    except (IOError, OSError):
        return ''


install_requires = [
    'six',
    'enum34',
    'keyring >= 3.7',
    'dirspec >= 13.08'
    # require --allow-external dirspec --allow-unverified dirspec
]

if sys.version_info < (2, 7):
    install_requires.append('argparse')


setup(
    name='geofront-cli',
    version=VERSION,
    description='CLI client for Geofront, a simple SSH key management server',
    long_description=readme(),
    url='https://github.com/spoqa/geofront-cli',
    author='Hong Minhee',
    author_email='minhee' '@' 'dahlia.kr',
    maintainer='Spoqa',
    maintainer_email='dev' '@' 'spoqa.com',
    license='GPLv3 or later',
    packages=find_packages(exclude=['tests']),
    entry_points='''
        [console_scripts]
        geofront-cli = geofrontcli.cli:main
    ''',
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved '
        ':: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: Utilities'
    ]
)
