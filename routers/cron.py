from fastapi import APIRouter, Depends, Header, HTTPException
from datetime import datetime
from database.connection import get_database
from services.telegram_service import telegram_service

router = APIRouter(tags=["cron"])

@router.post("/check-reminders")
async def check_reminders_cron(
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """
    Endpoint para ejecutar como Cron Job en Render.
    Revisa y envía recordatorios pendientes.

    IMPORTANTE: Este endpoint debe ser llamado desde Render Cron Job.
    No requiere autenticación de usuario.
    """

    try:
        current_time = datetime.utcnow()

        # Find reminders that should be sent
        reminders_cursor = db["reminders"].find({
            "sent": False,
            "reminder_time": {"$lte": current_time}
        })

        reminders = await reminders_cursor.to_list(length=None)

        sent_count = 0
        failed_count = 0

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
                    await db["reminders"].update_one(
                        {"_id": reminder["_id"]},
                        {"$set": {"sent": True}}
                    )
                    sent_count += 1
                    print(f"✅ Reminder sent for event: {reminder['event_title']}")
                else:
                    failed_count += 1
                    print(f"❌ Failed to send reminder for event: {reminder['event_title']}")

            except Exception as e:
                failed_count += 1
                print(f"❌ Error sending reminder for event {reminder['event_title']}: {e}")

        return {
            "status": "success",
            "checked_at": current_time.isoformat(),
            "reminders_sent": sent_count,
            "reminders_failed": failed_count,
            "total_checked": len(reminders)
        }

    except Exception as e:
        print(f"❌ Error in cron job: {e}")
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }
