from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class User(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    email: str
    username: str
    hashed_password: str
    refresh_token: Optional[str] = None  # Token para renovar sesiones
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    created_at: datetime

class Nota(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    titulo: str
    contenido: str  # Markdown
    etiquetas: List[str] = []
    archivos_adjuntos: List[str] = []  # URLs de archivos
    owner_id: ObjectId
    parent_id: Optional[ObjectId] = None  # ID de la caja o cajita padre
    parent_type: str  # "caja" o "cajita"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NotaCreate(BaseModel):
    titulo: str
    contenido: str
    etiquetas: List[str] = []
    parent_id: str
    parent_type: str

class NotaUpdate(BaseModel):
    titulo: Optional[str] = None
    contenido: Optional[str] = None
    etiquetas: Optional[List[str]] = None

class Cajita(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    nombre: str
    descripcion: Optional[str] = None
    owner_id: ObjectId
    caja_id: ObjectId  # ID de la caja padre
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CajitaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    caja_id: str

class CajitaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class Caja(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    nombre: str
    descripcion: Optional[str] = None
    color: Optional[str] = "#6366f1"  # Color por defecto
    owner_id: ObjectId
    armario_id: ObjectId  # ID del armario padre
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CajaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    color: Optional[str] = "#6366f1"
    armario_id: str

class CajaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    color: Optional[str] = None

class Armario(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    nombre: str
    descripcion: Optional[str] = None
    owner_id: ObjectId
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ArmarioCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    is_default: bool = False

class ArmarioUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

# Modelos para respuestas con contenido anidado
class NotaResponse(BaseModel):
    id: str
    titulo: str
    contenido: str
    etiquetas: List[str]
    archivos_adjuntos: List[str]
    parent_id: Optional[str]
    parent_type: str
    created_at: datetime
    updated_at: datetime

class CajitaResponse(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str]
    caja_id: str
    notas: List[NotaResponse] = []
    created_at: datetime
    updated_at: datetime

class CajaResponse(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str]
    color: str
    armario_id: str
    cajitas: List[CajitaResponse] = []
    notas: List[NotaResponse] = []
    created_at: datetime
    updated_at: datetime

class ArmarioResponse(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str]
    is_default: bool
    cajas: List[CajaResponse] = []
    created_at: datetime
    updated_at: datetime

# Event Reminder (vinculado a eventos de Google Calendar)
class EventReminder(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    user_id: ObjectId
    event_id: str  # Google Calendar Event ID
    event_title: str
    event_start: datetime
    reminder_time: datetime  # Calculated from event_start - minutes_before
    minutes_before: int  # Minutes before event to send reminder
    sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EventReminderCreate(BaseModel):
    event_id: str
    event_title: str
    event_start: datetime
    minutes_before: int = 15  # Default 15 minutes

class EventReminderUpdate(BaseModel):
    event_title: str
    event_start: datetime
    minutes_before: int

class EventReminderResponse(BaseModel):
    id: str
    event_id: str
    event_title: str
    event_start: datetime
    reminder_time: datetime
    minutes_before: int
    sent: bool
    created_at: datetime

# Backward compatibility aliases
Reminder = EventReminder
ReminderCreate = EventReminderCreate
ReminderUpdate = EventReminderUpdate
ReminderResponse = EventReminderResponse

# Internal Reminder (recordatorios internos de la app)
class InternalReminder(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    user_id: ObjectId
    title: str
    reminder_datetime: datetime  # Fecha y hora del recordatorio
    reminder_time: datetime  # Hora a la que se enviará el aviso (reminder_datetime - minutes_before)
    minutes_before: int  # Minutos de anticipación para el aviso
    description: Optional[str] = None
    sent: bool = False
    completed: bool = False  # Indica si el recordatorio ha sido marcado como completado
    # Campos de recurrencia
    is_recurring: bool = False  # Indica si es un recordatorio recurrente
    recurrence_type: Optional[str] = None  # 'daily', 'weekly', 'monthly', 'yearly'
    recurrence_end_date: Optional[datetime] = None  # Fecha de finalización de la recurrencia
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InternalReminderCreate(BaseModel):
    title: str
    reminder_datetime: datetime
    minutes_before: int = 0  # Default: a la hora exacta
    description: Optional[str] = None
    is_recurring: bool = False
    recurrence_type: Optional[str] = None  # 'daily', 'weekly', 'monthly', 'yearly'
    recurrence_end_date: Optional[datetime] = None

class InternalReminderUpdate(BaseModel):
    title: str
    reminder_datetime: datetime
    minutes_before: int
    description: Optional[str] = None
    completed: Optional[bool] = None
    is_recurring: Optional[bool] = None
    recurrence_type: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None

class InternalReminderResponse(BaseModel):
    id: str
    title: str
    reminder_datetime: datetime
    reminder_time: datetime
    minutes_before: int
    description: Optional[str]
    sent: bool
    completed: bool
    is_recurring: bool
    recurrence_type: Optional[str]
    recurrence_end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime