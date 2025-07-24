# telegram_utils.py
import asyncio
import logging
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Отправка сообщений в телеграм
async def send_telegram_alert(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=payload)
        return response.json()
    
    
    if __name__ == "__main__":
        application.run_polling()



