import os
import json
import urllib.request
import urllib.parse

from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


@app.get("/")
def home():
    return {
        "status": "ok",
        "service": "Dilshod Oripov AI Secretary"
    }
