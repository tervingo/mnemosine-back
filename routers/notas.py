from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from models.models import Nota, NotaCreate, NotaUpdate, NotaResponse, User
from auth.auth import get_current_user
from database.connection import (
    get_notas_collection, get_cajas_collection,
    get_cajitas_collection, get_armarios_collection
)
from bson import ObjectId
from datetime import datetime

router = APIRouter()

class MoveNotaRequest(BaseModel):
    new_parent_id: str
    new_parent_type: str

@router.get("/search", response_model=List[NotaResponse])
async def search_notas(
    q: str,
    current_user: User = Depends(get_current_user)
):
    """Buscar notas por título, contenido o etiquetas"""
    collection = await get_notas_collection()

    # Búsqueda en título, contenido y etiquetas
    search_query = {
        "owner_id": current_user.id,
        "$or": [
            {"titulo": {"$regex": q, "$options": "i"}},
            {"contenido": {"$regex": q, "$options": "i"}},
            {"etiquetas": {"$regex": q, "$options": "i"}}
        ]
    }

    notas_cursor = collection.find(search_query)
    notas = await notas_cursor.to_list(length=None)

    return [
        NotaResponse(
            id=str(nota["_id"]),
            titulo=nota["titulo"],
            contenido=nota["contenido"],
            etiquetas=nota["etiquetas"],
            attachments=nota.get("attachments", []),
            parent_id=str(nota["parent_id"]),
            parent_type=nota["parent_type"],
            created_at=nota["created_at"],
            updated_at=nota["updated_at"]
        ) for nota in notas
    ]

@router.get("/etiquetas", response_model=List[str])
async def get_all_etiquetas(current_user: User = Depends(get_current_user)):
    """Obtener todas las etiquetas únicas del usuario"""
    collection = await get_notas_collection()

    pipeline = [
        {"$match": {"owner_id": current_user.id}},
        {"$unwind": "$etiquetas"},
        {"$group": {"_id": "$etiquetas"}},
        {"$sort": {"_id": 1}}
    ]

    result = await collection.aggregate(pipeline).to_list(length=None)
    return [item["_id"] for item in result if item["_id"]]

@router.get("/container/{container_id}/{container_type}", response_model=List[NotaResponse])
async def get_notas_by_container(
    container_id: str,
    container_type: str,
    current_user: User = Depends(get_current_user)
):
    """Obtener notas de una caja o cajita específica"""
    if container_type not in ["caja", "cajita"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de contenedor inválido. Debe ser 'caja' o 'cajita'"
        )

    try:
        # Verificar permisos según el tipo de contenedor
        await verify_container_permissions(container_id, container_type, current_user)

        collection = await get_notas_collection()
        notas_cursor = collection.find({
            "parent_id": ObjectId(container_id),
            "parent_type": container_type
        })
        notas = await notas_cursor.to_list(length=None)

        return [
            NotaResponse(
                id=str(nota["_id"]),
                titulo=nota["titulo"],
                contenido=nota["contenido"],
                etiquetas=nota["etiquetas"],
                attachments=nota.get("attachments", []),
                parent_id=str(nota["parent_id"]),
                parent_type=nota["parent_type"],
                created_at=nota["created_at"],
                updated_at=nota["updated_at"]
            ) for nota in notas
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de contenedor inválido"
        )

