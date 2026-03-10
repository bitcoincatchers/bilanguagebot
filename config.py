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

# CTAs — appended after every message (includes group redirect)
CTA_ES = (
    "\n\n"
    "🤖 Señales con IA: crypto-signals.app\n"
    "🎁 Promoción 1 mes gratis: https://crypto-signals.app/blofin\n"
    "💸 Hasta 250$ GRATIS con BLOFIN: https://partner.blofin.com/d/CryptoUniverse\n\n"
    "🇬🇧 English Group: @signalsaicrypto"
)

CTA_EN = (
    "\n\n"
    "🤖 AI Trading Signals: crypto-signals.app\n"
    "🎁 1 Month FREE promo: https://crypto-signals.app/blofin\n"
    "💸 Up to $250 FREE with BLOFIN: https://partner.blofin.com/d/CryptoUniverse\n\n"
    "🇪🇸 Grupo en Español: @cryptosignalapp"
)

# Telegram message limit
TG_MSG_LIMIT = 4096
TG_SAFE_LIMIT = 3900
