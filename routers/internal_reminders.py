from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timedelta
from bson import ObjectId

from models.models import InternalReminder, InternalReminderCreate, InternalReminderUpdate, InternalReminderResponse, User
from database.connection import get_database
from routers.auth import get_current_user

router = APIRouter(prefix="/internal-reminders", tags=["internal-reminders"])

@router.post("/", response_model=InternalReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_internal_reminder(
    reminder_data: InternalReminderCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Crear un nuevo recordatorio interno
    """
    # Calculate reminder time
    reminder_time = reminder_data.reminder_datetime - timedelta(minutes=reminder_data.minutes_before)

    # Create reminder document
    reminder = InternalReminder(
        user_id=current_user.id,
        title=reminder_data.title,
        reminder_datetime=reminder_data.reminder_datetime,
        reminder_time=reminder_time,
        minutes_before=reminder_data.minutes_before,
        description=reminder_data.description,
        sent=False
    )

    # Insert into database
    result = await db["internal_reminders"].insert_one(reminder.model_dump(by_alias=True, exclude=["id"]))

    # Get the created reminder
    created_reminder = await db["internal_reminders"].find_one({"_id": result.inserted_id})

    return InternalReminderResponse(
        id=str(created_reminder["_id"]),
        title=created_reminder["title"],
        reminder_datetime=created_reminder["reminder_datetime"],
        reminder_time=created_reminder["reminder_time"],
        minutes_before=created_reminder["minutes_before"],
        description=created_reminder.get("description"),
        sent=created_reminder["sent"],
        completed=created_reminder.get("completed", False),
        created_at=created_reminder["created_at"],
        updated_at=created_reminder["updated_at"]
    )

@router.get("/", response_model=List[InternalReminderResponse])
async def get_internal_reminders(
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Obtener todos los recordatorios internos del usuario actual
    """
    reminders_cursor = db["internal_reminders"].find({
        "user_id": current_user.id
    }).sort("reminder_datetime", 1)  # Sort by date ascending

    reminders = await reminders_cursor.to_list(length=None)

    return [
        InternalReminderResponse(
            id=str(reminder["_id"]),
            title=reminder["title"],
            reminder_datetime=reminder["reminder_datetime"],
            reminder_time=reminder["reminder_time"],
            minutes_before=reminder["minutes_before"],
            description=reminder.get("description"),
            sent=reminder["sent"],
            completed=reminder.get("completed", False),
            created_at=reminder["created_at"],
            updated_at=reminder["updated_at"]
        )
        for reminder in reminders
    ]

@router.get("/{reminder_id}", response_model=InternalReminderResponse)
async def get_internal_reminder(
    reminder_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Obtener un recordatorio interno específico
    """
    if not ObjectId.is_valid(reminder_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de recordatorio inválido"
        )

    reminder = await db["internal_reminders"].find_one({
        "_id": ObjectId(reminder_id),
        "user_id": current_user.id
    })

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )

    return InternalReminderResponse(
        id=str(reminder["_id"]),
        title=reminder["title"],
        reminder_datetime=reminder["reminder_datetime"],
        reminder_time=reminder["reminder_time"],
        minutes_before=reminder["minutes_before"],
        description=reminder.get("description"),
        sent=reminder["sent"],
        completed=reminder.get("completed", False),
        created_at=reminder["created_at"],
        updated_at=reminder["updated_at"]
    )

@router.put("/{reminder_id}", response_model=InternalReminderResponse)
async def update_internal_reminder(
    reminder_id: str,
    reminder_data: InternalReminderUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Actualizar un recordatorio interno existente
    """
    if not ObjectId.is_valid(reminder_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de recordatorio inválido"
        )

    # Calculate new reminder time
    reminder_time = reminder_data.reminder_datetime - timedelta(minutes=reminder_data.minutes_before)

    # Build update dict
    update_dict = {
        "title": reminder_data.title,
        "reminder_datetime": reminder_data.reminder_datetime,
        "reminder_time": reminder_time,
        "minutes_before": reminder_data.minutes_before,
        "description": reminder_data.description,
        "sent": False,  # Reset sent status when updating
        "updated_at": datetime.utcnow()
    }

    # Only update completed if provided
    if reminder_data.completed is not None:
        update_dict["completed"] = reminder_data.completed

    # Update reminder
    result = await db["internal_reminders"].update_one(
        {"_id": ObjectId(reminder_id), "user_id": current_user.id},
        {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )

    # Get updated reminder
    updated_reminder = await db["internal_reminders"].find_one({
        "_id": ObjectId(reminder_id),
        "user_id": current_user.id
    })

    return InternalReminderResponse(
        id=str(updated_reminder["_id"]),
        title=updated_reminder["title"],
        reminder_datetime=updated_reminder["reminder_datetime"],
        reminder_time=updated_reminder["reminder_time"],
        minutes_before=updated_reminder["minutes_before"],
        description=updated_reminder.get("description"),
        sent=updated_reminder["sent"],
        completed=updated_reminder.get("completed", False),
        created_at=updated_reminder["created_at"],
        updated_at=updated_reminder["updated_at"]
    )

@router.patch("/{reminder_id}/toggle-completed", response_model=InternalReminderResponse)
async def toggle_reminder_completed(
    reminder_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Cambiar el estado de completado de un recordatorio interno
    """
    if not ObjectId.is_valid(reminder_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de recordatorio inválido"
        )

    # Get current reminder
    reminder = await db["internal_reminders"].find_one({
        "_id": ObjectId(reminder_id),
        "user_id": current_user.id
    })

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )

    # Toggle completed status
    new_completed = not reminder.get("completed", False)

    # Update reminder
    await db["internal_reminders"].update_one(
        {"_id": ObjectId(reminder_id), "user_id": current_user.id},
        {
            "$set": {
                "completed": new_completed,
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Get updated reminder
    updated_reminder = await db["internal_reminders"].find_one({
        "_id": ObjectId(reminder_id),
        "user_id": current_user.id
    })

    return InternalReminderResponse(
        id=str(updated_reminder["_id"]),
        title=updated_reminder["title"],
        reminder_datetime=updated_reminder["reminder_datetime"],
        reminder_time=updated_reminder["reminder_time"],
        minutes_before=updated_reminder["minutes_before"],
        description=updated_reminder.get("description"),
        sent=updated_reminder["sent"],
        completed=updated_reminder.get("completed", False),
        created_at=updated_reminder["created_at"],
        updated_at=updated_reminder["updated_at"]
    )

@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_internal_reminder(
    reminder_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Eliminar un recordatorio interno
    """
    if not ObjectId.is_valid(reminder_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de recordatorio inválido"
        )

    result = await db["internal_reminders"].delete_one({
        "_id": ObjectId(reminder_id),
        "user_id": current_user.id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )
