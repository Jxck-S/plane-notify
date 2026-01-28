"""
heartbeat_server.py: Service Health & Control Server

This module implements a lightweight HTTP server using the standard library.
It provides endpoints for:
1. Health Monitoring (/heartbeat): Returns a timestamp to indicate the service is running.
2. Configuration Management (/reload): Triggers a hot-reload of the application configuration without restarting the process.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from threading import Lock
import logging
import traceback

import json  # Import for JSON encoding

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#import get_heartbeat from the main


class Heartbeat:
    def __init__(self):
        self.shared_timestamp_variable = None
        self.timestamp_lock = Lock()
        self.config_manager = None
        self.planes_dict = None
        self.reload_requested = False
        self.reload_stats = None

    def update_timestamp(self):
        with self.timestamp_lock:
            self.shared_timestamp_variable = time.time()

    def get_heartbeat(self):
        with self.timestamp_lock:
            return self.shared_timestamp_variable
    
    def set_config_manager(self, config_manager, planes_dict):
        """Link config manager and planes dict for reloading"""
        self.config_manager = config_manager
        self.planes_dict = planes_dict
    
    def request_reload(self):
        """Request a config reload"""
        with self.timestamp_lock:
            self.reload_requested = True
        return True
    
    def check_and_clear_reload(self):
        """Check if reload was requested and clear flag"""
        with self.timestamp_lock:
            if self.reload_requested:
                self.reload_requested = False
                return True
            return False
    
    def get_and_clear_reload_stats(self):
        """Get reload stats and clear them"""
        with self.timestamp_lock:
            stats = self.reload_stats
            self.reload_stats = None
            return stats


def run_heartbeat_server(hb: Heartbeat):
  class HeartbeatHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            """Override to use logging instead of print"""
            logger.info("%s - - [%s] %s\n" %
                       (self.address_string(),
                        self.log_date_time_string(),
                        format%args))
        
        def do_GET(self):
            try:
                if self.path == '/heartbeat':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    content = bytes(json.dumps({"timestamp": hb.get_heartbeat()}), 'utf-8')
                    self.wfile.write(content)
                elif self.path == '/reload':
                    # Trigger config reload
                    success = hb.request_reload()
                    
                    # Wait briefly for reload to complete and get stats
                    time.sleep(0.1)
                    max_wait = 50  # 5 seconds max
                    while max_wait > 0:
                        stats = hb.get_and_clear_reload_stats()
                        if stats is not None:
                            break
                        time.sleep(0.1)
                        max_wait -= 1
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    
                    response = {"status": "reload_completed", "success": success}
                    if stats:
                        response.update(stats)
                    
                    content = bytes(json.dumps(response), 'utf-8')
                    self.wfile.write(content)
                else:
                    self.send_error(404, 'Not Found')
            except Exception as e:
                logger.error(f"Error handling request {self.path}: {e}")
                logger.error(traceback.format_exc())
                try:
                    self.send_error(500, 'Internal Server Error')
                except:
                    pass
  
  server_address = ('', 8778)  # Bind to all interfaces, port 8000 (adjust if needed)
  
  while True:
      try:
          httpd = HTTPServer(server_address, HeartbeatHandler)
          logger.info(f'Heartbeat server starting on port {server_address[1]}')
          httpd.serve_forever()
      except Exception as e:
          logger.error(f"Heartbeat server crashed: {e}")
          logger.error(traceback.format_exc())
          logger.info("Restarting heartbeat server in 5 seconds...")
          time.sleep(5)
