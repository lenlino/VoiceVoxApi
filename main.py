import json
import os
import re
import sqlite3
import time
from datetime import datetime
from typing import Annotated, Union, Optional

import aiohttp
import stripe
from dotenv import load_dotenv
from fastapi import Body, FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, Response
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

load_dotenv()

stripe.api_key = os.environ.get("STRIPE_API_KEY", None)
VOICEVOX_ADDRESS = os.environ.get("VOICEVOX_ADDRESS", None)
app = FastAPI()
whitelist = ["audio_query", "sing_frame_audio_query", "accent_phrases", "mora_data", "mora_length",
             "mora_pitch", "sing_frame_volume", "synthesis", "multi_synthesis", "frame_synthesis",
             "morphable_targets", "synthesis_morphing", "connect_waves", "validate_kana", "speakers",
             "speaker_info", "singers", "singer_info", "version"]
enabled_tokens = {}
TOKEN_CACHE_SECONDS = 600

db = sqlite3.connect(os.environ.get("USAGE_DB", "usage.db"), check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS usage (token TEXT, month TEXT, count INTEGER, PRIMARY KEY (token, month))")


def check_request(token, params):
    if params not in whitelist:
        raise HTTPException(status_code=404)
    if is_enabled_token(token) is False:
        raise HTTPException(status_code=401, detail="invalid token")
    db.execute("INSERT INTO usage VALUES (?, ?, 1) ON CONFLICT(token, month) DO UPDATE SET count = count + 1",
               (token, datetime.now().strftime("%Y-%m")))
    db.commit()


@app.post("/{token}/{params}")
async def post_item(
    token: str, params: str, request: Request, body=Body(default=None)
):
    check_request(token, params)
    if body is None:
        headers = {}
    else:
        headers = {'Content-Type': 'application/json', }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://{VOICEVOX_ADDRESS}/{params}?{request.query_params}",
                                data=json.dumps(body), headers=headers) as response:
            if response.status >= 400:
                print("upstream", params, response.status)
            return Response(await response.read(), status_code=response.status,
                            media_type=response.headers.get("content-type"))


@app.get("/{token}/{params}")
async def get_item(
    token: str, params: str, request: Request, body=Body(default=None)
):
    check_request(token, params)
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://{VOICEVOX_ADDRESS}/{params}?{request.query_params}",
                               data=json.dumps(body)) as response:
            if response.status >= 400:
                print("upstream", params, response.status)
            return Response(await response.read(), status_code=response.status,
                            media_type=response.headers.get("content-type"))

def reset_limit_job():
    print("This job is run every day at 0:00")



def is_enabled_token(token):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", token):
        return False
    if enabled_tokens.get(token, 0) > time.monotonic():
        return True
    for d in stripe.Subscription.search(limit=10,
                                        query=f"status:'active' AND metadata['voicevox_token']:'{token}'"):
        enabled_tokens[token] = time.monotonic() + TOKEN_CACHE_SECONDS
        return True
    for d in stripe.Subscription.search(limit=10,
                                        query=f"status:'trialing' AND metadata['voicevox_token']:'{token}'"):
        enabled_tokens[token] = time.monotonic() + TOKEN_CACHE_SECONDS
        return True
    return False

# スケジューラインスタンスを作成します
scheduler = BackgroundScheduler(timezone=utc)
# 毎日0時に関数を実行するタスクを追加します
scheduler.add_job(reset_limit_job, 'cron', hour=0)
# スケジューラを起動します
scheduler.start()
