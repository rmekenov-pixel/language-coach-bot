import logging

import httpx
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_session
from app.services import coach, memory
from app.services.progress_service import get_progress_summary

logger = logging.getLogger("webhook")

router = APIRouter()

GRAPH_API_BASE = "https://graph.facebook.com"


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> Response:
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("Webhook verification succeeded")
        return Response(content=hub_challenge, media_type="text/plain")
    logger.warning("Webhook verification failed: token mismatch")
    return Response(status_code=403)


@router.post("/webhook")
async def receive_message(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    payload = await request.json()
    logger.info("Incoming webhook payload: %s", payload)

    message_text, sender_number = _extract_message(payload)

    if message_text and sender_number:
        cmd = message_text.strip().lower()

        if cmd == "/reset":
            await memory.clear_history(session, sender_number)
            await _send_whatsapp_text(
                to=sender_number,
                body="History cleared! Let's start fresh. Hello! 👋 How are you today?"
            )
        elif cmd == "/progress":
            summary = await get_progress_summary(session, sender_number)
            await _send_whatsapp_text(to=sender_number, body=summary)
        else:
            response_text = await coach.get_coach_response(
                session, sender_number, message_text
            )
            await _send_whatsapp_text(to=sender_number, body=response_text)

    return {"status": "received"}


def _extract_message(payload: dict) -> tuple[str | None, str | None]:
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
            return None, None
        return message["text"]["body"], sender_number
    except (KeyError, IndexError) as exc:
        logger.warning("Could not parse webhook payload: %s", exc)
        return None, None


async def _send_whatsapp_text(to: str, body: str) -> None:
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
        logger.error("Failed to send WhatsApp message: %s %s", response.status_code, response.text)
    else:
        logger.info("Message sent to %s", to)
