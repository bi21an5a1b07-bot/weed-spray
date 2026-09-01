"""Accept harness: last-run markdown table order and rtsp_open false on a closed port."""

import socket
import threading

from weed_spray.harness import accept as accept_mod


def test_write_last_run_orders_steps(tmp_path):
    out = tmp_path / "last-run.md"
    accept_mod.write_last_run(
        out,
        {
            "1 connect": ("pass", "ok"),
            "10 pump-off on kill": ("pass", "off"),
        },
    )
    text = out.read_text()
    assert "| 1 connect | pass | ok |" in text
    assert "| 2 typed geofence box | blocked | not reached |" in text
    assert text.index("1 connect") < text.index("10 pump-off")


def test_rtsp_open_true_and_false():
    accept_mod.RTSP_HOST, accept_mod.RTSP_PORT = "127.0.0.1", 1
    try:
        assert accept_mod.rtsp_open() is False
    finally:
        accept_mod.RTSP_HOST, accept_mod.RTSP_PORT = "127.0.0.1", 8554

    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.listen(1)

    def serve():
        conn, _ = server.accept()
        conn.recv(256)
        conn.sendall(b"RTSP/1.0 200 OK\r\nCSeq: 1\r\n\r\n")
        conn.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    accept_mod.RTSP_HOST, accept_mod.RTSP_PORT = "127.0.0.1", port
    try:
        assert accept_mod.rtsp_open() is True
    finally:
        server.close()
        accept_mod.RTSP_HOST, accept_mod.RTSP_PORT = "127.0.0.1", 8554
