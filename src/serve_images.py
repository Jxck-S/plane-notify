"""
serve_images.py: Simple HTTP Server for Images

This script runs a simple HTTP server to serve generated images from the temporary directory.
It is required because services like Instagram and Threads require a public web accessible URL to fetch images for posting.
This server exposes the local images so they can be accessed via a reverse proxy or directly if configured.
"""

import logging
import socketserver
import tempfile
from http.server import SimpleHTTPRequestHandler

logger = logging.getLogger(__name__)

PORT = 8080
DIRECTORY = f"{tempfile.gettempdir()}/plane-notify/imgs"

Handler = SimpleHTTPRequestHandler


class CusHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # expires_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=60)
        # expires_string = expires_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
        self.send_header("Cache-Control", "no-cache, no-store, max-age=0")
        # self.send_header('Expires', expires_string)
        super().end_headers()

    # Turn off Dir list
    def list_directory(self, path):
        self.send_error(404, "Directory listing has been disabled")


with socketserver.TCPServer(("", PORT), CusHandler) as httpd:
    logger.info(f"Serving {DIRECTORY} at port {PORT}")
    httpd.serve_forever()
