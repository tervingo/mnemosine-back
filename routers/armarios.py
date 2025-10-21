from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from models.models import (
    Armario, ArmarioCreate, ArmarioUpdate, ArmarioResponse,
    User, CajaResponse, CajitaResponse, NotaResponse
)
from auth.auth import get_current_user
from database.connection import (
    get_armarios_collection, get_cajas_collection,
    get_cajitas_collection, get_notas_collection
)
from bson import ObjectId
from datetime import datetime

router = APIRouter()

async def create_default_armario(user_id: str):
    """Crear armario por defecto para nuevo usuario"""
    collection = await get_armarios_collection()
    default_armario = Armario(
        nombre="Mi Armario",
        descripcion="Armario principal para mis notas",
        owner_id=ObjectId(user_id),
        is_default=True
    )
    await collection.insert_one(default_armario.dict(by_alias=True, exclude={"id"}))

@router.get("/", response_model=List[ArmarioResponse])
async def get_armarios(current_user: User = Depends(get_current_user)):
    """Obtener todos los armarios del usuario"""
    collection = await get_armarios_collection()
    armarios_cursor = collection.find({"owner_id": current_user.id})
    armarios = await armarios_cursor.to_list(length=None)

    result = []
    for armario in armarios:
        armario_response = await get_armario_with_content(armario)
        result.append(armario_response)

    return result

@router.get("/{armario_id}", response_model=ArmarioResponse)
async def get_armario(armario_id: str, current_user: User = Depends(get_current_user)):
    """Obtener un armario específico con todo su contenido"""
    try:
        collection = await get_armarios_collection()
        armario = await collection.find_one({
            "_id": ObjectId(armario_id),
            "owner_id": current_user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Armario no encontrado"
            )

        return await get_armario_with_content(armario)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de armario inválido"
        )

async def get_armario_with_content(armario_data: dict) -> ArmarioResponse:
    """Obtener armario con todas sus cajas, cajitas y notas"""
    # Obtener cajas del armario
    cajas_collection = await get_cajas_collection()
    cajas_cursor = cajas_collection.find({"armario_id": armario_data["_id"]})
    cajas = await cajas_cursor.to_list(length=None)

    cajas_response = []
    for caja in cajas:
        caja_response = await get_caja_with_content(caja)
        cajas_response.append(caja_response)

    return ArmarioResponse(
        id=str(armario_data["_id"]),
        nombre=armario_data["nombre"],
        descripcion=armario_data.get("descripcion"),
        is_default=armario_data.get("is_default", False),
        cajas=cajas_response,
        created_at=armario_data["created_at"],
        updated_at=armario_data["updated_at"]
    )

async def get_caja_with_content(caja_data: dict) -> CajaResponse:
    """Obtener caja con todas sus cajitas y notas"""
    # Obtener cajitas de la caja
    cajitas_collection = await get_cajitas_collection()
    cajitas_cursor = cajitas_collection.find({"caja_id": caja_data["_id"]})
    cajitas = await cajitas_cursor.to_list(length=None)

    cajitas_response = []
    for cajita in cajitas:
        cajita_response = await get_cajita_with_content(cajita)
        cajitas_response.append(cajita_response)

    # Obtener notas directas de la caja
    notas_collection = await get_notas_collection()
    notas_cursor = notas_collection.find({
        "parent_id": caja_data["_id"],
        "parent_type": "caja"
    })
    notas = await notas_cursor.to_list(length=None)

    notas_response = [
        NotaResponse(
            id=str(nota["_id"]),
            titulo=nota["titulo"],
            contenido=nota["contenido"],
            etiquetas=nota["etiquetas"],
            archivos_adjuntos=nota.get("archivos_adjuntos", []),
            parent_id=str(nota["parent_id"]),
            parent_type=nota["parent_type"],
            created_at=nota["created_at"],
            updated_at=nota["updated_at"]
        ) for nota in notas
    ]

    return CajaResponse(
        id=str(caja_data["_id"]),
        nombre=caja_data["nombre"],
        descripcion=caja_data.get("descripcion"),
        color=caja_data.get("color", "#6366f1"),
        armario_id=str(caja_data["armario_id"]),
        cajitas=cajitas_response,
        notas=notas_response,
        created_at=caja_data["created_at"],
        updated_at=caja_data["updated_at"]
    )

