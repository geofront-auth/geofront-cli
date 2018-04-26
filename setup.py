import os.path
import sys
import warnings

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


install_requires = {
    'certifi',
    'iterfzf >= 0.2.0.16.7, < 1.0.0.0.0',
    'keyring >= 3.7',
    'logging-spinner >= 0.2.1',
    'six',
}

below_py34_requires = {
    'enum34',
}

win32_requires = {
    'pypiwin32',
}

if sys.version_info < (3, 4):
    install_requires.update(below_py34_requires)

if sys.platform == 'win32':
    install_requires.update(win32_requires)


setup(
    name='geofront-cli',
    version=VERSION,
    description='CLI client for Geofront, a simple SSH key management server',
    long_description=readme(),
    url='https://github.com/spoqa/geofront-cli',
    author='Hong Minhee',
    author_email='hongminhee' '@' 'member.fsf.org',
    maintainer='Spoqa',
    maintainer_email='dev' '@' 'spoqa.com',
    license='GPLv3 or later',
    packages=find_packages(exclude=['tests']),
    entry_points='''
        [console_scripts]
        geofront-cli = geofrontcli.cli:main
        gfg = geofrontcli.cli:main_go
    ''',
    install_requires=list(install_requires),
    extras_require={
        ":python_version<'3.4'": list(below_py34_requires),
        ":sys_platform=='win32'": list(win32_requires),
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',  # noqa: E501
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: System :: Systems Administration :: Authentication/Directory',  # noqa: E501
        'Topic :: Utilities'
    ]
)


if 'bdist_wheel' in sys.argv and (
        below_py34_requires.issubset(install_requires) or
        win32_requires.issubset(install_requires)):
    warnings.warn('Building wheels on Windows or using below Python 3.4 is '
                  'not recommended since platform-specific dependencies can '
                  'be merged into common dependencies:\n' +
                  '\n'.join('- ' + i for i in install_requires))
