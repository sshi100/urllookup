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
service_port = os.getenv('PORT') if os.getenv('PORT') else "8082"
blacklist_path = os.getenv('BLACKLIST') if os.getenv('BLACKLIST') else "../data/blacklist"


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
async def help():
    return {"usage": "/urlupdate/1/{group}/{hostname_and_port}/{original_path_and_query_string}"}

@app.post("/urlupdate/1/{group}/{hostname_and_port}/{original_path_and_query_string}")
async def urlupdate_v1(group: str, hostname_and_port: str, original_path_and_query_string: str, cache: aioredis.Redis = Depends(depends_redis)):
    key = hostname_and_port + "/" + original_path_and_query_string
    c = await cache.get(key)
    if c:
        logger.info(f"existing item: {key}")
    else:
        await cache.set(key, group)

    return {"is_added": key, "group": group}


@app.post("/urlupdate_batch/1/{group}")
async def urlupdate_batch_v1(group: str, cache: aioredis.Redis = Depends(depends_redis)):
    file_path = blacklist_path + "/" + group + ".txt"
    count_added = 0
    with open(file_path, 'r') as f:
        for line in f:
            key = line.rstrip('\n')
            c = await cache.get(key)
            if c:
                logger.info(f"existing item: {key}")
                print(f"old: group: {group}, key: {key}")
            else:
                await cache.set(key, group)
                logger.info(f"new: {key}")
                print(f"new: group: {group}, key: {key}")
                count_added += 1

    return {"group": group, "total_added": count_added}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=service_port)
