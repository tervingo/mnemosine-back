from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from models.models import Cajita, CajitaCreate, CajitaUpdate, CajitaResponse, User
from auth.auth import get_current_user
from database.connection import (
    get_cajitas_collection, get_cajas_collection,
    get_armarios_collection, get_notas_collection
)
from routers.armarios import get_cajita_with_content
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.get("/caja/{caja_id}", response_model=List[CajitaResponse])
async def get_cajitas_by_caja(
    caja_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las cajitas de una caja"""
    try:
        # Verificar que la caja existe y el usuario tiene permisos
        cajas_collection = await get_cajas_collection()
        caja = await cajas_collection.find_one({"_id": ObjectId(caja_id)})

        if not caja:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caja no encontrada"
            )

        # Verificar que el armario pertenece al usuario
        armarios_collection = await get_armarios_collection()
        armario = await armarios_collection.find_one({
            "_id": caja["armario_id"],
            "owner_id": current_user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a esta caja"
            )

        # Obtener cajitas
        collection = await get_cajitas_collection()
        cajitas_cursor = collection.find({"caja_id": ObjectId(caja_id)})
        cajitas = await cajitas_cursor.to_list(length=None)

        result = []
        for cajita in cajitas:
            cajita_response = await get_cajita_with_content(cajita)
            result.append(cajita_response)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de caja inválido"
        )

@router.get("/{cajita_id}", response_model=CajitaResponse)
async def get_cajita(cajita_id: str, current_user: User = Depends(get_current_user)):
    """Obtener una cajita específica con todas sus notas"""
    try:
        collection = await get_cajitas_collection()
        cajita = await collection.find_one({"_id": ObjectId(cajita_id)})

        if not cajita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cajita no encontrada"
            )

        # Verificar permisos a través de la caja y armario
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
            "owner_id": current_user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a esta cajita"
            )

        return await get_cajita_with_content(cajita)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cajita inválido"
        )

@router.post("/", response_model=CajitaResponse)
async def create_cajita(
    cajita: CajitaCreate,
    current_user: User = Depends(get_current_user)
):
    """Crear nueva cajita en una caja"""
    try:
        # Verificar que la caja existe y el usuario tiene permisos
        cajas_collection = await get_cajas_collection()
        caja = await cajas_collection.find_one({"_id": ObjectId(cajita.caja_id)})

        if not caja:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caja no encontrada"
            )

        armarios_collection = await get_armarios_collection()
        armario = await armarios_collection.find_one({
            "_id": caja["armario_id"],
            "owner_id": current_user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para crear cajitas en esta caja"
            )

        new_cajita = Cajita(
            nombre=cajita.nombre,
            descripcion=cajita.descripcion,
            owner_id=current_user.id,
            caja_id=ObjectId(cajita.caja_id)
        )

        collection = await get_cajitas_collection()
        result = await collection.insert_one(new_cajita.dict(by_alias=True, exclude={"id"}))

        created_cajita = await collection.find_one({"_id": result.inserted_id})
        return await get_cajita_with_content(created_cajita)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de caja inválido"
        )

@router.put("/{cajita_id}", response_model=CajitaResponse)
async def update_cajita(
    cajita_id: str,
    cajita_update: CajitaUpdate,
    current_user: User = Depends(get_current_user)
):
    """Actualizar cajita"""
    try:
        collection = await get_cajitas_collection()

        # Verificar que la cajita existe
        existing_cajita = await collection.find_one({"_id": ObjectId(cajita_id)})
        if not existing_cajita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cajita no encontrada"
            )

        # Verificar permisos a través de caja y armario
        cajas_collection = await get_cajas_collection()
        caja = await cajas_collection.find_one({"_id": existing_cajita["caja_id"]})

        if not caja:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caja padre no encontrada"
            )

        armarios_collection = await get_armarios_collection()
        armario = await armarios_collection.find_one({
            "_id": caja["armario_id"],
            "owner_id": current_user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para modificar esta cajita"
            )

        # Preparar datos para actualizar
        update_data = {k: v for k, v in cajita_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()

        await collection.update_one(
            {"_id": ObjectId(cajita_id)},
            {"$set": update_data}
        )

        updated_cajita = await collection.find_one({"_id": ObjectId(cajita_id)})
        return await get_cajita_with_content(updated_cajita)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cajita inválido"
        )

@router.delete("/{cajita_id}")
async def delete_cajita(
    cajita_id: str,
    current_user: User = Depends(get_current_user)
):
    """Eliminar cajita solo si está vacía"""
    try:
        collection = await get_cajitas_collection()

        # Verificar que la cajita existe
        cajita = await collection.find_one({"_id": ObjectId(cajita_id)})
        if not cajita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cajita no encontrada"
            )

        # Verificar permisos a través de caja y armario
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
            "owner_id": current_user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para eliminar esta cajita"
            )

        # Verificar que la cajita está vacía (no tiene notas)
        notas_collection = await get_notas_collection()
        notas_count = await notas_collection.count_documents({
            "parent_id": ObjectId(cajita_id),
            "parent_type": "cajita"
        })

        if notas_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar una cajita que contiene notas. Elimina primero todas las notas."
            )

        # Eliminar la cajita
        await collection.delete_one({"_id": ObjectId(cajita_id)})

        return {"message": "Cajita eliminada correctamente"}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cajita inválido"
        )