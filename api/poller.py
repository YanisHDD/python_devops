import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)


async def poll_server(server_id: int, url: str, store: dict):
    """Checks the health of a single server and updates its status in the store."""
    server = store.get(server_id)
    if not server:
        return
    full_url = f"{url}{server.health_path}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(full_url)
        if resp.status_code == 200:
            server.status = "UP"
        else:
            server.status = "DEGRADED"
        logger.info("Poller check: Server %s is %s", server.name, server.status)
    except httpx.RequestError as e:
        server.status = "DOWN"
        logger.warning("Poller check failed for server %s: %s", server.name, e)


async def run_poll_loop(store: dict, interval: int = 10):
    """Periodically polls all registered servers concurrently."""
    while True:
        if store:
            tasks = [poll_server(sid, s.base_url(), store) for sid, s in store.items()]
            await asyncio.gather(*tasks)
        await asyncio.sleep(interval)
