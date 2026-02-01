import asyncio
import json
import logging
import os
import threading
import time

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Initialize logging
logger = logging.getLogger("web_server")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Plane Notify Control", version="2.2.0")

# Determine paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Global state
config_manager = None
planes_list = []
start_time = time.time()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the static dashboard HTML"""
    return FileResponse(os.path.join(TEMPLATE_DIR, "index.html"))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                request = json.loads(data)
                if request.get("action") == "reload":
                    # Broadcast start status
                    await manager.broadcast(
                        json.dumps(
                            {
                                "type": "status",
                                "message": "Starting configuration reload...",
                            }
                        )
                    )

                    if config_manager:
                        try:
                            # Run reload in thread pool to avoid blocking event loop
                            loop = asyncio.get_running_loop()

                            # Define callback to pipe logs to WebSocket
                            def sync_status_callback(msg: str):
                                asyncio.run_coroutine_threadsafe(
                                    manager.broadcast(
                                        json.dumps({"type": "status", "message": msg})
                                    ),
                                    loop,
                                )

                            stats = await loop.run_in_executor(
                                None,
                                config_manager.reload_all_configs,
                                planes_list,
                                sync_status_callback,
                            )

                            # Broadcast success
                            await manager.broadcast(
                                json.dumps({"type": "result", "data": stats})
                            )
                        except Exception as e:
                            logger.error(f"Reload failed: {e}")
                            await manager.broadcast(
                                json.dumps(
                                    {
                                        "type": "error",
                                        "message": f"Reload failed: {str(e)}",
                                    }
                                )
                            )
                    else:
                        await manager.broadcast(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "Config Manager not initialized",
                                }
                            )
                        )

            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/heartbeat")
async def heartbeat():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "uptime": time.time() - start_time,
        "plane_count": len(planes_list),
    }


# Keep HTTP endpoint for backward compatibility/scripts
@app.get("/reload")
async def reload_config_http():
    """Trigger configuration reload (HTTP)"""
    if config_manager is None:
        raise HTTPException(status_code=503, detail="Config Manager not initialized")

    stats = config_manager.reload_all_configs(planes_list)
    return stats


def run_server(host: str = "127.0.0.1", port: int = 8778):
    """Run Uvicorn server"""
    # install_signal_handlers=False is CRITICAL to allow the main thread
    # to handle shutdown (Ctrl+C) correctly.
    # Restore startup info (log_level="info") but keep request spam off (access_log=False)
    config = uvicorn.Config(
        app, host=host, port=port, log_level="info", access_log=False
    )
    server = uvicorn.Server(config)

    # Manually disable signal handlers to prevent Uvicorn from capturing Ctrl+C
    server.install_signal_handlers = lambda: None
    server.run()


def start_web_server(cm, planes, host: str = "127.0.0.1", port: int = 8778):
    """Start the web server in a background thread"""
    global config_manager, planes_list
    config_manager = cm
    planes_list = planes

    server_thread = threading.Thread(
        target=run_server,
        kwargs={"host": host, "port": port},
        name="web_server",
        daemon=True,
    )
    server_thread.start()
    logger.info(f"Web server thread started on {host}:{port}")
    return server_thread
