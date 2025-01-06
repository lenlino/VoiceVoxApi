import json
import os
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
enabled_tokens = []


@app.post("/{token}/{params}")
async def post_item(
    token: str, params: str, request: Request, body=Body(default=None)
):
    if is_enabled_token(token) is False:
        raise HTTPException(status_code=401, detail="invalid token")
    print(enabled_tokens)
    if body is None:
        headers = {}
    else:
        headers = {'Content-Type': 'application/json', }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://{VOICEVOX_ADDRESS}/{params}?{request.query_params}",
                                data=json.dumps(body), headers=headers) as response:
            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])
            if response.headers['content-type'] == "audio/wav":
                return Response(await response.read(), media_type="audio/wav")
            else:
                return await response.json()


@app.get("/{token}/{params}")
async def get_item(
    token: str, params: str, request: Request, body=Body(default=None)
):
    if is_enabled_token(token) is False:
        raise HTTPException(status_code=401, detail="invalid token")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://{VOICEVOX_ADDRESS}/{params}?{request.query_params}",
                               data=json.dumps(body)) as response:
            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])

            if response.headers['content-type'] == "audio/wav":
                return await response.read()
            else:
                return await response.json()

def reset_limit_job():
    print("This job is run every day at 0:00")



def is_enabled_token(token):
    if token in enabled_tokens:
        return True
    for d in stripe.Subscription.search(limit=10,
                                        query=f"status:'active' AND metadata['voicevox_token']:'{token}'"):
        enabled_tokens.append(token)
        return True
    for d in stripe.Subscription.search(limit=10,
                                        query=f"status:'trialing' AND metadata['voicevox_token']:'{token}'"):
        enabled_tokens.append(token)
        return True
    return False

# スケジューラインスタンスを作成します
scheduler = BackgroundScheduler(timezone=utc)
# 毎日0時に関数を実行するタスクを追加します
scheduler.add_job(reset_limit_job, 'cron', hour=0)
# スケジューラを起動します
scheduler.start()
