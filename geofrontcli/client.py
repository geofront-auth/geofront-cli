""":mod:`geofrontcli.client` --- Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import collections
import contextlib
import io
import json
import logging
import re
import sys
import uuid

from keyring import get_password, set_password
from six import string_types
from six.moves.urllib.error import HTTPError
from six.moves.urllib.parse import urljoin
from six.moves.urllib.request import Request, urlopen

from .key import PublicKey
from .version import MIN_PROTOCOL_VERSION, MAX_PROTOCOL_VERSION, VERSION

__all__ = ('REMOTE_PATTERN', 'BufferedResponse',
           'Client', 'ExpiredTokenIdError',
           'MasterKeyError', 'NoTokenIdError', 'ProtocolVersionError',
           'RemoteAliasError', 'RemoteError', 'RemoteStateError',
           'TokenIdError', 'UnfinishedAuthenticationError',
           'parse_mimetype')


#: (:class:`re.RegexObject`) The pattern that matches to the remote string
#: look like ``'user@host:port'``.
REMOTE_PATTERN = re.compile(r'^(?:(?P<user>[^@]+)@)?'
                            r'(?P<host>[^:]+)'
                            r'(?::(?P<port>\d+))?$')


def parse_mimetype(content_type):
    """Parse :mailheader:`Content-Type` header and return the actual mimetype
    and its options.

    >>> parse_mimetype('text/html; charset=utf-8')
    ('text/html', ['charset=utf-8'])

    """
    values = [v.strip() for v in content_type.split(';')]
    return values[0], values[1:]


class Client(object):
    """Client for a configured Geofront server."""

    #: (:class:`PublicKeyDict`) Public keys registered to Geofront server.
    public_keys = None

    def __init__(self, server_url):
        self.logger = logging.getLogger(__name__ + '.Client')
        self.server_url = server_url
        self.public_keys = PublicKeyDict(self)

    @contextlib.contextmanager
    def request(self, method, url, data=None, headers={}):
        logger = self.logger.getChild('request')
        if isinstance(url, tuple):
            url = './{0}/'.format('/'.join(url))
        url = urljoin(self.server_url, url)
        h = {
            'User-Agent': 'geofront-cli/{0} (Python-urllib/{1})'.format(
                VERSION, sys.version[:3]
            ),
            'Accept': 'application/json'
        }
        h.update(headers)
        request = Request(url, method=method, data=data, headers=h)
        try:
            response = urlopen(request)
        except HTTPError as e:
            logger.exception(e)
            response = e
        server_version = response.headers.get('X-Geofront-Version')
        if server_version:
            try:
                server_version_info = tuple(
                    map(int, server_version.strip().split('.'))
                )
            except ValueError:
                raise ProtocolVersionError(
                    None,
                    'the protocol version number the server sent is not '
                    'a valid format: ' + repr(server_version)
                )
            else:
                if not (MIN_PROTOCOL_VERSION <=
                        server_version_info <=
                        MAX_PROTOCOL_VERSION):
                    raise ProtocolVersionError(
                        server_version_info,
                        'the server protocol version ({0}) is '
                        'incompatible'.format(server_version)
                    )
        else:
            raise ProtocolVersionError(
                None,
                'the server did not send the protocol version '
                '(X-Geofront-Version)'
            )
        mimetype, _ = parse_mimetype(response.headers['Content-Type'])
        if mimetype == 'application/json' and 400 <= response.code < 500:
            read = response.read()
            body = json.loads(read.decode('utf-8'))
            response.close()
            error = isinstance(body, dict) and body.get('error')
            if response.code == 404 and error == 'token-not-found' or \
               response.code == 410 and error == 'expired-token':
                raise ExpiredTokenIdError('token id seems expired')
            elif response.code == 412 and error == 'unfinished-authentication':
                raise UnfinishedAuthenticationError(body['message'])
            buffered = BufferedResponse(response.code, response.headers, read)
            yield buffered
            buffered.close()
            return
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
    def identity(self):
        """(:class:`tuple`) A pair of ``(team_type, identifier)``."""
        with self.request('GET', ('tokens', self.token_id)) as r:
            assert r.code == 200
            mimetype, _ = parse_mimetype(r.headers['Content-Type'])
            assert mimetype == 'application/json'
            result = json.loads(r.read().decode('utf-8'))
            return result['team_type'], result['identifier']

    @property
    def master_key(self):
        """(:class:`~.key.PublicKey`) The current master key."""
        path = ('tokens', self.token_id, 'masterkey')
        headers = {'Accept': 'text/plain'}
        with self.request('GET', path, headers=headers) as r:
            if r.code == 200:
                mimetype, _ = parse_mimetype(r.headers['Content-Type'])
                if mimetype == 'text/plain':
                    return PublicKey.parse_line(r.read())
        raise MasterKeyError('server failed to show the master key')

    @property
    def remotes(self):
        """(:class:`collections.Mapping`) The map of aliases to remote
        addresses.

        """
        path = ('tokens', self.token_id, 'remotes')
        with self.request('GET', path) as r:
            assert r.code == 200
            mimetype, _ = parse_mimetype(r.headers['Content-Type'])
            assert mimetype == 'application/json'
            result = json.loads(r.read().decode('utf-8'))
        fmt = '{0[user]}@{0[host]}:{0[port]}'.format
        return dict((alias, fmt(remote)) for alias, remote in result.items())

    def authorize(self, alias):
        """Temporarily authorize you to access the given remote ``alias``.
        A made authorization keeps alive in a minute, and then will be expired.

        """
        path = ('tokens', self.token_id, 'remotes', alias)
        with self.request('POST', path) as r:
            mimetype, _ = parse_mimetype(r.headers['Content-Type'])
            assert mimetype == 'application/json'
            result = json.loads(r.read().decode('utf-8'))
            if r.code == 404 and result.get('error') == 'not-found':
                raise RemoteAliasError(result.get('message'))
            elif r.code == 500 and result.get('error') == 'connection-failure':
                raise RemoteStateError(result.get('message'))
            assert r.code == 200
            assert result['success'] == 'authorized'
            return '{0[user]}@{0[host]}:{0[port]}'.format(result['remote'])

    def __repr__(self):
        return '{0.__module__}.{0.__name__}({1!r})'.format(
            type(self), self.server_url
        )


class BufferedResponse(io.BytesIO):
    """:class:`io.BytesIO` subclass that mimics some interface of
    :class:`http.client.HTTPResponse`.

    """

    def __init__(self, code, headers, *args, **kwargs):
        super(BufferedResponse, self).__init__(*args, **kwargs)
        self.code = code
        self.headers = headers


class PublicKeyDict(collections.MutableMapping):
    """:class:`dict`-like object that contains public keys."""

    def __init__(self, client):
        self.client = client

    def _request(self, path=(), method='GET', data=None, headers={}):
        path = ('tokens', self.client.token_id, 'keys') + path
        with self.client.request(method, path, data, headers) as resp:
            mimetype, _ = parse_mimetype(resp.headers['Content-Type'])
            body = resp.read()
            if mimetype == 'application/json':
                body = json.loads(body.decode('utf-8'))
                error = isinstance(body, dict) and body.get('error')
            else:
                error = None
            return resp.code, body, error

    def __len__(self):
        code, body, error = self._request()
        assert code == 200
        return len(body)

    def __iter__(self):
        code, body, error = self._request()
        assert code == 200
        return iter(body)

    def __getitem__(self, fprint):
        if isinstance(fprint, string_types):
            code, body, error = self._request((fprint,))
            if not (code == 404 and error == 'not-found'):
                return PublicKey.parse_line(body)
        raise KeyError(fprint)

    def __setitem__(self, fprint, pkey):
        if not isinstance(pkey, PublicKey):
            raise TypeError('expected {0.__module__}.{0.__name__}, not '
                            '{1!r}'.format(PublicKey, pkey))
        if fprint != pkey.fingerprint:
            raise ValueError(
                '{0} is not a valid fingerprint of {1!r}'.format(fprint, pkey)
            )
        code, body, error = self._request(
            method='POST',
            data=bytes(pkey),
            headers={'Content-Type': 'text/plain'}
        )
        if code == 400 and error == 'duplicate-key':
            if fprint in self:
                return
            raise ValueError(fprint + ' is already used by other')
        assert code == 201, 'error: ' + error

    def __delitem__(self, fprint):
        if isinstance(fprint, string_types):
            code, body, error = self._request((fprint,), method='DELETE')
            if not (code == 404 and error == 'not-found'):
                return
        raise KeyError(fprint)

    def items(self):
        code, body, error = self._request()
        assert code == 200
        return [(fprint, PublicKey.parse_line(pkey))
                for fprint, pkey in body.items()]

    def values(self):
        code, body, error = self._request()
        assert code == 200
        return map(PublicKey.parse_line, body.values())


class ProtocolVersionError(Exception):
    """Exception that rises when the server version is not compatibile."""

    #: (:class:`tuple`) The protocol version triple the server sent.
    #: Might be :const:`None`.
    server_version_info = None

    def __init__(self, server_version_info, *args, **kwargs):
        super(ProtocolVersionError, self).__init__(*args, **kwargs)
        self.server_version_info = server_version_info

    @property
    def server_version(self):
        """(:class:`str`) The server version in string."""
        v = self.server_version_info
        return v and '{0}.{1}.{2}'.format(*v)


class TokenIdError(Exception):
    """Exception related to token id."""


class NoTokenIdError(TokenIdError, AttributeError):
    """Exception that rises when there's no configured token id."""


class ExpiredTokenIdError(TokenIdError):
    """Exception that rises when the used token id is expired."""


class UnfinishedAuthenticationError(TokenIdError):
    """Exception that rises when the used token id is not finished
    authentication.

    """


class MasterKeyError(Exception):
    """Exception related to the master key."""


class RemoteError(Exception):
    """Exception related to remote."""


class RemoteAliasError(RemoteError, LookupError):
    """Exception that rises when the given remote alias doesn't exist."""


class RemoteStateError(RemoteError):
    """Exception that rises when the status of the remote is unavailable."""


if sys.version_info < (3, 3):
    class Request(Request):

        superclass = Request

        def __init__(self, url, data=None, headers={}, method=None):
            if isinstance(Request, type):
                super(Request, self).__init__(url, data, headers)
            else:
                self.superclass.__init__(self, url, data, headers)
            if method is not None:
                self.method = method

        def get_method(self):
            if hasattr(self, 'method'):
                return self.method
            return 'GET' if self.data is None else 'POST'
