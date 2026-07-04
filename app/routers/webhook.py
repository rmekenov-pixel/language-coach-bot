import logging

import httpx
from fastapi import APIRouter, Query, Request, Response

from app.config import settings
from app.services import coach

logger = logging.getLogger("webhook")

router = APIRouter()

GRAPH_API_BASE = "https://graph.facebook.com"


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> Response:
    """
    Meta вызывает этот endpoint при настройке вебхука.
    Проверяем verify_token и возвращаем challenge.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("Webhook verification succeeded")
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning("Webhook verification failed: token mismatch")
    return Response(status_code=403)


@router.post("/webhook")
async def receive_message(request: Request) -> dict[str, str]:
    """
    Получаем входящее сообщение от Meta, передаём коучу, отправляем ответ.
    Всегда возвращаем 200 OK быстро — иначе Meta решит, что вебхук сломан.
    """
    payload = await request.json()
    logger.info("Incoming webhook payload: %s", payload)

    message_text, sender_number = _extract_message(payload)

    if message_text and sender_number:
        # Специальная команда: сброс истории диалога
        if message_text.strip().lower() == "/reset":
            from app.services.memory import clear_history
            clear_history(sender_number)
            await _send_whatsapp_text(
                to=sender_number,
                body="History cleared! Let's start fresh. Hello! 👋 How are you today?"
            )
        else:
            # Получаем ответ от коуча (вызов Groq)
            response_text = await coach.get_coach_response(sender_number, message_text)
            await _send_whatsapp_text(to=sender_number, body=response_text)

    return {"status": "received"}


def _extract_message(payload: dict) -> tuple[str | None, str | None]:
    """
    Безопасно достаёт текст и номер отправителя из payload Meta.
    Возвращает (None, None) для не-текстовых событий.
    """
    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        messages = value.get("messages")
        if not messages:
            return None, None

        message = messages[0]
        sender_number = message["from"]

        if message.get("type") != "text":
            logger.info("Skipping non-text message of type: %s", message.get("type"))
            return None, None

        message_text = message["text"]["body"]
        return message_text, sender_number

    except (KeyError, IndexError) as exc:
        logger.warning("Could not parse webhook payload: %s", exc)
        return None, None


async def _send_whatsapp_text(to: str, body: str) -> None:
    """Отправляет текстовое сообщение через WhatsApp Cloud API."""
    url = (
        f"{GRAPH_API_BASE}/{settings.whatsapp_api_version}/"
        f"{settings.whatsapp_phone_number_id}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=10.0)

    if response.status_code >= 400:
        logger.error(
            "Failed to send WhatsApp message: %s %s",
            response.status_code,
            response.text,
        )
    else:
        logger.info("Message sent to %s", to)
