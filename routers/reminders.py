from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timedelta
from bson import ObjectId

from models.models import Reminder, ReminderCreate, ReminderResponse, User
from database.connection import get_database
from routers.auth import get_current_user

router = APIRouter(prefix="/reminders", tags=["reminders"])

@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Crear un nuevo recordatorio para un evento de Google Calendar
    """
    # Calculate reminder time
    reminder_time = reminder_data.event_start - timedelta(minutes=reminder_data.minutes_before)

    # Create reminder document
    reminder = Reminder(
        user_id=current_user.id,
        event_id=reminder_data.event_id,
        event_title=reminder_data.event_title,
        event_start=reminder_data.event_start,
        reminder_time=reminder_time,
        minutes_before=reminder_data.minutes_before,
        sent=False
    )

    # Insert into database
    result = await db["reminders"].insert_one(reminder.model_dump(by_alias=True, exclude=["id"]))

    # Get the created reminder
    created_reminder = await db["reminders"].find_one({"_id": result.inserted_id})

    return ReminderResponse(
        id=str(created_reminder["_id"]),
        event_id=created_reminder["event_id"],
        event_title=created_reminder["event_title"],
        event_start=created_reminder["event_start"],
        reminder_time=created_reminder["reminder_time"],
        minutes_before=created_reminder["minutes_before"],
        sent=created_reminder["sent"],
        created_at=created_reminder["created_at"]
    )

@router.get("/", response_model=List[ReminderResponse])
async def get_reminders(
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Obtener todos los recordatorios del usuario actual
    """
    reminders_cursor = db["reminders"].find({"user_id": current_user.id})
    reminders = await reminders_cursor.to_list(length=None)

    return [
        ReminderResponse(
            id=str(reminder["_id"]),
            event_id=reminder["event_id"],
            event_title=reminder["event_title"],
            event_start=reminder["event_start"],
            reminder_time=reminder["reminder_time"],
            minutes_before=reminder["minutes_before"],
            sent=reminder["sent"],
            created_at=reminder["created_at"]
        )
        for reminder in reminders
    ]

@router.get("/event/{event_id}", response_model=ReminderResponse)
async def get_reminder_by_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Obtener el recordatorio de un evento específico
    """
    reminder = await db["reminders"].find_one({
        "event_id": event_id,
        "user_id": current_user.id
    })

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )

    return ReminderResponse(
        id=str(reminder["_id"]),
        event_id=reminder["event_id"],
        event_title=reminder["event_title"],
        event_start=reminder["event_start"],
        reminder_time=reminder["reminder_time"],
        minutes_before=reminder["minutes_before"],
        sent=reminder["sent"],
        created_at=reminder["created_at"]
    )

@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Eliminar un recordatorio
    """
    if not ObjectId.is_valid(reminder_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de recordatorio inválido"
        )

    result = await db["reminders"].delete_one({
        "_id": ObjectId(reminder_id),
        "user_id": current_user.id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )

@router.delete("/event/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder_by_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Eliminar el recordatorio de un evento específico
    """
    result = await db["reminders"].delete_one({
        "event_id": event_id,
        "user_id": current_user.id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )

@router.put("/event/{event_id}", response_model=ReminderResponse)
async def update_reminder(
    event_id: str,
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Actualizar un recordatorio existente
    """
    # Calculate new reminder time
    reminder_time = reminder_data.event_start - timedelta(minutes=reminder_data.minutes_before)

    # Update reminder
    result = await db["reminders"].update_one(
        {"event_id": event_id, "user_id": current_user.id},
        {
            "$set": {
                "event_title": reminder_data.event_title,
                "event_start": reminder_data.event_start,
                "reminder_time": reminder_time,
                "minutes_before": reminder_data.minutes_before,
                "sent": False  # Reset sent status when updating
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )

    # Get updated reminder
    updated_reminder = await db["reminders"].find_one({
        "event_id": event_id,
        "user_id": current_user.id
    })

    return ReminderResponse(
        id=str(updated_reminder["_id"]),
        event_id=updated_reminder["event_id"],
        event_title=updated_reminder["event_title"],
        event_start=updated_reminder["event_start"],
        reminder_time=updated_reminder["reminder_time"],
        minutes_before=updated_reminder["minutes_before"],
        sent=updated_reminder["sent"],
        created_at=updated_reminder["created_at"]
    )
