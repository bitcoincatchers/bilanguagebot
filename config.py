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

# Cross-promotion lines (appended at the very end of every message)
CROSS_PROMO_EN = "\n\n🇪🇸 Grupo en Español: @cryptosignalapp"
CROSS_PROMO_ES = "\n\n🇬🇧 English Group: @signalsaicrypto"

# CTAs
CTA_ES = (
    "\n\n"
    "🎁 1000$ GRATIS con BITMART: https://crypto-signals.app/bitmart-bonus\n"
    "💸 300$ GRATIS con BINGX: https://crypto-signals.app/bingx-bonus\n"
    "🤖 Señales con IA: crypto-signals.app"
)

CTA_EN = (
    "\n\n"
    "🎁 $1000 FREE with BITMART: https://crypto-signals.app/bitmart-bonus\n"
    "💸 $300 FREE with BINGX: https://crypto-signals.app/bingx-bonus\n"
    "🤖 AI Trading Signals: crypto-signals.app"
)

# Telegram message limit
TG_MSG_LIMIT = 4096
TG_SAFE_LIMIT = 3900
```

Railway will auto-deploy once you commit. The final message will look like:

**Spanish channel:**
```
[message]

🎁 1000$ GRATIS con BITMART: https://crypto-signals.app/bitmart-bonus
💸 300$ GRATIS con BINGX: https://crypto-signals.app/bingx-bonus
🤖 Señales con IA: crypto-signals.app

🇬🇧 English Group: @signalsaicrypto
```

**English channel:**
```
[message]

🎁 $1000 FREE with BITMART: https://crypto-signals.app/bitmart-bonus
💸 $300 FREE with BINGX: https://crypto-signals.app/bingx-bonus
🤖 AI Trading Signals: crypto-signals.app

🇪🇸 Grupo en Español: @cryptosignalapp
