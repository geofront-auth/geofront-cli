from geofrontcli.client import parse_mimetype


def test_parse_mimetype():
    assert parse_mimetype('text/plain') == ('text/plain', [])
    assert parse_mimetype('text/html; charset=utf-8') == \
           ('text/html', ['charset=utf-8'])
