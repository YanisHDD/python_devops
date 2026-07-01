import asyncio
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from models import Server, ServerIn, ServerOut
from auth import verify_api_key
from metrics import get_system_metrics
from poller import run_poll_loop, poll_server
from config import ConfigLoader

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")

_store: dict[int, Server] = {}
_counter = 0
poll_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global poll_task, _counter
    # Startup: Load initial servers from servers.json
    try:
        import pathlib
        config_path = pathlib.Path(__file__).parent / "servers.json"
        loader = ConfigLoader(str(config_path))
        servers = loader.load()
        for s in servers:
            _store[s.id] = s
            _counter = max(_counter, s.id)
        logger.info("Loaded %d initial servers from servers.json", len(servers))
    except Exception as e:
        logger.warning("Could not load initial servers: %s", e)

    # Launch background polling task
    poll_task = asyncio.create_task(run_poll_loop(_store))
    yield
    # Shutdown: Cancel the polling task
    if poll_task:
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="DevOps Monitoring API", version="1.0", lifespan=lifespan)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "servers_monitored": len(_store)}


@app.get("/metrics", tags=["System"])
async def metrics_endpoint():
    return get_system_metrics()


@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            metrics = get_system_metrics()
            await websocket.send_text(json.dumps(metrics))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass


@app.post("/servers", response_model=ServerOut, status_code=201, tags=["Servers"])
async def register_server(server: ServerIn, _key: str = Depends(verify_api_key)):
    global _counter
    _counter += 1
    record = Server(
        id=_counter,
        name=server.name,
        host=server.host,
        port=server.port,
        tags=server.tags,
        health_path=server.health_path
    )
    _store[_counter] = record
    return record


@app.get("/servers", response_model=list[ServerOut], tags=["Servers"])
async def list_servers(status: str | None = None):
    servers = list(_store.values())
    if status:
        servers = [s for s in servers if s.status == status]
    return servers


@app.get("/servers/{server_id}", response_model=ServerOut, tags=["Servers"])
async def get_server(server_id: int):
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")
    return _store[server_id]


@app.delete("/servers/{server_id}", status_code=204, tags=["Servers"])
async def delete_server(server_id: int, _key: str = Depends(verify_api_key)):
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")
    del _store[server_id]


@app.post("/servers/{server_id}/check", response_model=ServerOut, tags=["Servers"])
async def trigger_check(server_id: int):
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")
    await poll_server(server_id, _store[server_id].base_url(), _store)
    return _store[server_id]
