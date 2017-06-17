""":mod:`geofrontcli.proxy` --- Local SSH proxy over HTTPS/WebSocket
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import asyncio
import contextlib
import csv
import logging
import pathlib
import socket
import sys
import traceback

from aiohttp import ClientError, ClientSession, WSMsgType
from aiotools import actxmgr, start_server
from dirspec.basedir import load_config_paths, save_config_path

from .version import VERSION

__all__ = ('start_ssh_proxy', )


CONFIG_RESOURCE = 'geofront-cli'
PROXY_PORT_MAP_FILENAME = 'proxyports.csv'

logger = logging.getLogger(__name__)


def get_unused_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with contextlib.closing(s):
        s.bind(('localhost', 0))
        return s.getsockname()[1]


def load_proxy_port_map():
    data = dict()
    for path in load_config_paths(CONFIG_RESOURCE):
        path = pathlib.Path(path.decode()) / PROXY_PORT_MAP_FILENAME
        if path.is_file():
            with open(path) as f:
                for row in csv.reader(f):
                    data[row[0]] = int(row[1])
    return data


def save_proxy_port_map(data):
    config_path = (pathlib.Path(save_config_path(CONFIG_RESOURCE).decode())
                   / PROXY_PORT_MAP_FILENAME)
    with open(config_path, 'w') as f:
        writer = csv.writer(f)
        for key, val in data.items():
            writer.writerow((key, val))
    logger.info(f'To modify port-host mapping, check out {config_path}.',
                extra={'user_waiting': False})


def get_port_for_remote(host):
    data = load_proxy_port_map()
    if host in data:
        return data[host]
    else:
        port = get_unused_port()
        data[host] = port
        logger.info(f'Mapped port {port} with host {host}.',
                    extra={'user_waiting': False})
        save_proxy_port_map(data)
        return port


async def pipe(url, remote, ssh_executable):
    """The main task that proxies the incoming SSH traffic via WebSockets."""
    loop = asyncio.get_event_loop()
    headers = {
        'User-Agent': 'geofront-cli/{0} (Python-asyncio/{1})'.format(
            VERSION, sys.version[:3]
        ),
    }

    async def handle_ssh_sock(ws, ssh_sock):
        """A sub-task that proxies the outgoing SSH traffic via WebSocket."""
        while True:
            try:
                data = await loop.sock_recv(ssh_sock, 4096)
            except asyncio.CancelledError:
                break
            if not data:
                break
            ws.send_bytes(data)

    async def handle_subproc(cmd, pipe_task):
        """Launch the local SSH agent and wait until it terminates."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=None, stdout=None, stderr=None,  # inherit
                close_fds=True,
            )
            await proc.wait()
            pipe_task.cancel()  # signal to terminate
        except:
            logger.error('Unexpected error!', extra={'user_waiting': False})
            traceback.print_exc()

    local_sock = None
    ssh_sock = None
    ssh_reader_task = None
    subproc_task = None

    logger.info(f"Making a local SSH proxy to {remote['host']}...",
                extra={'user_waiting': True})

    # TODO: response header version check?
    session = ClientSession()
    try:
        sock_type = socket.SOCK_STREAM
        if hasattr(socket, 'SOCK_NONBLOCK'):  # only for Linux
            sock_type |= socket.SOCK_NONBLOCK
        local_sock = socket.socket(socket.AF_INET, sock_type)
        local_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_port = get_port_for_remote(f"{remote['host']}:{remote['port']}")
        try:
            local_sock.bind(('localhost', bind_port))
        except OSError:
            logger.error(f'Cannot bind to port {bind_port}!',
                         extra={'user_waiting': False})
            return
        local_sock.listen(1)
        logger.info(f'Connecting to local SSH proxy at port {bind_port}...',
                    extra={'user_waiting': False})
        async with session.ws_connect(url, headers=headers) as ws:
            cmd = [
                ssh_executable,
                '-l', remote['user'],
                '-p', str(bind_port),
                'localhost',
            ]
            subproc_task = loop.create_task(
                handle_subproc(cmd, asyncio.Task.current_task()))
            await asyncio.sleep(0)  # required!
            ssh_sock, _ = await loop.sock_accept(local_sock)
            ssh_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            local_sock.close()  # used only once
            ssh_reader_task = loop.create_task(handle_ssh_sock(ws, ssh_sock))
            async for msg in ws:
                if msg.type == WSMsgType.BINARY:
                    await loop.sock_sendall(ssh_sock, msg.data)
                elif msg.type == WSMsgType.CLOSED:
                    break
                elif msg.type == WSMsgType.ERROR:
                    logger.error('Server disconnected unexpectedly.',
                                 extra={'user_waiting': False})
                    break
    except ClientError:
        logger.error('Connection error!', extra={'user_waiting': False})
        raise
    except asyncio.CancelledError:
        pass
    except:
        logger.error('Unexpected error!', extra={'user_waiting': False})
        traceback.print_exc()
    finally:
        if subproc_task and not subproc_task.done():
            subproc_task.cancel()
            await subproc_task
        if ssh_reader_task and not ssh_reader_task.done():
            ssh_reader_task.cancel()
            await ssh_reader_task
        if ssh_sock:
            ssh_sock.close()
        session.close()
        loop.stop()


@actxmgr
async def serve_proxy(loop, pidx, args):
    """The initialize and shtudown routines for the local SSH proxy."""
    pipe_task = None
    try:
        pipe_task = loop.create_task(pipe(*args))
        yield
    finally:
        if pipe_task and not pipe_task.done():
            pipe_task.cancel()
            await pipe_task


def start_ssh_proxy(url, remote, ssh_executable):
    start_server(serve_proxy,
                 args=(url, remote, ssh_executable),
                 num_proc=1)
