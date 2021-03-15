import os

import typing
import aioredis
import pydantic
from fastapi import FastAPI, Depends
from fastapi.logger import logger
from fastapi_plugins import RedisSettings, depends_redis, redis_plugin
import uvicorn

app = FastAPI()
KEY = "fastapi_cache_snippet"
redis_master = os.getenv('DATASTORE') if os.getenv('DATASTORE') else "localhost"
service_port = os.getenv('PORT') if os.getenv('PORT') else "8081"


class Other(pydantic.BaseSettings):
    pass


class AppSettings(Other, RedisSettings):
    pass


@app.on_event("startup")
async def startup():
    logger.info("server startup")
    config = AppSettings(redis_url="redis://" + redis_master)
    await redis_plugin.init_app(app=app, config=config)
    await redis_plugin.init()


@app.on_event("shutdown")
async def shutdown():
    await redis_plugin.terminate()
    logger.info("server shutdown")


@app.get("/")
async def root_get(
        cache: aioredis.Redis = Depends(depends_redis),
) -> typing.Dict:
    return dict(ping=await cache.ping())

@app.get("/hello/{msg}")
async def hello(msg: str, cache: aioredis.Redis = Depends(depends_redis)):
    c = await cache.get(KEY)
    if c:
        logger.info(f"existing item: {c}")
    else:
        c = f"Hello {msg}"
        await cache.set(KEY, c)
    return {"msg": c}

@app.get("/help")
def help():
    return {"urllookup": "/urlinfo/1/{hostname_and_port}/{original_path_and_query_string}"}

@app.get("/urlinfo/1/{hostname_and_port}/{original_path_and_query_string}")
async def urlinfo_v1(hostname_and_port: str, original_path_and_query_string: str, cache: aioredis.Redis = Depends(depends_redis)):
    c = await cache.get(hostname_and_port + "/" + original_path_and_query_string)
    if c:
        logger.info(f"existing item: {c}")
        return {"is_safe": False}

    return {"is_safe": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=service_port)
