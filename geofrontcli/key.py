""":mod:`geofrontcli.key` --- Public keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import base64
import enum
import hashlib
import re

from six import string_types

__all__ = 'KeyType', 'PublicKey'


class KeyType(enum.Enum):
    """SSH key types."""

    #: (:class:`KeyType`) ECDSA NIST P-256.
    ecdsa_ssh2_nistp256 = 'ecdsa-sha2-nistp256'

    #: (:class:`KeyType`) ECDSA NIST P-384.
    ecdsa_ssh2_nistp384 = 'ecdsa-sha2-nistp384'

    #: (:class:`KeyType`) ECDSA NIST P-521.
    ecdsa_ssh2_nistp521 = 'ecdsa-sha2-nistp521'

    #: (:class:`KeyType`) DSA.
    ssh_dss = 'ssh-dss'

    #: (:class:`KeyType`) RSA.
    ssh_rsa = 'ssh-rsa'

    def __repr__(self):
        return '{0.__module__}.{0.__name__}.{1}'.format(
            type(self),
            self.name
        )


class PublicKey(object):
    """Public key for SSH.

    :param keytype: the keytype
    :type keytype: :class:`KeyType`
    :param key: keyword-only parameter. the raw :class:`bytes` of the key.
                it cannot be used together with ``base64_key`` parameter
    :type key: :class:`bytes`
    :param base64_key: keyword-only parameter. the base64-encoded form
                       of the key. it cannot be used together with ``key``
                       parameter
    :type base64_key: :class:`str`
    :param comment: keyword-only parameter. an optional comment
    :type comment: :class:`str`

    """

    #: (:class:`KeyType`) The keytype.
    keytype = None

    #: (:class:`bytes`) The raw :class:`bytes` of the key.
    key = None

    #: (:class:`str`) Optional comment. Note that this is ignored when
    #: it's compared to other public key (using :token:`==` or :token`!=`),
    #: or hashed (using :func:`hash()` function).
    comment = None

    @classmethod
    def parse_line(cls, line):
        """Parse a line of ``authorized_keys`` list.

        :param line: a line of ``authorized_keys`` list
        :type line: :class:`bytes`, :class:`str`
        :return: the parsed public key
        :rtype: :class:`PublicKey`
        :raise ValueError: when the given ``line`` is invalid

        """
        if isinstance(line, bytes) and not isinstance(line, str):
            line = line.decode()
        if not isinstance(line, string_types):
            raise TypeError('line must be a string, not ' + repr(line))
        tup = line.split()
        if len(tup) == 2:
            keytype, key = tup
            comment = None
        elif len(tup) == 3:
            keytype, key, comment = tup
        else:
            raise ValueError('line should consist of two or three columns')
        return cls(KeyType(keytype), base64_key=key, comment=comment)

    def __init__(self, keytype, key=None, base64_key=None, comment=None):
        if not isinstance(keytype, KeyType):
            raise TypeError('keytype must be an instance of {0.__module__}.'
                            '{0.__name__}, not {1!r}'.format(KeyType, keytype))
        elif not (comment is None or isinstance(comment, string_types)):
            raise TypeError('comment must a string, not ' + repr(comment))
        self.keytype = keytype
        if key and base64_key:
            raise TypeError('key and base64_key arguments cannot be set '
                            'at a time')
        elif key:
            if not isinstance(key, bytes):
                raise TypeError('key must be a bytes, not ' + repr(key))
            self.key = key
        elif base64_key:
            if not isinstance(base64_key, string_types):
                raise TypeError('base64_key must be a string, not ' +
                                repr(base64_key))
            self.base64_key = base64_key
        else:
            raise TypeError('key or base64_key must be filled')
        self.comment = comment if comment and comment.strip() else None

    @property
    def base64_key(self):
        """(:class:`str`) Base64-encoded form of :attr:`key`."""
        return base64.b64encode(self.key).decode()

    @base64_key.setter
    def base64_key(self, base64_key):
        if not isinstance(base64_key, bytes) and isinstance(base64_key, str):
            base64_key = base64_key.encode()
        self.key = base64.b64decode(base64_key)
        assert self.key

    @property
    def fingerprint(self):
        """(:class:`str`) Hexadecimal fingerprint of the :attr:`key`."""
        return re.sub(r'(\w\w)(?!$)', r'\1:',
                      hashlib.md5(self.key).hexdigest())

    def __eq__(self, other):
        return (isinstance(other, type(self)) and
                self.keytype == other.keytype and
                self.key == other.key)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.keytype, self.key))

    def __str__(self):
        return '{0} {1} {2}'.format(
            self.keytype.value,
            self.base64_key,
            self.comment or ''
        )

    def __bytes__(self):
        return str(self).encode()

    def __repr__(self):
        fmt = '{0.__module__}.{0.__name__}({1!r}, key={2!r}, comment={3!r})'
        return fmt.format(type(self), self.keytype, self.key, self.comment)
