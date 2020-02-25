from __future__ import absolute_import

import re
import ssl

import certifi  # noqa: I902
from six.moves.urllib.request import HTTPSHandler

__all__ = ('create_https_context', 'create_urllib_https_handler',
           'get_https_context_factory')


def get_https_context_factory():
    if not hasattr(ssl, 'Purpose'):
        return lambda *_, **__: None
    if not hasattr(ssl, '_create_default_https_context') or \
       hasattr(ssl, 'get_default_verify_paths') and \
       ssl.get_default_verify_paths()[0] is None:
        m = re.match(r'(Open|Libre)SSL (\d+)\.(\d+)\.(\d+)',
                     ssl.OPENSSL_VERSION)
        openssl_version = int(m.group(2)), int(m.group(3)), int(m.group(4))
        if openssl_version < (1, 0, 2) and hasattr(certifi, 'old_where'):
            # https://github.com/certifi/python-certifi/issues/26
            where = certifi.old_where
        else:
            where = certifi.where

        def get_https_context(purpose=ssl.Purpose.SERVER_AUTH,
                              cafile=None, capath=None, cadata=None):
            return ssl.create_default_context(
                purpose=purpose,
                cafile=cafile or where(),
                capath=capath,
                cadata=cadata
            )
        return get_https_context
    if hasattr(ssl, '_create_default_https_context'):
        return ssl._create_default_https_context
    if hasattr(ssl, 'create_default_context'):
        return ssl.create_default_context
    return lambda *_, **__: None


create_https_context = get_https_context_factory()


def create_urllib_https_handler():
    context = create_https_context()
    try:
        return HTTPSHandler(context=context)
    except TypeError:
        # Older Python versions doesn't have context parameter.
        # (Prior to Python 2.7.9/3.4.3
        return HTTPSHandler()
