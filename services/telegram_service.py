import os
import requests
from datetime import datetime
from typing import Optional

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, message: str) -> bool:
        """
        Envía un mensaje a través del bot de Telegram
        """
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }

            response = requests.post(url, json=data)
            response.raise_for_status()

            return response.json().get("ok", False)
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
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
        # Format the datetime
        formatted_time = event_start.strftime("%d/%m/%Y %H:%M")

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

        return self.send_message(message)

# Singleton instance
telegram_service = TelegramService()
