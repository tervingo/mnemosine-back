from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from routers import armarios, cajas, cajitas, notas, auth, reminders, internal_reminders
from database.connection import connect_to_mongo, close_mongo_connection

load_dotenv()

app = FastAPI(
    title="Mnemosyne API",
    description="API para gestión de notas organizadas jerárquicamente",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://mymir.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(armarios.router, prefix="/api/armarios", tags=["armarios"])
app.include_router(cajas.router, prefix="/api/cajas", tags=["cajas"])
app.include_router(cajitas.router, prefix="/api/cajitas", tags=["cajitas"])
app.include_router(notas.router, prefix="/api/notas", tags=["notas"])
app.include_router(reminders.router, prefix="/api", tags=["reminders"])
app.include_router(internal_reminders.router, prefix="/api", tags=["internal-reminders"])
# app.include_router(cron.router, prefix="/api/cron", tags=["cron"])  # Endpoint movido directamente a main.py

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Mnemosyne API v1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/cron/check-reminders")
async def check_reminders_endpoint():
    """
    Endpoint para cron job - verifica y envía recordatorios pendientes (eventos de Google Calendar y recordatorios internos)
    """
    from datetime import datetime
    from database.connection import get_database
    from services.telegram_service import telegram_service

    try:
        db = await get_database()
        current_time = datetime.utcnow()

        total_sent = 0
        total_failed = 0
        event_reminders_checked = 0
        internal_reminders_checked = 0

        # ===== PROCESS EVENT REMINDERS (Google Calendar) =====
        event_reminders_cursor = db["reminders"].find({
            "sent": False,
            "reminder_time": {"$lte": current_time}
        })

        event_reminders = await event_reminders_cursor.to_list(length=None)
        event_reminders_checked = len(event_reminders)

        for reminder in event_reminders:
            try:
                # Ensure event_start is a datetime object
                event_start = reminder["event_start"]
                if isinstance(event_start, str):
                    from dateutil import parser
                    event_start = parser.parse(event_start)

                print(f"🔍 Processing event reminder: {reminder['event_title']}, event_start type: {type(event_start)}, value: {event_start}")

                # Send Telegram message
                success = telegram_service.send_event_reminder(
                    event_title=reminder["event_title"],
                    event_start=event_start,
                    minutes_before=reminder["minutes_before"],
                    event_location=reminder.get("event_location")
                )

                if success:
                    # Mark as sent
                    await db["reminders"].update_one(
                        {"_id": reminder["_id"]},
                        {"$set": {"sent": True}}
                    )
                    total_sent += 1
                    print(f"✅ Event reminder sent: {reminder['event_title']}")
                else:
                    total_failed += 1
                    print(f"❌ Failed to send event reminder: {reminder['event_title']}")

            except Exception as e:
                total_failed += 1
                print(f"❌ Error sending event reminder {reminder['event_title']}: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")

        # ===== PROCESS INTERNAL REMINDERS =====
        internal_reminders_cursor = db["internal_reminders"].find({
            "sent": False,
            "reminder_time": {"$lte": current_time}
        })

        internal_reminders = await internal_reminders_cursor.to_list(length=None)
        internal_reminders_checked = len(internal_reminders)

        for reminder in internal_reminders:
            try:
                # Ensure reminder_datetime is a datetime object
                reminder_datetime = reminder["reminder_datetime"]
                if isinstance(reminder_datetime, str):
                    from dateutil import parser
                    reminder_datetime = parser.parse(reminder_datetime)

                print(f"🔍 Processing internal reminder: {reminder['title']}, reminder_datetime type: {type(reminder_datetime)}, value: {reminder_datetime}")

                # Send Telegram message for internal reminder
                success = telegram_service.send_internal_reminder(
                    title=reminder["title"],
                    reminder_datetime=reminder_datetime,
                    minutes_before=reminder["minutes_before"],
                    description=reminder.get("description")
                )

                if success:
                    # Check if this is a recurring reminder
                    if reminder.get("is_recurring", False) and reminder.get("recurrence_type"):
                        # Calculate next occurrence
                        from dateutil.relativedelta import relativedelta

                        current_datetime = reminder["reminder_datetime"]
                        recurrence_type = reminder["recurrence_type"]
                        recurrence_end_date = reminder.get("recurrence_end_date")

                        # Calculate next datetime based on recurrence type
                        if recurrence_type == "daily":
                            next_datetime = current_datetime + relativedelta(days=1)
                        elif recurrence_type == "weekly":
                            next_datetime = current_datetime + relativedelta(weeks=1)
                        elif recurrence_type == "monthly":
                            next_datetime = current_datetime + relativedelta(months=1)
                        elif recurrence_type == "yearly":
                            next_datetime = current_datetime + relativedelta(years=1)
                        else:
                            next_datetime = None

                        # Only create next occurrence if it's before the end date (if specified)
                        should_create_next = next_datetime is not None
                        if recurrence_end_date and next_datetime:
                            should_create_next = next_datetime <= recurrence_end_date

                        if should_create_next:
                            # Calculate next reminder time
                            from datetime import timedelta
                            next_reminder_time = next_datetime - timedelta(minutes=reminder["minutes_before"])

                            # Update current reminder to next occurrence
                            await db["internal_reminders"].update_one(
                                {"_id": reminder["_id"]},
                                {"$set": {
                                    "reminder_datetime": next_datetime,
                                    "reminder_time": next_reminder_time,
                                    "sent": False,
                                    "completed": False
                                }}
                            )
                            print(f"🔄 Recurring reminder updated to next occurrence: {next_datetime}")
                        else:
                            # Recurrence ended, mark as sent and completed
                            await db["internal_reminders"].update_one(
                                {"_id": reminder["_id"]},
                                {"$set": {"sent": True, "completed": True}}
                            )
                            print(f"🏁 Recurring reminder ended: {reminder['title']}")
                    else:
                        # Non-recurring reminder, just mark as sent
                        await db["internal_reminders"].update_one(
                            {"_id": reminder["_id"]},
                            {"$set": {"sent": True}}
                        )

                    total_sent += 1
                    print(f"✅ Internal reminder sent: {reminder['title']}")
                else:
                    total_failed += 1
                    print(f"❌ Failed to send internal reminder: {reminder['title']}")

            except Exception as e:
                total_failed += 1
                print(f"❌ Error sending internal reminder {reminder['title']}: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")

        return {
            "status": "success",
            "checked_at": current_time.isoformat(),
            "reminders_sent": total_sent,
            "reminders_failed": total_failed,
            "event_reminders_checked": event_reminders_checked,
            "internal_reminders_checked": internal_reminders_checked,
            "total_checked": event_reminders_checked + internal_reminders_checked
        }

    except Exception as e:
        print(f"❌ Error in cron job: {e}")
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)