import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from motor.motor_asyncio import AsyncIOMotorClient
import os

from services.telegram_service import telegram_service

class ReminderScheduler:
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db_client = db_client
        self.db = db_client[os.getenv("DATABASE_NAME", "mnemosine")]
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    async def check_and_send_reminders(self):
        """
        Revisa los recordatorios pendientes y envía los que ya deben enviarse
        """
        try:
            current_time = datetime.utcnow()

            # Find reminders that should be sent
            reminders_cursor = self.db["reminders"].find({
                "sent": False,
                "reminder_time": {"$lte": current_time}
            })

            reminders = await reminders_cursor.to_list(length=None)

            for reminder in reminders:
                try:
                    # Send Telegram message
                    success = telegram_service.send_event_reminder(
                        event_title=reminder["event_title"],
                        event_start=reminder["event_start"],
                        minutes_before=reminder["minutes_before"],
                        event_location=reminder.get("event_location")
                    )

                    if success:
                        # Mark as sent
                        await self.db["reminders"].update_one(
                            {"_id": reminder["_id"]},
                            {"$set": {"sent": True}}
                        )
                        print(f"✅ Reminder sent for event: {reminder['event_title']}")
                    else:
                        print(f"❌ Failed to send reminder for event: {reminder['event_title']}")

                except Exception as e:
                    print(f"❌ Error sending reminder for event {reminder['event_title']}: {e}")

        except Exception as e:
            print(f"❌ Error in reminder scheduler: {e}")

    def start(self):
        """
        Inicia el scheduler para revisar recordatorios cada minuto
        """
        if not self.is_running:
            # Check every minute
            self.scheduler.add_job(
                self.check_and_send_reminders,
                trigger=IntervalTrigger(minutes=1),
                id='check_reminders',
                name='Check and send reminders',
                replace_existing=True
            )

            self.scheduler.start()
            self.is_running = True
            print("🔔 Reminder scheduler started - checking every minute")

    def stop(self):
        """
        Detiene el scheduler
        """
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("🔕 Reminder scheduler stopped")

# Global scheduler instance
reminder_scheduler = None

def get_reminder_scheduler():
    return reminder_scheduler

def initialize_scheduler(db_client: AsyncIOMotorClient):
    global reminder_scheduler
    reminder_scheduler = ReminderScheduler(db_client)
    reminder_scheduler.start()
