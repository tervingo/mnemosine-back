import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from dotenv import load_dotenv

load_dotenv()

# Configurar Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Configuración de límites
MAX_FILE_SIZE_MB = 20
MAX_FILES_PER_NOTE = 3
ALLOWED_IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'heic', 'heif', 'bmp', 'svg']
ALLOWED_VIDEO_FORMATS = ['mp4', 'mov', 'avi', 'wmv', 'flv', 'webm']
ALLOWED_DOCUMENT_FORMATS = ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx']

def upload_file_to_cloudinary(file_content: bytes, filename: str, folder: str = "mnemosine/attachments") -> dict:
    """
    Sube un archivo a Cloudinary

    Args:
        file_content: Contenido del archivo en bytes
        filename: Nombre del archivo
        folder: Carpeta en Cloudinary donde se guardará

    Returns:
        dict con url, public_id, format, bytes, etc.
    """
    try:
        # Determinar el tipo de recurso basado en la extensión
        file_extension = filename.split('.')[-1].lower()

        if file_extension in ALLOWED_IMAGE_FORMATS:
            resource_type = 'image'
        elif file_extension in ALLOWED_VIDEO_FORMATS:
            resource_type = 'video'
        else:
            resource_type = 'raw'  # Para documentos y otros archivos

        # Subir archivo
        result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            resource_type=resource_type,
            use_filename=True,
            unique_filename=True,
            overwrite=False
        )

        return {
            'url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'format': result.get('format'),
            'resource_type': result.get('resource_type'),
            'bytes': result.get('bytes'),
            'created_at': result.get('created_at')
        }

    except Exception as e:
        raise Exception(f"Error al subir archivo a Cloudinary: {str(e)}")


def delete_file_from_cloudinary(public_id: str, resource_type: str = 'image') -> bool:
    """
    Elimina un archivo de Cloudinary

    Args:
        public_id: ID público del archivo en Cloudinary
        resource_type: Tipo de recurso ('image', 'video', 'raw')

    Returns:
        True si se eliminó correctamente
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result.get('result') == 'ok'
    except Exception as e:
        print(f"Error al eliminar archivo de Cloudinary: {str(e)}")
        return False


def is_valid_file_format(filename: str) -> tuple[bool, str]:
    """
    Verifica si el formato del archivo es válido

    Returns:
        (es_válido, tipo_archivo)
    """
    file_extension = filename.split('.')[-1].lower()

    if file_extension in ALLOWED_IMAGE_FORMATS:
        return True, 'image'
    elif file_extension in ALLOWED_VIDEO_FORMATS:
        return True, 'video'
    elif file_extension in ALLOWED_DOCUMENT_FORMATS:
        return True, 'document'
    else:
        return False, 'unknown'


def is_valid_file_size(file_size_bytes: int) -> bool:
    """
    Verifica si el tamaño del archivo es válido
    """
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    return file_size_bytes <= max_size_bytes
