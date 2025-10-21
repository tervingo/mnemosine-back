from pydantic import BaseModel, Field
from typing import List, Optional, Annotated
from datetime import datetime
from bson import ObjectId

# Simplificamos para compatibilidad con Pydantic v2
def validate_object_id(v):
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    if v is None:
        return ObjectId()
    raise ValueError("Invalid ObjectId")

# Tipo simple para ObjectId
ObjectIdType = Annotated[ObjectId, Field()]

class User(BaseModel):
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    email: str
    username: str
    hashed_password: str
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
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

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
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

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
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

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
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

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