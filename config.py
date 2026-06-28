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
# claude-sonnet-4-20250514 reached end-of-life 2026-06-15 and now returns 404,
# which made the bot silently echo the original text untranslated. Haiku 4.5 is
# cheap + fast and ideal for short-message translation. Bump to claude-sonnet-4-6
# for higher polish. Use the bare alias (no date suffix).
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-haiku-4-5')

# Footer — appended after every translation
CTA_ES = (
    "\n\n"
    "🚀 Prueba Crypto Signals gratis: https://crypto-signals.app\n\n"
    "🇬🇧 English Group: @signalsaicrypto"
)

CTA_EN = (
    "\n\n"
    "🚀 Try Crypto Signals free: https://crypto-signals.app\n\n"
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
