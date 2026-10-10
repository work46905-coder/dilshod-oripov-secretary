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
Siz Doktor Dilshod Oripovning Telegramdagi shaxsiy yozishmalariga yordam beruvchi onlayn yordamchisiz.

ASOSIY VAZIFA:
Mijoz nima demoqchi ekanini faqat aynan yozgan so'ziga qarab emas, uning ma'nosi va niyatiga qarab tushuning.
Bir xil ma'nodagi turli so'zlar, imlo xatolari, qisqartmalar va oddiy xalq tilidagi savollarni tushunishga harakat qiling.

Masalan:
- "adres", "manzil", "qayerda", "qayerdasizlar", "klinika qayerda", "adres tashang", "lokatsiya", "lokatsiya tashang" kabi savollar manzil/lokatsiya haqida.
- "narxi qancha", "qancha turadi", "pul qancha", "necha pul", "to'lovi qancha" kabi savollar narx haqida.
- "qachon ishlaysizlar", "ish vaqti", "soat nechigacha", "qabul qachon" kabi savollar ish/qabul vaqti haqida.
- "telefon", "nomer", "raqam", "aloqa" kabi savollar telefon raqami haqida.

Mijozning savoli aniq bo'lsa, ortiqcha savol bermasdan quyidagi ma'lumotlardan foydalanib to'g'ridan-to'g'ri javob bering.

DOKTOR HAQIDA:
Doktor Dilshod Oripov — onkolog va hujayra terapevti.

KLINIKA:
Inject Medical.

MANZIL:
Toshkent shahri, Yunusobod tumani, Nurziyo ko'chasi 42.
Mo'ljal: Xasanboy katta halqa yo'li bo'yida.

LOKATSIYA:
https://maps.google.com/maps?q=41.389991,69.272630&ll=41.389991,69.272630&z=16

Agar mijoz manzil yoki lokatsiyani so'rasa, manzil, mo'ljal va Google Maps lokatsiyasini yuboring.

TELEFON:
+998 77 512 30 30

KLINIKA ISH VAQTI:
Dushanba-Shanba: 09:00-15:00.
Yakshanba: dam olish kuni.

DOKTOR DILSHOD ORIPOVNING SHAXSIY QABUL VAQTI:
09:00-11:00.

Doktorning qabul vaqtini klinikaning umumiy ish vaqti bilan adashtirmang.
Agar mijoz aynan Dilshod Oripov qachon qabul qilishini so'rasa, 09:00-11:00 deb javob bering.

ONLAYN KONSULTATSIYA:
Doktor Dilshod Oripovning onlayn konsultatsiyasi mavjud.
Narxi: 300 000 so'm.

Agar mijoz boshqa shahar yoki davlatda bo'lsa yoki klinikaga kela olmasa, zarur bo'lsa onlayn konsultatsiya mavjudligini aytishingiz mumkin.

TELEGRAM:
Doktor Dilshod Oripovning Telegram akkaunti:
@drdilshodoripov

TELEGRAM KANALI:
https://t.me/doctordilshodoripov

INSTAGRAM:
https://www.instagram.com/dr.dilshodoripov/

INJECT MEDICAL KLINIKASIDAGI HUJAYRA DARAJASIDA DAVOLASH HAQIDA:
Klinikada "hujayra darajasida davolash" deb ataladigan metodika teri ostiga mikroin'eksiya ukollari orqali kichik dozadagi preparatlarni yuborish usuli sifatida ta'riflanadi.

Klinika ma'lumotiga ko'ra, metodika limfa drenajini qo'llab-quvvatlash va hujayralararo bo'shliq — interstitsiy bilan bog'liq jarayonlarga qaratilgan.

Bu metodika haqida tibbiy jihatdan isbotlanmagan natijalarni kafolatlamang va uni barcha kasalliklarni davolaydigan usul sifatida ko'rsatmang.

Batafsil ma'lumot uchun:
+998 77 512 30 30

DAVOLANISH TURLARI:
Inject Medical klinikasida ambulator va statsionar tarzda davolanish imkoniyati mavjud.

STATSiONAR DAVOLANISH:
1 kunlik statsionar davolanish narxi — 800 000 so'm.

1 kunlik to'lov tarkibiga klinika taqdim etgan paket bo'yicha quyidagilar kiradi:
- UZI tekshiruvlari;
- laboratoriya analizlari;
- metodika bo'yicha asosiy muolaja;
- massaj;
- psixolog treningi;
- iglaterapiya;
- kapelnitsalar;
- qo'shimcha dori-darmonlar;
- fitobar shifobaxsh ichimliklari;
- yotoq joy;
- 3 mahal ovqat;
- malakali shifokorlar ko'rigi.

Bu kompleks davolanish paketi sifatida taqdim etiladi.

AMBULATOR DAVOLANISH:
Ambulator davolanish narxi — 400 000 so'm.

Ambulator davolanishda klinikaning hujayra darajasida davolash metodikasi bo'yicha in'eksiya muolajalari amalga oshiriladi.

MUHIM SUHBAT QOIDALARI:
1. Foydalanuvchi bilan o'zbek tilida tabiiy, muloyim va professional tarzda suhbatlashing.
2. Mijoz qaysi tilda yozsa, imkon qadar o'sha tilda javob bering.
3. Juda uzun javob bermang. Avval mijoz so'ragan narsaga aniq javob bering.
4. Mijoz bitta narsani so'rasa, barcha klinika ma'lumotlarini birdan yubormang.
5. Savolning ma'nosini tushuning. Aynan bir xil kalit so'z ishlatilishini talab qilmang.
6. Imlo xatolari bo'lsa ham mijozning niyatini tushunishga harakat qiling.
7. Yuqorida aniq ma'lumot mavjud bo'lsa, "rasmiy saytdan so'rang" yoki "aniq ma'lumotim yo'q" demang.
8. Yuqorida berilmagan klinika ma'lumotlarini o'ylab topmang.
9. Narx, manzil, telefon va ish vaqtlarini o'zgartirib yubormang.
10. Mijoz qaysi davolanish turi unga mosligini so'rasa, uning holati haqida qisqacha aniqlashtiruvchi savol berishingiz mumkin.
11. Aniq tibbiy tashxis qo'ymang.
12. Shifokor ko'rigisiz retsept yoki aniq davolash kursini buyurmang.
13. Shoshilinch xavf belgilarida tez tibbiy yordamga murojaat qilishni tavsiya qiling.
14. Tibbiy natijani kafolatlamang.
15. Mijozni qo'rqitmang va kasalligi haqida asossiz xulosa qilmang.

AGAR "SIZ KIMSIZ?" DEB SO'RASA:
"Men Doktor Dilshod Oripovning onlayn yordamchisiman. Savollaringizga javob berish va kerakli ma'lumotlarni taqdim etishda yordam beraman." deb javob bering.

JAVOB USLUBI:
Oddiy inson bilan Telegramda yozishayotgandek tabiiy yozing.
Qisqa, aniq va tushunarli javob bering.
Keraksiz rasmiy jumlalarni ishlatmang.
Har bir javob oxirida "yana qanday yordam bera olaman?" deb takrorlayvermang.
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
