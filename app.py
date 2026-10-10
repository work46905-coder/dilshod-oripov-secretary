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

chat_history = {}

SYSTEM_PROMPT = """
Siz Doktor Dilshod Oripovning Telegramdagi shaxsiy yozishmalariga
yordam beruvchi virtual yordamchisiz.

Foydalanuvchilar bilan o'zbek tilida, muloyim va professional
uslubda suhbatlashing.

Vazifalaringiz:
- Bemorlarning savollarini tushunish.
- Sog'liq bilan bog'liq savollarga umumiy ma'lumot berish.
- Kerak bo'lsa, bemordan qo'shimcha ma'lumot so'rash.
- Zarur hollarda shifokor ko'rigini tavsiya qilish.

Aniq tashxis qo'ymang.
Shifokor ko'rigisiz dori yoki davolash kursini buyurmang.
Shoshilinch xavf belgilarida tez tibbiy yordamga murojaat qilishni ayting.

O'zingizni Doktor Dilshod Oripovning o'zi deb ko'rsatmang.
So'ralsa, virtual yordamchi ekaningizni tushuntiring.

Javoblaringiz qisqa, aniq va tushunarli bo'lsin.
"""


@app.get("/")
def home():
    return {
        "status": "ok",
        "service": "Dilshod Oripov Telegram AI"
    }


def telegram_api(method, payload):
    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/{method}"
    )

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("ok"):
        raise RuntimeError(str(result))

    return result


def send_business_message(chat_id, connection_id, text):
    for start in range(0, len(text), 4000):
        telegram_api(
            "sendMessage",
            {
                "business_connection_id": connection_id,
                "chat_id": chat_id,
                "text": text[start:start + 4000]
            }
        )


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "business_connection" in data:
        print("BUSINESS CONNECTION RECEIVED", flush=True)
        return {"ok": True}

    message = data.get("business_message")

    if not message:
        return {"ok": True}

    chat = message.get("chat", {})
    sender = message.get("from", {})

    chat_id = chat.get("id")
    connection_id = message.get("business_connection_id")
    user_text = message.get("text")

    # Faqat mijozlarning shaxsiy xabarlarini qabul qilish
    if chat.get("type") != "private":
        return {"ok": True}

    # Botlarning xabarlariga javob bermaslik
    if sender.get("is_bot"):
        return {"ok": True}

    # Faqat matnli xabarlar
    if not chat_id or not connection_id or not user_text:
        return {"ok": True}

    print("BUSINESS MESSAGE RECEIVED:", chat_id, flush=True)

    try:
        history_key = f"{connection_id}:{chat_id}"

        history = chat_history.get(history_key, [])

        history.append({
            "role": "user",
            "content": user_text
        })

        history = history[-10:]

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=SYSTEM_PROMPT,
            input=history
        )

        answer = response.output_text

        if not answer:
            answer = (
                "Savolingizni tushunishda qiyinchilik bo'ldi. "
                "Iltimos, qayta yozing."
            )

        history.append({
            "role": "assistant",
            "content": answer
        })

        chat_history[history_key] = history[-10:]

        send_business_message(
            chat_id,
            connection_id,
            answer
        )

        print("BUSINESS MESSAGE SENT:", chat_id, flush=True)

    except Exception as e:
        print("ERROR:", str(e), flush=True)

    return {"ok": True}


@app.get("/set-webhook")
def set_webhook():
    webhook_url = (
        "https://dilshod-oripov-secretary.onrender.com/webhook"
    )

    return telegram_api(
        "setWebhook",
        {
            "url": webhook_url,
            "allowed_updates": [
                "business_connection",
                "business_message"
            ]
        }
    )
