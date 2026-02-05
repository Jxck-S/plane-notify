"""web/server.py: FastAPI server for the control dashboard and WebSocket communication."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from config_manager import ConfigManager
    from plane import Plane

# Initialize logging
logger = logging.getLogger("web_server")


app = FastAPI(title="Plane Notify Control", version="2.2.0")

# Determine paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Global state
config_manager = None
planes_list = []
start_time = time.time()


class ConnectionManager:
    """Manage active WebSocket connections for real-time status updates."""

    def __init__(self) -> None:
        """Initialize the connection manager with an empty list of connections."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection and track it."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the tracked list."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        """
        Send a message to all active WebSocket connections.

        :param message: The string message to broadcast.
        """
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.exception("Error broadcasting message: %s", e)


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> FileResponse:
    """Serve the static dashboard HTML."""
    return FileResponse(TEMPLATE_DIR / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Handle WebSocket communication for the dashboard.

    Processes reload requests and broadcasts status updates.
    """
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
                            def sync_status_callback(msg: str) -> None:
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
                            logger.exception("Reload failed: %s", e)
                            await manager.broadcast(
                                json.dumps(
                                    {
                                        "type": "error",
                                        "message": f"Reload failed: {e!s}",
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
async def heartbeat() -> dict[str, str | float | int]:
    """Provide a health check endpoint for the server."""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "uptime": time.time() - start_time,
        "plane_count": len(planes_list),
    }


# Keep HTTP endpoint for backward compatibility/scripts
@app.get("/reload")
async def reload_config_http() -> dict[str, int]:
    """Trigger a configuration reload via standard HTTP request."""
    if config_manager is None:
        raise HTTPException(status_code=503, detail="Config Manager not initialized")

    return config_manager.reload_all_configs(planes_list)


def run_server(host: str = "127.0.0.1", port: int = 8778) -> None:
    """Run the Uvicorn server."""
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


def start_web_server(
    cm: ConfigManager,
    planes: list[Plane],
    host: str = "127.0.0.1",
    port: int = 8778,
) -> threading.Thread:
    """Start the web server in a background daemon thread."""
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
    logger.info("Web server thread started on %s:%s", host, port)
    return server_thread
