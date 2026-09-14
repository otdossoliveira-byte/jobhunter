"""
notifications/telegram_notifier.py

Envia alertas via Telegram Bot toda vez que uma nova vaga relevante é
salva no banco. Usa apenas `requests` chamando a API HTTP do Telegram
diretamente (sem dependência extra de python-telegram-bot), o que
mantém o projeto mais leve e fácil de rodar.
"""

import requests

from config import settings
from database.models import Vaga

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def enviar_notificacao(vaga: Vaga) -> bool:
    """
    Envia uma mensagem formatada para o chat configurado no .env.
    Retorna True se o Telegram confirmou o envio, False caso contrário.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        print("[Telegram] Token ou Chat ID não configurados — notificação não enviada.")
        return False

    texto = (
        "🆕 *Nova vaga encontrada!*\n\n"
        f"📌 *Cargo:* {_escapar(vaga.titulo_vaga)}\n"
        f"🏢 *Empresa:* {_escapar(vaga.empresa)}\n"
        f"📍 *Cidade:* {_escapar(vaga.cidade)}\n"
        f"🌐 *Fonte:* {_escapar(vaga.fonte)}\n"
        f"🗂️ *Perfil:* {_escapar(vaga.perfil_busca or '—')}\n"
        f"🔗 [Ver vaga]({vaga.link_vaga})"
    )

    url = TELEGRAM_API_URL.format(token=settings.TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": texto,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False,
    }

    try:
        resposta = requests.post(url, json=payload, timeout=15)
        resposta.raise_for_status()
        return True
    except requests.RequestException as erro:
        print(f"[Telegram] Falha ao enviar notificação: {erro}")
        return False


def _escapar(texto: str) -> str:
    """Escapa caracteres especiais do Markdown do Telegram para evitar erro 400."""
    caracteres_especiais = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]
    for caractere in caracteres_especiais:
        texto = texto.replace(caractere, f"\\{caractere}")
    return texto
