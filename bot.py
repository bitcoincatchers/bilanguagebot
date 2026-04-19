"""
Dual-Language Crypto Telegram Bot v1.2
--------------------------------------
Flow:
  1. You forward/paste a message to the bot (EN or ES source)
  2. Bot uses Claude to rewrite it in BOTH English and Spanish
  3. Shows side-by-side preview with buttons
  4. On approve -> sends to both channels simultaneously
  5. Daily promo sent once per day (no footer on every message)
"""
import asyncio
import datetime
import logging
import re
import uuid
from io import BytesIO
from typing import Optional
import requests
from anthropic import Anthropic
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
)
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
from config import *
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)
class DualLangBot:
    """Telegram bot that translates and publishes to EN + ES channels."""
    def __init__(self):
        self.anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.pending: dict = {}
        self.preview_msgs: dict = {}
    # --- REWRITE ---
    def _rewrite(self, text: str) -> dict:
        prompt = f"""You MUST produce TWO versions of the message below — English and Spanish.

CRITICAL RULES:
1. Keep it SHORT and proportional to the input. If the input is 1-2 lines, output 3-5 lines MAX per language. Do NOT write essays from short inputs.
2. Lightly reword the message — same meaning, same tone, same structure. Just clean it up. Do NOT invent new content, metaphors, or dramatic narratives.
3. If the input is just a ticker + percentage (e.g. "SOL +33%"), write a brief 2-3 line update. Example:
   "💥 SOL just pumped +33% today!
   Keep watching volume and key levels 👀"
   That's it. No novels.
4. Keep ALL numbers, prices, levels, percentages, tickers EXACTLY as given.
5. The Spanish version must sound native, not translated. But still SHORT.
6. Use a few emojis but don't overdo it.
7. Keep crypto jargon in English in both versions (bullish, bearish, ATH, RSI, etc.)
8. NEVER use markdown like **bold** or *italic*. Use CAPS or emojis for emphasis.
9. Do NOT add links, CTAs, promotional content, philosophical questions, dramatic intros, or motivational speeches.

LENGTH GUIDE:
- Input 1-5 words → 2-4 lines per language
- Input 1-2 sentences → 3-6 lines per language
- Input a paragraph → similar length per language
- Input multi-section → keep sections, reword concisely

OUTPUT FORMAT — Use this exact format:
===EN===
[English version]
===ES===
[Spanish version — ALL IN SPANISH]

Original message:
{text}"""
        try:
            resp = self.anthropic.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            logger.info(f"Claude response length: {len(raw)} chars")
        except Exception as e:
            logger.error(f"Claude rewrite failed: {e}")
            return {"en": text, "es": text}
        en_text = text
        es_text = text
        if "===EN===" in raw and "===ES===" in raw:
            parts = raw.split("===ES===")
            en_part = parts[0].replace("===EN===", "").strip()
            es_part = parts[1].strip() if len(parts) > 1 else text
            en_text = en_part
            es_text = es_part
        else:
            logger.warning("Claude output didn't follow format, using raw as both")
            en_text = raw
            es_text = raw
        for label in ["English:", "Spanish:", "EN:", "ES:", "```"]:
            en_text = en_text.replace(label, "").strip()
            es_text = es_text.replace(label, "").strip()
        logger.info(f"EN preview (first 100): {en_text[:100]}")
        logger.info(f"ES preview (first 100): {es_text[:100]}")
        return {"en": en_text, "es": es_text}
    def _translate_direct(self, text: str) -> dict:
        prompt = f"""Translate the message below into both English and Spanish.
RULES:
1. If the original is in English, translate to Spanish. If in Spanish, translate to English. If mixed, provide both clean versions.
2. Keep ALL numbers, prices, ticker symbols, and crypto jargon exactly as-is.
3. The translation should be natural and fluent, not robotic.
4. Do NOT add anything — no links, CTAs, extra commentary, or emojis that weren't in the original.
5. Do NOT use markdown formatting. Keep it plain text.
OUTPUT FORMAT (strict):
===EN===
[English version]
===ES===
[Spanish version]
Original message:
{text}"""
        try:
            resp = self.anthropic.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {"en": text, "es": text}
        en_text = text
        es_text = text
        if "===EN===" in raw and "===ES===" in raw:
            parts = raw.split("===ES===")
            en_part = parts[0].replace("===EN===", "").strip()
            es_part = parts[1].strip() if len(parts) > 1 else text
            en_text = en_part
            es_text = es_part
        else:
            en_text = raw
            es_text = raw
        for label in ["English:", "Spanish:", "EN:", "ES:", "```"]:
            en_text = en_text.replace(label, "").strip()
            es_text = es_text.replace(label, "").strip()
        return {"en": en_text, "es": es_text}
    # --- MESSAGE SPLITTING ---
    def _split_safe(self, text: str, limit: int = 4000) -> list[str]:
        if len(text) <= limit:
            return [text]
        chunks = []
        remaining = text
        while remaining:
            if len(remaining) <= limit:
                chunks.append(remaining)
                break
            cut_at = remaining.rfind("\n\n", 0, limit)
            if cut_at > limit * 0.3:
                chunks.append(remaining[:cut_at].rstrip())
                remaining = remaining[cut_at:].lstrip("\n")
                continue
            cut_at = remaining.rfind("\n", 0, limit)
            if cut_at > limit * 0.3:
                chunks.append(remaining[:cut_at].rstrip())
                remaining = remaining[cut_at:].lstrip("\n")
                continue
            cut_at = remaining.rfind(". ", 0, limit)
            if cut_at > limit * 0.3:
                chunks.append(remaining[: cut_at + 1])
                remaining = remaining[cut_at + 2 :].lstrip()
                continue
            chunks.append(remaining[:limit])
            remaining = remaining[limit:]
        return [c for c in chunks if c.strip()]
    # --- SEND TO CHANNEL (no footer) ---
    async def _send_to_channel(self, bot, channel_id: str, text: str,
                                photo_url: Optional[str] = None):
        clean_text = self._remove_external_links(text)
        if photo_url:
            try:
                resp = requests.get(photo_url, timeout=30)
                await bot.send_photo(chat_id=channel_id, photo=BytesIO(resp.content))
            except Exception as e:
                logger.warning(f"Photo send failed for {channel_id}: {e}")
        chunks = self._split_safe(clean_text)
        if not chunks:
            chunks = ["📊"]
        for chunk in chunks:
            await bot.send_message(
                chat_id=channel_id, text=chunk,
                disable_web_page_preview=True
            )
    def _remove_external_links(self, text: str) -> str:
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    # --- DAILY PROMO ---
    async def _send_daily_promo(self, context: ContextTypes.DEFAULT_TYPE):
        """Send promo message to both channels once per day."""
        bot = context.bot
        try:
            await bot.send_message(
                chat_id=CHANNEL_ES, text=PROMO_ES,
                disable_web_page_preview=True
            )
            await bot.send_message(
                chat_id=CHANNEL_EN, text=PROMO_EN,
                disable_web_page_preview=True
            )
            logger.info("✅ Daily promo sent to both channels")
        except Exception as e:
            logger.error(f"❌ Daily promo failed: {e}")
    # --- PREVIEW CLEANUP ---
    def _record_preview(self, user_id: int, chat_id: int, msg_id: int):
        self.preview_msgs.setdefault(user_id, []).append((chat_id, msg_id))
    async def _cleanup_previews(self, bot, user_id: int):
        msgs = self.preview_msgs.pop(user_id, [])
        for chat_id, msg_id in msgs:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass
    # --- HANDLERS ---
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 *Dual-Language Crypto Bot*\n\n"
            "Forward or paste any crypto message and I'll:\n"
            "1️⃣ Rewrite it in English + Spanish\n"
            "2️⃣ Show you a preview\n"
            "3️⃣ Send to both channels on your approval\n\n"
            f"🇪🇸 → {CHANNEL_ES}\n"
            f"🇬🇧 → {CHANNEL_EN}",
            parse_mode=ParseMode.MARKDOWN
        )
    async def cmd_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"Current channels:\n"
            f"🇪🇸 Spanish: {CHANNEL_ES}\n"
            f"🇬🇧 English: {CHANNEL_EN}"
        )
    async def cmd_promo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manually trigger the daily promo."""
        user_id = update.effective_user.id
        if ALLOWED_USER_ID != 0 and user_id != ALLOWED_USER_ID:
            return
        await self._send_daily_promo(context)
        await update.message.reply_text("✅ Promo sent to both channels!")
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if update.effective_chat.type != "private":
            return
        if ALLOWED_USER_ID != 0 and user_id != ALLOWED_USER_ID:
            await update.message.reply_text("❌ No tienes permisos / Not authorized")
            return
        text = update.message.text or ""
        is_forwarded = bool(getattr(update.message, 'forward_origin', None))
        if is_forwarded and not text:
            text = update.message.caption or ""
        if not text.strip():
            await update.message.reply_text("Send me a text message to rewrite and publish.")
            return
        photo_url = None
        if is_forwarded and update.message.photo:
            photo = update.message.photo[-1]
            file = await photo.get_file()
            photo_url = file.file_path
        status = await update.message.reply_text("🔄 Rewriting in EN + ES...")
        try:
            result = self._rewrite(text)
            en_text = result["en"]
            es_text = result["es"]
        except Exception as e:
            await status.edit_text(f"❌ Error: {e}")
            return
        session_id = str(uuid.uuid4())[:8]
        self.pending[user_id] = {
            "session_id": session_id,
            "original": text,
            "en": en_text,
            "es": es_text,
            "photo_url": photo_url,
        }
        await self._show_preview(update, status, user_id, session_id)
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if update.effective_chat.type != "private":
            return
        if ALLOWED_USER_ID != 0 and user_id != ALLOWED_USER_ID:
            return
        caption = update.message.caption or ""
        if not caption.strip():
            await update.message.reply_text("Send a photo with a caption/text to rewrite.")
            return
        photo = update.message.photo[-1]
        file = await photo.get_file()
        photo_url = file.file_path
        status = await update.message.reply_text("🔄 Rewriting in EN + ES...")
        try:
            result = self._rewrite(caption)
        except Exception as e:
            await status.edit_text(f"❌ Error: {e}")
            return
        session_id = str(uuid.uuid4())[:8]
        self.pending[user_id] = {
            "session_id": session_id,
            "original": caption,
            "en": result["en"],
            "es": result["es"],
            "photo_url": photo_url,
        }
        await self._show_preview(update, status, user_id, session_id)
    async def _show_preview(self, update: Update, status_msg, user_id: int, session_id: str):
        pending = self.pending[user_id]
        chat_id = update.effective_chat.id
        await self._cleanup_previews(update.get_bot(), user_id)
        en_text = pending["en"]
        es_text = pending["es"]
        has_photo = bool(pending.get("photo_url"))
        photo_note = "📸 Photo attached" if has_photo else "📝 Text only"
        sep = "─" * 30
        en_preview = f"🇬🇧 *ENGLISH PREVIEW*\n{sep}\n\n{en_text}"
        if len(en_preview) > TG_SAFE_LIMIT:
            en_preview = en_preview[:TG_SAFE_LIMIT] + "\n[...truncated in preview]"
        es_preview = f"🇪🇸 *SPANISH PREVIEW*\n{sep}\n\n{es_text}"
        if len(es_preview) > TG_SAFE_LIMIT:
            es_preview = es_preview[:TG_SAFE_LIMIT] + "\n[...truncated in preview]"
        keyboard = [
            [
                InlineKeyboardButton("✅ Send Both", callback_data=f"send_both|{session_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel|{session_id}"),
            ],
            [
                InlineKeyboardButton("🇬🇧 EN Only", callback_data=f"send_en|{session_id}"),
                InlineKeyboardButton("🇪🇸 ES Only", callback_data=f"send_es|{session_id}"),
            ],
            [
                InlineKeyboardButton("🔄 Regenerate", callback_data=f"regen|{session_id}"),
                InlineKeyboardButton("✏️ Edit EN", callback_data=f"edit_en|{session_id}"),
                InlineKeyboardButton("✏️ Edit ES", callback_data=f"edit_es|{session_id}"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        header = f"{photo_note}\n\n"
        first_msg = header + en_preview
        if len(first_msg) > TG_SAFE_LIMIT:
            first_msg = first_msg[:TG_SAFE_LIMIT]
        await status_msg.edit_text(first_msg, reply_markup=reply_markup)
        self._record_preview(user_id, chat_id, status_msg.message_id)
        try:
            sent = await update.get_bot().send_message(chat_id=chat_id, text=es_preview)
            self._record_preview(user_id, chat_id, sent.message_id)
        except Exception as e:
            logger.error(f"Failed to send ES preview: {e}")
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        if ALLOWED_USER_ID != 0 and user_id != ALLOWED_USER_ID:
            await query.answer("❌ Not authorized", show_alert=True)
            return
        await query.answer()
        data = query.data
        action, session_id = data.split("|", 1) if "|" in data else (data, "")
        pending = self.pending.get(user_id)
        if not pending or pending.get("session_id") != session_id:
            await query.edit_message_text("⛔ Expired session. Send a new message.")
            return
        bot = query.get_bot()
        if action == "send_both":
            await query.edit_message_text("📤 Sending to both channels...")
            try:
                await self._send_to_channel(
                    bot, CHANNEL_EN, pending["en"],
                    pending.get("photo_url")
                )
                await self._send_to_channel(
                    bot, CHANNEL_ES, pending["es"],
                    pending.get("photo_url")
                )
                await self._cleanup_previews(bot, user_id)
                await query.edit_message_text(
                    f"✅ Sent to both channels!\n\n"
                    f"🇬🇧 {CHANNEL_EN}\n"
                    f"🇪🇸 {CHANNEL_ES}"
                )
            except Exception as e:
                await query.edit_message_text(f"❌ Error sending: {e}")
            self.pending.pop(user_id, None)
        elif action == "send_en":
            await query.edit_message_text("📤 Sending to English channel...")
            try:
                await self._send_to_channel(
                    bot, CHANNEL_EN, pending["en"],
                    pending.get("photo_url")
                )
                await self._cleanup_previews(bot, user_id)
                await query.edit_message_text(f"✅ Sent to {CHANNEL_EN}")
            except Exception as e:
                await query.edit_message_text(f"❌ Error: {e}")
            self.pending.pop(user_id, None)
        elif action == "send_es":
            await query.edit_message_text("📤 Sending to Spanish channel...")
            try:
                await self._send_to_channel(
                    bot, CHANNEL_ES, pending["es"],
                    pending.get("photo_url")
                )
                await self._cleanup_previews(bot, user_id)
                await query.edit_message_text(f"✅ Sent to {CHANNEL_ES}")
            except Exception as e:
                await query.edit_message_text(f"❌ Error: {e}")
            self.pending.pop(user_id, None)
        elif action == "cancel":
            await self._cleanup_previews(bot, user_id)
            await query.edit_message_text("❌ Cancelled")
            self.pending.pop(user_id, None)
        elif action == "regen":
            await query.edit_message_text("🔄 Regenerating...")
            try:
                result = self._rewrite(pending["original"])
                pending["en"] = result["en"]
                pending["es"] = result["es"]
                new_session = str(uuid.uuid4())[:8]
                pending["session_id"] = new_session
                sep = "─" * 30
                en_preview = f"🇬🇧 *ENGLISH PREVIEW* (regenerated)\n{sep}\n\n{pending['en']}"
                es_preview = f"🇪🇸 *SPANISH PREVIEW* (regenerated)\n{sep}\n\n{pending['es']}"
                if len(en_preview) > TG_SAFE_LIMIT:
                    en_preview = en_preview[:TG_SAFE_LIMIT]
                if len(es_preview) > TG_SAFE_LIMIT:
                    es_preview = es_preview[:TG_SAFE_LIMIT]
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Send Both", callback_data=f"send_both|{new_session}"),
                        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel|{new_session}"),
                    ],
                    [
                        InlineKeyboardButton("🇬🇧 EN Only", callback_data=f"send_en|{new_session}"),
                        InlineKeyboardButton("🇪🇸 ES Only", callback_data=f"send_es|{new_session}"),
                    ],
                    [
                        InlineKeyboardButton("🔄 Regenerate", callback_data=f"regen|{new_session}"),
                        InlineKeyboardButton("✏️ Edit EN", callback_data=f"edit_en|{new_session}"),
                        InlineKeyboardButton("✏️ Edit ES", callback_data=f"edit_es|{new_session}"),
                    ],
                ]
                await query.edit_message_text(en_preview, reply_markup=InlineKeyboardMarkup(keyboard))
                chat_id = query.message.chat.id
                sent = await bot.send_message(chat_id=chat_id, text=es_preview)
                self._record_preview(user_id, chat_id, sent.message_id)
            except Exception as e:
                await query.edit_message_text(f"❌ Regeneration failed: {e}")
        elif action == "edit_en":
            pending["editing"] = "en"
            await query.edit_message_text(
                "✏️ Send me the corrected *English* text.\n"
                "I'll replace the EN version and show you a new preview.",
                parse_mode=ParseMode.MARKDOWN
            )
        elif action == "edit_es":
            pending["editing"] = "es"
            await query.edit_message_text(
                "✏️ Send me the corrected *Spanish* text.\n"
                "I'll replace the ES version and show you a new preview.",
                parse_mode=ParseMode.MARKDOWN
            )
    async def handle_edit_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        pending = self.pending.get(user_id)
        if not pending or "editing" not in pending:
            await self.handle_message(update, context)
            return
        lang = pending.pop("editing")
        new_text = update.message.text.strip()
        pending[lang] = new_text
        new_session = str(uuid.uuid4())[:8]
        pending["session_id"] = new_session
        status = await update.message.reply_text(f"✅ {lang.upper()} updated. Refreshing preview...")
        await self._show_preview(update, status, user_id, new_session)
    # --- RUN ---
    def run(self):
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("channels", self.cmd_channels))
        app.add_handler(CommandHandler("promo", self.cmd_promo))
        app.add_handler(CallbackQueryHandler(self.button_callback))
        app.add_handler(MessageHandler(
            filters.PHOTO & filters.ChatType.PRIVATE,
            self.handle_photo
        ))
        async def _text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            pending = self.pending.get(user_id)
            if pending and "editing" in pending:
                await self.handle_edit_response(update, context)
            else:
                await self.handle_message(update, context)
        app.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
            _text_router
        ))
        app.add_handler(MessageHandler(
            filters.FORWARDED & filters.ChatType.PRIVATE,
            self.handle_message
        ))
        # Schedule daily promo
        promo_time = datetime.time(hour=PROMO_HOUR_UTC, minute=0, tzinfo=datetime.timezone.utc)
        # DISABLED: app.job_queue.run_daily(self._send_daily_promo, time=promo_time)
        logger.info(f"🤖 Dual-Lang Bot started")
        logger.info(f"🇪🇸 ES channel: {CHANNEL_ES}")
        logger.info(f"🇬🇧 EN channel: {CHANNEL_EN}")
        logger.info(f"👤 Allowed user: {ALLOWED_USER_ID}")
        logger.info(f"📢 Daily promo scheduled at {PROMO_HOUR_UTC}:00 UTC")
        app.run_polling(drop_pending_updates=True)
if __name__ == "__main__":
    bot = DualLangBot()
    bot.run()
