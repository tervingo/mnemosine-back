from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional
from models.models import User, Attachment
from auth.auth import get_current_user
from database.connection import get_notas_collection
from bson import ObjectId
from datetime import datetime
from utils.cloudinary_config import (
    upload_file_to_cloudinary,
    delete_file_from_cloudinary,
    is_valid_file_format,
    is_valid_file_size,
    MAX_FILE_SIZE_MB,
    MAX_FILES_PER_NOTE
)

router = APIRouter()


@router.post("/notas/{nota_id}/attachments")
async def upload_attachment(
    nota_id: str,
    file: Optional[UploadFile] = File(None),
    link_url: Optional[str] = Form(None),
    link_type: Optional[str] = Form(None),  # 'link' o 'youtube'
    current_user: User = Depends(get_current_user)
):
    """
    Sube un archivo adjunto a una nota.
    Puede ser un archivo o un enlace/YouTube video.
    """
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

        # Verificar límite de archivos
        current_attachments = nota.get("attachments", [])
        if len(current_attachments) >= MAX_FILES_PER_NOTE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Máximo {MAX_FILES_PER_NOTE} archivos por nota"
            )

        attachment_data = {}

        # Procesar archivo subido
        if file:
            # Verificar formato
            is_valid, file_type = is_valid_file_format(file.filename)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de archivo no permitido"
                )

            # Leer el archivo
            file_content = await file.read()
            file_size = len(file_content)

            # Verificar tamaño
            if not is_valid_file_size(file_size):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El archivo excede el límite de {MAX_FILE_SIZE_MB}MB"
                )

            # Subir a Cloudinary
            cloudinary_result = upload_file_to_cloudinary(
                file_content,
                file.filename,
                folder=f"mnemosine/notas/{nota_id}"
            )

            attachment_data = {
                "id": str(ObjectId()),
                "filename": file.filename,
                "file_type": file_type,
                "url": cloudinary_result['url'],
                "cloudinary_id": cloudinary_result['public_id'],
                "size": file_size,
                "uploaded_at": datetime.utcnow()
            }

        # Procesar enlace
        elif link_url:
            if not link_type or link_type not in ['link', 'youtube']:
                link_type = 'youtube' if 'youtube.com' in link_url or 'youtu.be' in link_url else 'link'

            attachment_data = {
                "id": str(ObjectId()),
                "filename": link_url,
                "file_type": link_type,
                "url": link_url,
                "cloudinary_id": None,
                "size": None,
                "uploaded_at": datetime.utcnow()
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar un archivo o un enlace"
            )

        # Añadir attachment a la nota
        await collection.update_one(
            {"_id": ObjectId(nota_id)},
            {
                "$push": {"attachments": attachment_data},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        return {
            "message": "Archivo adjunto añadido correctamente",
            "attachment": attachment_data
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al subir archivo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivo: {str(e)}"
        )


@router.delete("/notas/{nota_id}/attachments/{attachment_id}")
async def delete_attachment(
    nota_id: str,
    attachment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Elimina un archivo adjunto de una nota"""
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

        # Buscar el attachment
        attachments = nota.get("attachments", [])
        attachment_to_delete = None

        for att in attachments:
            if att.get("id") == attachment_id:
                attachment_to_delete = att
                break

        if not attachment_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo adjunto no encontrado"
            )

        # Si tiene cloudinary_id, eliminar de Cloudinary
        if attachment_to_delete.get("cloudinary_id"):
            file_type = attachment_to_delete.get("file_type", "image")
            resource_type = "image" if file_type == "image" else "video" if file_type == "video" else "raw"

            delete_file_from_cloudinary(
                attachment_to_delete["cloudinary_id"],
                resource_type=resource_type
            )

        # Eliminar attachment de la nota
        await collection.update_one(
            {"_id": ObjectId(nota_id)},
            {
                "$pull": {"attachments": {"id": attachment_id}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        return {
            "message": "Archivo adjunto eliminado correctamente"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al eliminar archivo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar archivo: {str(e)}"
        )


@router.get("/notas/{nota_id}/attachments")
async def get_attachments(
    nota_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene todos los archivos adjuntos de una nota"""
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

        return {
            "attachments": nota.get("attachments", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener archivos adjuntos"
        )
