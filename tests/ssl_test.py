import ssl

from geofrontcli.ssl import (create_https_context, create_urllib_https_handler,
                             get_https_context_factory)


def test_get_https_context_factory():
    factory = get_https_context_factory()
    context = factory()
    assert context is None or isinstance(context, ssl.SSLContext)


def test_create_https_context():
    context = create_https_context()
    assert context is None or isinstance(context, ssl.SSLContext)


def test_create_urllib_https_handler():
    create_urllib_https_handler()
