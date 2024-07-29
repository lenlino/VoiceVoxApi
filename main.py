from typing import Union, Optional

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

app = FastAPI()


@app.get("/{token}/{params}")
async def read_user_item(
    token: str, params: str, request: Request
):
    print(request.client.host)
    print(token)
    print(params)
    return {}