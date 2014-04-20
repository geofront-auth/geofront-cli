""":mod:`geofrontcli.cli` --- CLI main
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from __future__ import print_function

import argparse
import os.path
import subprocess
import sys
import webbrowser

from dirspec.basedir import load_config_paths, save_config_path
from six.moves import input

from .client import (REMOTE_PATTERN, Client, ExpiredTokenIdError,
                     NoTokenIdError, RemoteError, TokenIdError)
from .key import PublicKey


CONFIG_RESOURCE = 'geofront-cli'
SERVER_CONFIG_FILENAME = 'server'

SSH_PROGRAM = None
try:
    SSH_PROGRAM = subprocess.check_output(['which', 'ssh']).strip() or None
except subprocess.CalledProcessError:
    pass


parser = argparse.ArgumentParser(description='Geofront client utility')
parser.add_argument(
    '--ssh',
    default=SSH_PROGRAM,
    required=not SSH_PROGRAM,
    help='ssh client to use' + (' [%(default)s]' if SSH_PROGRAM else '')
)
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
        parser.error(str(e))
        if args.debug:
            raise


authorize.add_argument(
    'remote',
    help='the remote alias to authorize you to access'
)


def get_ssh_options(remote):
    """Translate the given ``remote`` to a corresponding :program:`ssh`
    options.  For example, it returns the following list for ``'user@host'``::

        ['-l', 'user', 'host']

    The remote can contain the port number or omit the user login as well
    e.g. ``'host:22'``::

        ['-p', '22', 'host']

    """
    remote_match = REMOTE_PATTERN.match(remote)
    if not remote_match:
        raise ValueError('invalid remote format: ' + str(remote))
    options = []
    user = remote_match.group('user')
    if user:
        options.extend(['-l', user])
    port = remote_match.group('port')
    if port:
        options.extend(['-p', port])
    options.append(remote_match.group('host'))
    return options


@subparser
def colonize(args):
    """Make the given remote to allow the current master key.
    It is equivalent to ``geofront-cli masterkey -v > /tmp/master_id_rsa &&
    ssh-copy-id -i /tmp/master_id_rsa REMOTE``.

    """
    client = get_client()
    remote = client.remotes.get(args.remote, args.remote)
    try:
        options = get_ssh_options(remote)
    except ValueError as e:
        parser.error(str(e))
    cmd = [args.ssh]
    if args.identity_file:
        cmd.extend(['-i', args.identity_file])
    cmd.extend(options)
    cmd.extend([
        'mkdir', '~/.ssh', '&>', '/dev/null', '||', 'true', ';',
        'echo', repr(str(client.master_key)),
        '>>', '~/.ssh/authorized_keys'
    ])
    subprocess.call(cmd)


colonize.add_argument(
    '-i',
    dest='identity_file',
    help='identity file to use.  it will be forwarded to the same option '
         'of the ssh program if used'
)
colonize.add_argument('remote', help='the remote alias to colonize')


@subparser
def ssh(args):
    """SSH to the remote through Geofront's temporary authorization."""
    while True:
        client = get_client()
        try:
            remote = client.authorize(args.remote)
        except RemoteError as e:
            parser.error(str(e))
            if args.debug:
                raise
        except TokenIdError:
            print('Authentication required.')
            authenticate.call(args)
        else:
            break
    try:
        options = get_ssh_options(remote)
    except ValueError as e:
        parser.error(str(e))
    subprocess.call([args.ssh] + options)


ssh.add_argument('remote', help='the remote alias to ssh')


for p in authenticate, start, ssh:
    p.add_argument(
        '-O', '--no-open-browser',
        dest='open_browser',
        action='store_false',
        help='do not open the authentication web page using browser.  '
             'instead print the url to open'
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
