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

# Daily promo message (sent once per day, NOT on every message)
PROMO_ES = (
    "🎁 1000$ GRATIS con BITMART: https://crypto-signals.app/bitmart-bonus\n"
    "💸 300$ GRATIS con BINGX: https://crypto-signals.app/bingx-bonus\n"
    "🤖 Señales con IA: crypto-signals.app\n\n"
    "🇬🇧 English Group: @signalsaicrypto"
)

PROMO_EN = (
    "🎁 $1000 FREE with BITMART: https://crypto-signals.app/bitmart-bonus\n"
    "💸 $300 FREE with BINGX: https://crypto-signals.app/bingx-bonus\n"
    "🤖 AI Trading Signals: crypto-signals.app\n\n"
    "🇪🇸 Grupo en Español: @cryptosignalapp"
)

# Hour (UTC) to send daily promo. Madrid is UTC+2, so 10 UTC = 12pm Madrid
PROMO_HOUR_UTC = int(os.getenv('PROMO_HOUR_UTC', '10'))

# Telegram message limit
TG_MSG_LIMIT = 4096
TG_SAFE_LIMIT = 3900
