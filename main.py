from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from routers import armarios, cajas, cajitas, notas, auth, reminders  # , cron
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

@app.post("/api/test/telegram")
async def test_telegram():
    """
    Endpoint de prueba para verificar que Telegram funciona
    """
    from services.telegram_service import telegram_service
    from datetime import datetime

    success = telegram_service.send_event_reminder(
        event_title="Test de Telegram",
        event_start=datetime.now(),
        minutes_before=0,
        event_location="Test Location"
    )

    return {
        "success": success,
        "bot_token_configured": telegram_service.bot_token is not None,
        "chat_id_configured": telegram_service.chat_id is not None,
        "chat_id": telegram_service.chat_id
    }

@app.post("/api/cron/check-reminders")
async def check_reminders_endpoint():
    """
    Endpoint para cron job - verifica y envía recordatorios pendientes
    """
    from datetime import datetime
    from database.connection import get_database
    from services.telegram_service import telegram_service

    try:
        db = await get_database()
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
                # Ensure event_start is a datetime object
                event_start = reminder["event_start"]
                if isinstance(event_start, str):
                    from dateutil import parser
                    event_start = parser.parse(event_start)

                print(f"🔍 Processing reminder: {reminder['event_title']}, event_start type: {type(event_start)}, value: {event_start}")

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
                    sent_count += 1
                    print(f"✅ Reminder sent for event: {reminder['event_title']}")
                else:
                    failed_count += 1
                    print(f"❌ Failed to send reminder for event: {reminder['event_title']}")

            except Exception as e:
                failed_count += 1
                print(f"❌ Error sending reminder for event {reminder['event_title']}: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)