async def get_cajita_with_content(cajita_data: dict) -> CajitaResponse:
    """Obtener cajita con todas sus notas"""
    # Obtener notas de la cajita
    notas_collection = await get_notas_collection()
    notas_cursor = notas_collection.find({
        "parent_id": cajita_data["_id"],
        "parent_type": "cajita"
    })
    notas = await notas_cursor.to_list(length=None)

    notas_response = [
        NotaResponse(
            id=str(nota["_id"]),
            titulo=nota["titulo"],
            contenido=nota["contenido"],
            etiquetas=nota["etiquetas"],
            archivos_adjuntos=nota.get("archivos_adjuntos", []),
            parent_id=str(nota["parent_id"]),
            parent_type=nota["parent_type"],
            created_at=nota["created_at"],
            updated_at=nota["updated_at"]
        ) for nota in notas
    ]

    return CajitaResponse(
        id=str(cajita_data["_id"]),
        nombre=cajita_data["nombre"],
        descripcion=cajita_data.get("descripcion"),
        caja_id=str(cajita_data["caja_id"]),
        notas=notas_response,
        created_at=cajita_data["created_at"],
        updated_at=cajita_data["updated_at"]
    )

@router.post("/", response_model=ArmarioResponse)
async def create_armario(
    armario: ArmarioCreate,
    current_user: User = Depends(get_current_user)
):
    """Crear nuevo armario"""
    new_armario = Armario(
        nombre=armario.nombre,
        descripcion=armario.descripcion,
        owner_id=current_user.id,
        is_default=armario.is_default
    )

    collection = await get_armarios_collection()
    result = await collection.insert_one(new_armario.dict(by_alias=True, exclude={"id"}))

    created_armario = await collection.find_one({"_id": result.inserted_id})
    return await get_armario_with_content(created_armario)

@router.put("/{armario_id}", response_model=ArmarioResponse)
async def update_armario(
    armario_id: str,
    armario_update: ArmarioUpdate,
    current_user: User = Depends(get_current_user)
):
    """Actualizar armario"""
    try:
        collection = await get_armarios_collection()

        # Verificar que el armario existe y pertenece al usuario
        existing_armario = await collection.find_one({
            "_id": ObjectId(armario_id),
            "owner_id": current_user.id
        })

        if not existing_armario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Armario no encontrado"
            )

        # Preparar datos para actualizar
        update_data = {k: v for k, v in armario_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()

        await collection.update_one(
            {"_id": ObjectId(armario_id)},
            {"$set": update_data}
        )

        updated_armario = await collection.find_one({"_id": ObjectId(armario_id)})
        return await get_armario_with_content(updated_armario)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de armario inválido"
        )

@router.delete("/{armario_id}")
async def delete_armario(
    armario_id: str,
    current_user: User = Depends(get_current_user)
):
    """Eliminar armario y todo su contenido"""
    try:
        collection = await get_armarios_collection()

        # Verificar que el armario existe y pertenece al usuario
        armario = await collection.find_one({
            "_id": ObjectId(armario_id),
            "owner_id": current_user.id
        })

        if not armario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Armario no encontrado"
            )

        # Eliminar todo el contenido en cascada
        await delete_armario_content(ObjectId(armario_id))

        # Eliminar el armario
        await collection.delete_one({"_id": ObjectId(armario_id)})

        return {"message": "Armario eliminado correctamente"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de armario inválido"
        )

async def delete_armario_content(armario_id: ObjectId):
    """Eliminar todo el contenido de un armario"""
    # Obtener todas las cajas del armario
    cajas_collection = await get_cajas_collection()
    cajas_cursor = cajas_collection.find({"armario_id": armario_id})
    cajas = await cajas_cursor.to_list(length=None)

    # Eliminar contenido de cada caja
    for caja in cajas:
        await delete_caja_content(caja["_id"])

    # Eliminar las cajas
    await cajas_collection.delete_many({"armario_id": armario_id})

async def delete_caja_content(caja_id: ObjectId):
    """Eliminar todo el contenido de una caja"""
    # Eliminar notas directas de la caja
    notas_collection = await get_notas_collection()
    await notas_collection.delete_many({
        "parent_id": caja_id,
        "parent_type": "caja"
    })

    # Obtener y eliminar cajitas
    cajitas_collection = await get_cajitas_collection()
    cajitas_cursor = cajitas_collection.find({"caja_id": caja_id})
    cajitas = await cajitas_cursor.to_list(length=None)

    for cajita in cajitas:
        # Eliminar notas de la cajita
        await notas_collection.delete_many({
            "parent_id": cajita["_id"],
            "parent_type": "cajita"
        })

    # Eliminar las cajitas
    await cajitas_collection.delete_many({"caja_id": caja_id})