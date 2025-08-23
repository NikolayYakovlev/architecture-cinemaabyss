import os
import random
from fastapi import FastAPI, Request, Response
import httpx
import logging

from utils import make_response

logging.basicConfig(level=logging.INFO)

app = FastAPI()

MONOLITH_URL = os.getenv("MONOLITH_URL")
MOVIES_SERVICE_URL = os.getenv("MOVIES_SERVICE_URL")
GRADUAL_MIGRATION = os.getenv("GRADUAL_MIGRATION", "false").lower() == "true"
MOVIES_MIGRATION_PERCENT = int(os.getenv("MOVIES_MIGRATION_PERCENT", "0"))

@app.api_route("/api/movies", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_movies(request: Request):
    if GRADUAL_MIGRATION:
        if random.randint(1, 100) <= MOVIES_MIGRATION_PERCENT:
            target = MOVIES_SERVICE_URL
        else:
            target = MONOLITH_URL
    else:
        target = MONOLITH_URL
    logging.info(f"Request to /api/movies routed to: {target}")     # логирование запроса для отслеживания нагрузки в логах
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            request.method,
            f"{target}/api/movies",
            headers = dict(request.headers),
            content = await request.body(),
            params = request.query_params
        )
        return make_response(resp)

@app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_monolith(request: Request, full_path: str):
    url = f"{MONOLITH_URL}/api/{full_path}"
    logging.info(f"Request to /api/{full_path} routed to: {url}")   # логирование запроса для отслеживания перенаправления запросов в монолит
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            request.method,
            url,
            headers = dict(request.headers),
            content = await request.body(),
            params = request.query_params
        )
        return make_response(resp)

@app.get("/health")
async def health():
    return {"status": "ok"}
