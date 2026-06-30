import logging

import httpx
from fastapi import APIRouter, Query, Request, Response

from app.config import settings

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
    Meta вызывает этот endpoint ОДИН РАЗ при настройке вебхука в Meta for
    Developers (и заново, если ты меняешь URL или Verify Token там).

    Правило простое: если hub.mode == "subscribe" и присланный hub.verify_token
    совпадает с тем, что мы сами задали — отвечаем телом hub.challenge как
    plain text. Если не совпадает — отвечаем 403, чтобы никто посторонний
    не смог подписаться на твой вебхук.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("Webhook verification succeeded")
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning("Webhook verification failed: token mismatch")
    return Response(status_code=403)


@router.post("/webhook")
async def receive_message(request: Request) -> dict[str, str]:
    """
    Meta присылает сюда POST-запрос на каждое событие (входящее сообщение,
    статус доставки и т.д.). Нам важно:
      1. Всегда быстро отвечать 200 OK — иначе Meta считает вебхук
         нерабочим и может временно остановить доставку.
      2. Разобрать вложенную структуру payload'а, чтобы достать текст
         сообщения и номер отправителя.
      3. На этапе 0 — просто отправить то же сообщение обратно (эхо).

    Структура payload от Meta (упрощённо):
    {
      "entry": [{
        "changes": [{
          "value": {
            "messages": [{
              "from": "77001234567",
              "text": {"body": "hello"}
            }]
          }
        }]
      }]
    }

    Важно: помимо входящих сообщений сюда же приходят статусы доставки
    (delivered/read) — у них нет ключа "messages", поэтому мы должны
    аккуратно проверять наличие данных на каждом уровне, а не падать
    с KeyError.
    """
    payload = await request.json()
    logger.info("Incoming webhook payload: %s", payload)

    message_text, sender_number = _extract_message(payload)

    if message_text and sender_number:
        await _send_whatsapp_text(to=sender_number, body=message_text)

    # Meta ожидает быстрый 200 OK независимо от того, было ли там
    # реальное сообщение или служебное событие (статус доставки и т.п.)
    return {"status": "received"}


def _extract_message(payload: dict) -> tuple[str | None, str | None]:
    """
    Безопасно достаёт текст и номер отправителя из вложенного payload'а.
    Возвращает (None, None), если это не текстовое сообщение
    (например, это просто статус доставки или другой тип события).
    """
    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        messages = value.get("messages")
        if not messages:
            # Это, например, событие статуса доставки — не сообщение
            return None, None

        message = messages[0]
        sender_number = message["from"]

        # На этапе 0 обрабатываем только текстовые сообщения.
        # Картинки/аудио/документы добавим позже при необходимости.
        if message.get("type") != "text":
            logger.info("Skipping non-text message of type: %s", message.get("type"))
            return None, None

        message_text = message["text"]["body"]
        return message_text, sender_number

    except (KeyError, IndexError) as exc:
        logger.warning("Could not parse webhook payload: %s", exc)
        return None, None


async def _send_whatsapp_text(to: str, body: str) -> None:
    """
    Отправляет текстовое сообщение через WhatsApp Cloud API (Graph API).
    На этапе 0 это просто эхо того, что прислал пользователь.
    """
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
