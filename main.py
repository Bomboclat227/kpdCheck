from pydantic import BaseModel
import httpx
from fastapi import FastAPI, HTTPException
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8082498905:AAH6dsU3rtYxdo7n0avI0sZ831gcQVSZz40"
CHAT_ID = "5860900715"

app = FastAPI()


class CheckRequest(BaseModel):
    url: str


class Message(BaseModel):
    text: str


@app.post("/send_message")
async def send_message_endpoint(message: Message):
    """Endpoint для отправки сообщения через API"""
    return await send_telegram_message(message.text)


async def send_telegram_message(text: str):
    """Внутренняя функция для отправки сообщений в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"  # Добавляем поддержку HTML форматирования
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, data=payload)
            if response.status_code == 200:
                logger.info("Сообщение в Telegram отправлено успешно")
                return {"status": "success", "response": response.json()}
            else:
                logger.error(f"Ошибка Telegram API: {response.status_code}")
                return {"status": "error", "code": response.status_code}
    except Exception as e:
        logger.error(f"Ошибка при отправке в Telegram: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/check_sourse")
async def check_service(data: CheckRequest):
    """Проверка доступности источника"""
    url = data.url
    logger.info(f"Проверка источника: {url}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)

        logger.info(f"Получен ответ от {url}: HTTP {response.status_code}")

        # Проверяем различные коды ошибок
        if response.status_code >= 500:  # 5xx ошибки сервера
            error_msg = (
                f"🚨 <b>Источник недоступен (Ошибка сервера)</b>\n"
                f"🌐 Sourse: {url}\n"
                f"📊 Status code: {response.status_code}\n"
                f"⏱ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await send_telegram_message(error_msg)
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Источник вернул ошибку сервера: {response.status_code}"
            )

        elif response.status_code >= 400:  # 4xx ошибки клиента
            error_msg = (
                f"⚠️ <b>Проблема с доступом к источнику</b>\n"
                f"🌐 Sourse: {response.status_code}\n"
                f"⏱ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await send_telegram_message(error_msg)
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ошибка доступа: {response.status_code}"
            )

        # Успешный ответ
        return {
            "status": "ok",
            "code": response.status_code,
            "url": url,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except httpx.ConnectError as e:
        error_msg = (
            f"❌ <b>Ошибка подключения к источнику</b>\n"
            f"🌐 URL: {url}\n"
            f"🔌 Ошибка: Не удается установить соединение\n"
            f"📝 Детали: {str(e)}\n"
            f"⏱ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.error(f"Ошибка подключения к {url}: {e}")
        await send_telegram_message(error_msg)
        raise HTTPException(status_code=502, detail="Источник недоступен - ошибка подключения")

    except httpx.TimeoutException as e:
        error_msg = (
            f"⏰ <b>Таймаут при обращении к источнику</b>\n"
            f"🌐 URL: {url}\n"
            f"⏱ Время ожидания истекло\n"
            f"📝 Детали: {str(e)}\n"
            f"⏱ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.error(f"Таймаут при обращении к {url}: {e}")
        await send_telegram_message(error_msg)
        raise HTTPException(status_code=504, detail="Источник недоступен - таймаут")

    except Exception as e:
        error_msg = (
            f"💥 <b>Неожиданная ошибка при проверке источника</b>\n"
            f"🌐 URL: {url}\n"
            f"❌ Ошибка: {str(e)}\n"
            f"⏱ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.error(f"Неожиданная ошибка при проверке {url}: {e}")
        await send_telegram_message(error_msg)
        raise HTTPException(status_code=502, detail=f"Источник недоступен: {str(e)}")


@app.get("/")
async def root():
    """Главная страница"""
    return {
        "message": "Source Checker API",
        "endpoints": {
            "POST /check_sourse": "Проверить доступность источника",
            "POST /send_message": "Отправить сообщение в Telegram",
            "GET /health": "Проверка работоспособности"
        }
    }


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "telegram_configured": bool(TELEGRAM_TOKEN and CHAT_ID)
    }


@app.post("/test-telegram")
async def test_telegram():
    """Тестовая отправка сообщения в Telegram"""
    test_message = (
        f"🧪 <b>Тестовое сообщение</b>\n"
        f"⏱ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"✅ Сервис проверки источников работает корректно"
    )

    result = await send_telegram_message(test_message)
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)