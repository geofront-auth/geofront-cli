""":mod:`geofrontcli.client` --- Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import contextlib
import json
import sys
import uuid

from keyring import get_password, set_password
from six.moves.urllib.error import HTTPError
from six.moves.urllib.parse import urljoin
from six.moves.urllib.request import Request, urlopen

from .key import PublicKey
from .version import MIN_PROTOCOL_VERSION, MAX_PROTOCOL_VERSION, VERSION

__all__ = ('Client', 'ExpiredTokenIdError', 'NoTokenIdError',
           'ProtocolVersionError', 'TokenIdError')


class Client(object):
    """Client for a configured Geofront server."""

    def __init__(self, server_url):
        self.server_url = server_url

    @contextlib.contextmanager
    def request(self, method, url, data=None, headers={}):
        if isinstance(url, tuple):
            url = './{0}/'.format('/'.join(url))
        url = urljoin(self.server_url, url)
        headers = dict(headers)
        headers.update({
            'User-Agent': 'geofront-cli/{0} (Python-urllib/{1})'.format(
                VERSION, sys.version[:3]
            ),
            'Accept': 'application/json'
        })
        request = Request(url, method=method, data=data, headers=headers)
        try:
            response = urlopen(request)
        except HTTPError as e:
            response = e
        server_version = response.headers.get('X-Geofront-Version')
        if server_version:
            try:
                server_version_info = tuple(
                    map(int, server_version.strip().split('.'))
                )
            except ValueError:
                raise ProtocolVersionError(
                    'the protocol version number the server sent is not '
                    'a valid format: ' + repr(server_version)
                )
            else:
                if not (MIN_PROTOCOL_VERSION <=
                        server_version_info <=
                        MAX_PROTOCOL_VERSION):
                    raise ProtocolVersionError(
                        'the server protocol version ({0}) is '
                        'incompatible'.format(server_version)
                    )
        else:
            raise ProtocolVersionError(
                'the server did not send the protocol version '
                '(X-Geofront-Version)'
            )
        yield response
        response.close()

    @property
    def token_id(self):
        """(:class:`str`) The previously authenticated token id stored
        in the system password store (e.g. Keychain of Mac).

        """
        token_id = get_password('geofront-cli', self.server_url)
        if token_id:
            return token_id
        raise NoTokenIdError('no configured token id')

    @token_id.setter
    def token_id(self, token_id):
        set_password('geofront-cli', self.server_url, token_id)

    @contextlib.contextmanager
    def authenticate(self):
        """Authenticate and then store the :attr:`token_id`."""
        token_id = uuid.uuid1().hex
        with self.request('PUT', ('tokens', token_id)) as response:
            assert response.code == 202
            result = json.loads(response.read().decode('utf-8'))
            yield result['next_url']
        self.token_id = token_id

    @property
    def public_keys(self):
        """Public keys registered to Geofront server."""
        with self.request('GET', ('tokens', self.token_id, 'keys')) as resp:
            if resp.code in (404, 410):
                raise ExpiredTokenIdError('token id seems expired')
            keys = json.loads(resp.read().decode('utf-8'))
        for key in keys:
            yield PublicKey.parse_line(key)

    def __repr__(self):
        return '{0.__module__}.{0.__name__}({1!r})'.format(
            type(self), self.server_url
        )


class ProtocolVersionError(Exception):
    """Exception that rises when the server version is not compatibile."""


class TokenIdError(Exception):
    """Exception related to token id."""


class NoTokenIdError(TokenIdError, AttributeError):
    """Exception that rises when there's no configured token id."""


class ExpiredTokenIdError(TokenIdError):
    """Exception that rises when the used token id is expired."""


if sys.version_info < (3, 3):
    class Request(Request):

        def __init__(self, url, data=None, headers={}, method=None):
            super(Request, self).__init__(url, data, headers)
            if method is not None:
                self.method = method

        def get_method(self):
            if hasattr(self, 'method'):
                return self.method
            return 'GET' if self.data is None else 'POST'
