"""
config/settings.py

Centraliza a configuração do JobHunter que NÃO muda de busca para
busca: credenciais, banco de dados e comportamento do robô. Os
critérios de busca (cargo e cidade) não ficam mais fixos aqui — eles
são informados pela pessoa em tempo real, por perfil de busca
(veja perfis/perfil_manager.py).
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Credenciais e segredos (NUNCA hardcode aqui, sempre via .env)
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print(
        "[AVISO] TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não configurados no .env. "
        "As notificações via Telegram não vão funcionar até isso ser corrigido."
    )


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/jobhunter.db")


# ---------------------------------------------------------------------------
# Valores sugeridos por padrão no prompt interativo (a pessoa pode aceitar
# apertando Enter, ou digitar outro valor na hora)
# ---------------------------------------------------------------------------
DEFAULT_CARGO = os.getenv("DEFAULT_CARGO", "assistente administrativo")
DEFAULT_CIDADE = os.getenv("DEFAULT_CIDADE", "Salvador")

# Arquivo onde os perfis de busca salvos pela pessoa ficam guardados
PERFIS_FILE = os.getenv("PERFIS_FILE", "perfis/perfis.json")


# ---------------------------------------------------------------------------
# Comportamento do robô / anti-bloqueio
# ---------------------------------------------------------------------------
HEADLESS = os.getenv("HEADLESS", "True").strip().lower() in ("1", "true", "yes")
DELAY_MIN = float(os.getenv("DELAY_MIN", "2"))
DELAY_MAX = float(os.getenv("DELAY_MAX", "5"))

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

VIEWPORT = {"width": 1366, "height": 768}
LOCALE = "pt-BR"
TIMEZONE_ID = "America/Bahia"
