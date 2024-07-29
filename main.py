from typing import Union, Optional

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

app = FastAPI()
whitelist = ["audio_query", "sing_frame_audio_query", "accent_phrases", "mora_data", "mora_length",
             "mora_pitch", "sing_frame_volume", "synthesis", "multi_synthesis", "frame_synthesis",
             "morphable_targets", "synthesis_morphing", "connect_waves", "validate_kana", "speakers",
             "speaker_info", "singers", "singer_info", "version"]

@app.post("/{token}/{params}")
async def post_item(
    token: str, params: str, request: Request
):
    print(request.query_params)
    print(token)
    print(params)
    return {}

@app.get("/{token}/{params}")
async def get_item(
    token: str, params: str, request: Request
):
    print(request.query_params)
    print(await request.json())
    print(token)
    print(params)
    return {}