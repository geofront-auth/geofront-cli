import sys

from pytest import mark

from geofrontcli.cli import fix_mac_codesign


@mark.skipif(sys.platform != 'darwin', reason='Useful only for macOS')
def test_fix_mac_codesign():
    try:
        fix_mac_codesign()
    except SystemExit:
        pass
