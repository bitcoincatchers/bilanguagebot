"""
Dual-Language Crypto Telegram Bot - Configuration
"""

import os

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
ALLOWED_USER_ID = int(os.getenv('ALLOWED_USER_ID', '1037845888'))

# Target Channels
CHANNEL_ES = os.getenv('CHANNEL_ES', '@cryptosignalapp')
CHANNEL_EN = os.getenv('CHANNEL_EN', '@signalsaicrypto')

# Anthropic
ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')

# Footer — appended after every translation
CTA_ES = (
    "\n\n"
    "🤖 Prueba nuestros bots de trading automatizado: https://atomated-trade-zen.lovable.app\n"
    "💬 Escríbeme para la contraseña: @alexworksout\n\n"
    "🇬🇧 English Group: @signalsaicrypto"
)

CTA_EN = (
    "\n\n"
    "🤖 Try our automated trading bots: https://atomated-trade-zen.lovable.app\n"
    "💬 Text me for the password: @alexworksout\n\n"
    "🇪🇸 Grupo en Español: @cryptosignalapp"
)

# Daily promo — DISABLED
PROMO_ES = ""
PROMO_EN = ""
DAILY_PROMO_ENABLED = False

# Telegram message limit
TG_MSG_LIMIT = 4096
TG_SAFE_LIMIT = 3900

# Daily promo hour (UTC) — kept for import compatibility, scheduler is disabled
PROMO_HOUR_UTC = 10
