from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from models.models import Caja, CajaCreate, CajaUpdate, CajaResponse, User
from auth.auth import get_current_user
from database.connection import get_cajas_collection, get_armarios_collection
from routers.armarios import get_caja_with_content, delete_caja_content
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.get("/armario/{armario_id}", response_model=List[CajaResponse])
async def get_cajas_by_armario(
    armario_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las cajas de un armario"""
    try:
        # Verificar que el armario existe y pertenece al usuario
        armarios_collection = await get_armarios_collection()
        armario = await armarios_collection.find_one({
            "_id": ObjectId(armario_id),
            "owner_id": current_user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Armario no encontrado"
            )

        # Obtener cajas
        collection = await get_cajas_collection()
        cajas_cursor = collection.find({"armario_id": ObjectId(armario_id)})
        cajas = await cajas_cursor.to_list(length=None)

        result = []
        for caja in cajas:
            caja_response = await get_caja_with_content(caja)
            result.append(caja_response)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de armario inválido"
        )

@router.get("/{caja_id}", response_model=CajaResponse)
async def get_caja(caja_id: str, current_user: User = Depends(get_current_user)):
    """Obtener una caja específica con todo su contenido"""
    try:
        collection = await get_cajas_collection()
        caja = await collection.find_one({"_id": ObjectId(caja_id)})

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

        return await get_caja_with_content(caja)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de caja inválido"
        )

@router.post("/", response_model=CajaResponse)
async def create_caja(
    caja: CajaCreate,
    current_user: User = Depends(get_current_user)
):
    """Crear nueva caja en un armario"""
    try:
        # Verificar que el armario existe y pertenece al usuario
        armarios_collection = await get_armarios_collection()
        armario = await armarios_collection.find_one({
            "_id": ObjectId(caja.armario_id),
            "owner_id": current_user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Armario no encontrado"
            )

        new_caja = Caja(
            nombre=caja.nombre,
            descripcion=caja.descripcion,
            color=caja.color,
            owner_id=current_user.id,
            armario_id=ObjectId(caja.armario_id)
        )

        collection = await get_cajas_collection()
        result = await collection.insert_one(new_caja.dict(by_alias=True, exclude={"id"}))

        created_caja = await collection.find_one({"_id": result.inserted_id})
        return await get_caja_with_content(created_caja)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de armario inválido"
        )

@router.put("/{caja_id}", response_model=CajaResponse)
async def update_caja(
    caja_id: str,
    caja_update: CajaUpdate,
    current_user: User = Depends(get_current_user)
):
    """Actualizar caja"""
    try:
        collection = await get_cajas_collection()

        # Verificar que la caja existe
        existing_caja = await collection.find_one({"_id": ObjectId(caja_id)})
        if not existing_caja:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caja no encontrada"
            )

        # Verificar que el armario pertenece al usuario
        armarios_collection = await get_armarios_collection()
        armario = await armarios_collection.find_one({
            "_id": existing_caja["armario_id"],
            "owner_id": current_user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para modificar esta caja"
            )

        # Preparar datos para actualizar
        update_data = {k: v for k, v in caja_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()

        await collection.update_one(
            {"_id": ObjectId(caja_id)},
            {"$set": update_data}
        )

        updated_caja = await collection.find_one({"_id": ObjectId(caja_id)})
        return await get_caja_with_content(updated_caja)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de caja inválido"
        )

@router.delete("/{caja_id}")
async def delete_caja(
    caja_id: str,
    current_user: User = Depends(get_current_user)
):
    """Eliminar caja y todo su contenido"""
    try:
        collection = await get_cajas_collection()

        # Verificar que la caja existe
        caja = await collection.find_one({"_id": ObjectId(caja_id)})
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
                detail="No tienes permisos para eliminar esta caja"
            )

        # Eliminar todo el contenido de la caja
        await delete_caja_content(ObjectId(caja_id))

        # Eliminar la caja
        await collection.delete_one({"_id": ObjectId(caja_id)})

        return {"message": "Caja eliminada correctamente"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de caja inválido"
        )