@router.get("/{nota_id}", response_model=NotaResponse)
async def get_nota(nota_id: str, current_user: User = Depends(get_current_user)):
    """Obtener una nota específica"""
    try:
        collection = await get_notas_collection()
        nota = await collection.find_one({
            "_id": ObjectId(nota_id),
            "owner_id": current_user.id
        })

        if not nota:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nota no encontrada"
            )

        return NotaResponse(
            id=str(nota["_id"]),
            titulo=nota["titulo"],
            contenido=nota["contenido"],
            etiquetas=nota["etiquetas"],
            attachments=nota.get("attachments", []),
            parent_id=str(nota["parent_id"]),
            parent_type=nota["parent_type"],
            created_at=nota["created_at"],
            updated_at=nota["updated_at"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de nota inválido"
        )

@router.post("/", response_model=NotaResponse)
async def create_nota(
    nota: NotaCreate,
    current_user: User = Depends(get_current_user)
):
    """Crear nueva nota"""
    try:
        # Verificar permisos del contenedor padre
        await verify_container_permissions(nota.parent_id, nota.parent_type, current_user)

        new_nota = Nota(
            titulo=nota.titulo,
            contenido=nota.contenido,
            etiquetas=nota.etiquetas,
            owner_id=current_user.id,
            parent_id=ObjectId(nota.parent_id),
            parent_type=nota.parent_type
        )

        collection = await get_notas_collection()
        result = await collection.insert_one(new_nota.dict(by_alias=True, exclude={"id"}))

        created_nota = await collection.find_one({"_id": result.inserted_id})
        return NotaResponse(
            id=str(created_nota["_id"]),
            titulo=created_nota["titulo"],
            contenido=created_nota["contenido"],
            etiquetas=created_nota["etiquetas"],
            attachments=created_nota.get("attachments", []),
            parent_id=str(created_nota["parent_id"]),
            parent_type=created_nota["parent_type"],
            created_at=created_nota["created_at"],
            updated_at=created_nota["updated_at"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear la nota"
        )

@router.put("/{nota_id}", response_model=NotaResponse)
async def update_nota(
    nota_id: str,
    nota_update: NotaUpdate,
    current_user: User = Depends(get_current_user)
):
    """Actualizar nota"""
    try:
        collection = await get_notas_collection()

        # Verificar que la nota existe y pertenece al usuario
        existing_nota = await collection.find_one({
            "_id": ObjectId(nota_id),
            "owner_id": current_user.id
        })

        if not existing_nota:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nota no encontrada"
            )

        # Preparar datos para actualizar
        update_data = {k: v for k, v in nota_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()

        await collection.update_one(
            {"_id": ObjectId(nota_id)},
            {"$set": update_data}
        )

        updated_nota = await collection.find_one({"_id": ObjectId(nota_id)})
        return NotaResponse(
            id=str(updated_nota["_id"]),
            titulo=updated_nota["titulo"],
            contenido=updated_nota["contenido"],
            etiquetas=updated_nota["etiquetas"],
            attachments=updated_nota.get("attachments", []),
            parent_id=str(updated_nota["parent_id"]),
            parent_type=updated_nota["parent_type"],
            created_at=updated_nota["created_at"],
            updated_at=updated_nota["updated_at"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de nota inválido"
        )

@router.delete("/{nota_id}")
async def delete_nota(
    nota_id: str,
    current_user: User = Depends(get_current_user)
):
    """Eliminar nota"""
    try:
        collection = await get_notas_collection()

        # Verificar que la nota existe y pertenece al usuario
        nota = await collection.find_one({
            "_id": ObjectId(nota_id),
            "owner_id": current_user.id
        })

        if not nota:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nota no encontrada"
            )

        await collection.delete_one({"_id": ObjectId(nota_id)})
        return {"message": "Nota eliminada correctamente"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de nota inválido"
        )

@router.put("/{nota_id}/move")
async def move_nota(
    nota_id: str,
    move_request: MoveNotaRequest,
    current_user: User = Depends(get_current_user)
):
    """Mover nota a una nueva ubicación"""
    try:
        if move_request.new_parent_type not in ["caja", "cajita"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de contenedor inválido. Debe ser 'caja' o 'cajita'"
            )

        collection = await get_notas_collection()

        # Verificar que la nota existe y pertenece al usuario
        nota = await collection.find_one({
            "_id": ObjectId(nota_id),
            "owner_id": current_user.id
        })

        if not nota:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nota no encontrada"
            )

        # Verificar permisos sobre la nueva ubicación
        await verify_container_permissions(move_request.new_parent_id, move_request.new_parent_type, current_user)

        # Actualizar la ubicación de la nota
        await collection.update_one(
            {"_id": ObjectId(nota_id)},
            {"$set": {
                "parent_id": ObjectId(move_request.new_parent_id),
                "parent_type": move_request.new_parent_type,
                "updated_at": datetime.utcnow()
            }}
        )

        return {"message": "Nota movida correctamente"}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al mover la nota"
        )

async def verify_container_permissions(container_id: str, container_type: str, user: User):
    """Verificar que el usuario tiene permisos sobre el contenedor"""
    if container_type == "caja":
        # Verificar caja y su armario
        cajas_collection = await get_cajas_collection()
        caja = await cajas_collection.find_one({"_id": ObjectId(container_id)})

        if not caja:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caja no encontrada"
            )

        armarios_collection = await get_armarios_collection()
        armario = await armarios_collection.find_one({
            "_id": caja["armario_id"],
            "owner_id": user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos sobre esta caja"
            )

    elif container_type == "cajita":
        # Verificar cajita, su caja y armario
        cajitas_collection = await get_cajitas_collection()
        cajita = await cajitas_collection.find_one({"_id": ObjectId(container_id)})

        if not cajita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cajita no encontrada"
            )

        cajas_collection = await get_cajas_collection()
        caja = await cajas_collection.find_one({"_id": cajita["caja_id"]})

        if not caja:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caja padre no encontrada"
            )

        armarios_collection = await get_armarios_collection()
        armario = await armarios_collection.find_one({
            "_id": caja["armario_id"],
            "owner_id": user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos sobre esta cajita"
            )