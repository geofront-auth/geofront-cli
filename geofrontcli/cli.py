""":mod:`geofrontcli.cli` --- CLI main
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from __future__ import print_function

import argparse
import os.path
import sys
import webbrowser

from dirspec.basedir import load_config_paths, save_config_path
from six.moves import input

from .client import (Client, ExpiredTokenIdError, NoTokenIdError,
                     RemoteError)
from .key import PublicKey


CONFIG_RESOURCE = 'geofront-cli'
SERVER_CONFIG_FILENAME = 'server'

parser = argparse.ArgumentParser(description='Geofront client utility')
parser.add_argument('-d', '--debug', action='store_true', help='debug mode')
subparsers = parser.add_subparsers()


def get_server_url():
    for path in load_config_paths(CONFIG_RESOURCE):
        path = os.path.join(path.decode(), SERVER_CONFIG_FILENAME)
        if os.path.isfile(path):
            with open(path) as f:
                return f.read().strip()
    parser.exit('Geofront server URL is not configured yet.\n'
                'Try `{0} start` command.'.format(parser.prog))


def get_client():
    server_url = get_server_url()
    return Client(server_url)


def subparser(function):
    """Register a subparser function."""
    p = subparsers.add_parser(function.__name__, description=function.__doc__)
    p.set_defaults(function=function)
    p.call = function
    return p


@subparser
def start(args):
    """Set up the Geofront server URL."""
    for path in load_config_paths(CONFIG_RESOURCE):
        path = os.path.join(path.decode(), SERVER_CONFIG_FILENAME)
        if os.path.isfile(path):
            message = 'Geofront server URL is already configured: ' + path
            if args.force:
                print(message + '; overwriting...', file=sys.stderr)
            else:
                parser.exit(message)
    server_url = input('Geofront server URL: ')
    server_config_filename = os.path.join(
        save_config_path(CONFIG_RESOURCE).decode(),
        SERVER_CONFIG_FILENAME
    )
    with open(server_config_filename, 'w') as f:
        print(server_url, file=f)
    authenticate.call(args)


start.add_argument('-f', '--force',
                   action='store_true',
                   help='overwrite the server url configuration')


@subparser
def authenticate(args):
    """Authenticate to Geofront server."""
    client = get_client()
    with client.authenticate() as url:
        if args.open_browser:
            print('Continue to authenticate in your web browser...')
            webbrowser.open(url)
        else:
            print('Continue to authenticate in your web browser:')
            print(url)
        input('Press return to continue')
    home = os.path.expanduser('~')
    ssh_dir = os.path.join(home, '.ssh')
    if os.path.isdir(ssh_dir):
        for name in 'id_rsa.pub', 'id_dsa.pub':
            pubkey_path = os.path.join(ssh_dir, name)
            if os.path.isfile(pubkey_path):
                with open(pubkey_path) as f:
                    public_key = PublicKey.parse_line(f.read())
                    break
        else:
            public_key = None
        if public_key and public_key.fingerprint not in client.public_keys:
            print('You have a public key ({0}), and it is not registered '
                  'to the Geofront server ({1}).'.format(pubkey_path,
                                                         client.server_url))
            while True:
                register = input('Would you register the public key to '
                                 'the Geofront server (Y/n)? ').strip()
                if register.lower() in ('', 'y', 'n'):
                    break
                print('{0!r} is an invalid answer.'.format(register))
            if register.lower() != 'n':
                try:
                    client.public_keys[public_key.fingerprint] = public_key
                except ValueError as e:
                    print(e, file=sys.stderr)
                    if args.debug:
                        raise


for p in authenticate, start:
    p.add_argument(
        '-O', '--no-open-browser',
        dest='open_browser',
        action='store_false',
        help='do not open the authentication web page using browser.  '
             'instead print the url to open'
    )


@subparser
def keys(args):
    """List registered public keys."""
    client = get_client()
    for fingerprint, key in client.public_keys.items():
        if args.fingerprint:
            print(fingerprint)
        else:
            print(key)


keys.add_argument(
    '-v', '--verbose',
    dest='fingerprint',
    action='store_false',
    help='print public keys with OpenSSH authorized_keys format instead of '
         'fingerprints'
)


@subparser
def masterkey(args):
    """Show the current master key."""
    client = get_client()
    master_key = client.master_key
    if args.fingerprint:
        print(master_key.fingerprint)
    else:
        print(master_key)


masterkey.add_argument(
    '-v', '--verbose',
    dest='fingerprint',
    action='store_false',
    help='print the master key with OpenSSH authorized_keys format instead of '
         'its fingerprint'
)


@subparser
def remotes(args):
    """List available remotes."""
    client = get_client()
    remotes = client.remotes
    if args.alias:
        for alias in remotes:
            print(alias)
    else:
        for alias, remote in remotes.items():
            print('{0}\t{1}'.format(alias, remote))


remotes.add_argument(
    '-v', '--verbose',
    dest='alias',
    action='store_false',
    help='print remote aliases with their actual addresses, not only aliases'
)


@subparser
def authorize(args):
    """Temporarily authorize you to access the given remote.
    A made authorization keeps alive in a minute, and then will be expired.

    """
    client = get_client()
    try:
        client.authorize(args.remote)
    except RemoteError as e:
        print(e, file=sys.stderr)
        if args.debug:
            raise


authorize.add_argument(
    'remote',
    help='the remote alias to authorize you to access'
)


def main(args=None):
    args = parser.parse_args(args)
    if getattr(args, 'function', None):
        try:
            args.function(args)
        except NoTokenIdError:
            parser.exit('Not authenticated yet.\n'
                        'Try `{0} authenticate` command.'.format(parser.prog))
        except ExpiredTokenIdError:
            parser.exit('Authentication renewal required.\n'
                        'Try `{0} authenticate` command.')
