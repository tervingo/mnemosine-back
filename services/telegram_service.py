import os
import requests
from datetime import datetime
from typing import Optional

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token:
            print("⚠️ WARNING: TELEGRAM_BOT_TOKEN not found in environment variables")
        if not self.chat_id:
            print("⚠️ WARNING: TELEGRAM_CHAT_ID not found in environment variables")

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        print(f"📱 TelegramService initialized with chat_id: {self.chat_id}")

    def send_message(self, message: str) -> bool:
        """
        Envía un mensaje a través del bot de Telegram
        """
        try:
            if not self.bot_token or not self.chat_id:
                print("❌ Cannot send message: Missing bot token or chat ID")
                return False

            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }

            print(f"📤 Sending Telegram message to chat_id {self.chat_id}")
            print(f"Message preview: {message[:100]}...")

            response = requests.post(url, json=data)

            print(f"📥 Telegram API response status: {response.status_code}")
            print(f"Response content: {response.text}")

            response.raise_for_status()

            result = response.json().get("ok", False)
            print(f"✅ Message sent successfully: {result}")
            return result

        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False

    def send_event_reminder(
        self,
        event_title: str,
        event_start: datetime,
        minutes_before: int,
        event_location: Optional[str] = None
    ) -> bool:
        """
        Envía un recordatorio de evento formateado
        """
        try:
            print(f"🔔 Preparing reminder for: {event_title}")
            print(f"   event_start type: {type(event_start)}, value: {event_start}")
            print(f"   minutes_before: {minutes_before}")

            # Format the datetime
            formatted_time = event_start.strftime("%d/%m/%Y %H:%M")
            print(f"   formatted_time: {formatted_time}")

            # Build the message
            message = f"🔔 <b>Recordatorio de Evento</b>\n\n"
            message += f"📅 <b>{event_title}</b>\n"
            message += f"🕐 {formatted_time}"

            if event_location:
                message += f"\n📍 {event_location}"

            if minutes_before > 0:
                if minutes_before >= 60:
                    hours = minutes_before // 60
                    remaining_minutes = minutes_before % 60
                    if remaining_minutes > 0:
                        message += f"\n\n⏰ El evento comienza en {hours}h {remaining_minutes}min"
                    else:
                        message += f"\n\n⏰ El evento comienza en {hours}h"
                else:
                    message += f"\n\n⏰ El evento comienza en {minutes_before} minutos"
            else:
                message += "\n\n⏰ El evento está comenzando ahora"

            print(f"📝 Full message prepared, length: {len(message)} chars")
            return self.send_message(message)

        except Exception as e:
            print(f"❌ Error in send_event_reminder: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False

    def send_internal_reminder(
        self,
        title: str,
        reminder_datetime: datetime,
        minutes_before: int,
        description: Optional[str] = None
    ) -> bool:
        """
        Envía un recordatorio interno formateado
        """
        try:
            print(f"🔔 Preparing internal reminder for: {title}")
            print(f"   reminder_datetime type: {type(reminder_datetime)}, value: {reminder_datetime}")
            print(f"   minutes_before: {minutes_before}")

            # Format the datetime
            formatted_time = reminder_datetime.strftime("%d/%m/%Y %H:%M")
            print(f"   formatted_time: {formatted_time}")

            # Build the message
            message = f"⏰ <b>Recordatorio</b>\n\n"
            message += f"📋 <b>{title}</b>\n"
            message += f"🕐 {formatted_time}"

            if description:
                message += f"\n📝 {description}"

            if minutes_before > 0:
                if minutes_before >= 60:
                    hours = minutes_before // 60
                    remaining_minutes = minutes_before % 60
                    if remaining_minutes > 0:
                        message += f"\n\n⏳ Tiempo restante: {hours}h {remaining_minutes}min"
                    else:
                        message += f"\n\n⏳ Tiempo restante: {hours}h"
                else:
                    message += f"\n\n⏳ Tiempo restante: {minutes_before} minutos"
            else:
                message += "\n\n⏳ ¡Es ahora!"

            print(f"📝 Full message prepared, length: {len(message)} chars")
            return self.send_message(message)

        except Exception as e:
            print(f"❌ Error in send_internal_reminder: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False

# Singleton instance
telegram_service = TelegramService()
