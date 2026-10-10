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
        "service": "Dilshod Oripov"
    }

SYSTEM_PROMPT = """
Siz Dilshod Oripovning shaxsiy onlayn sekretarisiz.

Suhbat davomida o'zingizni bot, AI, sun'iy intellekt yoki dastur deb tanishtirmang.
Foydalanuvchiga tabiiy, muloyim va professional tarzda javob bering.

Sizning vazifangiz:
- bemorning murojaatini tushunish;
- kerakli ma'lumotlarni aniqlashtirish;
- qisqa va tushunarli javob berish;
- zarur bo'lsa, Dilshod Oripov bilan bog'lanish yoki konsultatsiya bo'yicha yo'naltirish.

Tibbiy tashxisni o'zingiz mustaqil ravishda aniq qo'ymang.
"""

chat_history = {}
def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text
    }).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))
        @app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    user_text = message.get("text")

    if not chat_id or not user_text:
        return {"ok": True}

    try:
        history = chat_history.get(chat_id, [])

        history.append({
            "role": "user",
            "content": user_text
        })

        history = history[-10:]

        response = client.responses.create(
            model="gpt-5.4-mini",
            instructions=SYSTEM_PROMPT,
            input=history
        )

        answer = response.output_text

        history.append({
            "role": "assistant",
            "content": answer
        })

        chat_history[chat_id] = history[-10:]

        send_telegram_message(chat_id, answer)

    except Exception as e:
        print("ERROR:", str(e))
        send_telegram_message(
            chat_id,
            "Kechirasiz, hozir texnik xatolik yuz berdi. Iltimos, birozdan keyin qayta yozing."
        )

    return {"ok": True}
    @app.get("/set-webhook")
def set_webhook():
    webhook_url = "https://dilshod-oripov-secretary.onrender.com/webhook"

    url = (
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        f"?url={urllib.parse.quote(webhook_url, safe=':/')}"
    )

    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))
