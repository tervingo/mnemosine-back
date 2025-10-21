# Mnemosyne Backend

API REST en FastAPI para el sistema de notas organizadas jerárquicamente.

## Tecnologías

- **FastAPI** - Framework web
- **MongoDB** con Motor - Base de datos
- **JWT** - Autenticación
- **Pydantic** - Validación de datos
- **Uvicorn** - Servidor ASGI

## Estructura del Proyecto

```
backend/
├── main.py                 # Aplicación principal
├── requirements.txt        # Dependencias
├── .env.example           # Variables de entorno ejemplo
├── models/                # Modelos de datos
│   └── models.py
├── database/              # Configuración de base de datos
│   └── connection.py
├── auth/                  # Sistema de autenticación
│   └── auth.py
└── routers/               # Endpoints de la API
    ├── auth.py
    ├── armarios.py
    ├── cajas.py
    ├── cajitas.py
    └── notas.py
```

## Configuración

1. Crear entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   ```

4. Editar `.env` con tu configuración:
   ```
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
   DATABASE_NAME=mnemosine
   SECRET_KEY=tu_clave_secreta_muy_segura
   ```

## Desarrollo

```bash
# Ejecutar servidor de desarrollo
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# O con Python
python main.py
```

La API estará disponible en: http://localhost:8000

## Documentación API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints Principales

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Información del usuario actual

### Armarios
- `GET /api/armarios/` - Listar armarios
- `POST /api/armarios/` - Crear armario
- `GET /api/armarios/{id}` - Obtener armario
- `PUT /api/armarios/{id}` - Actualizar armario
- `DELETE /api/armarios/{id}` - Eliminar armario

### Cajas
- `GET /api/cajas/armario/{armario_id}` - Cajas de un armario
- `POST /api/cajas/` - Crear caja
- `GET /api/cajas/{id}` - Obtener caja
- `PUT /api/cajas/{id}` - Actualizar caja
- `DELETE /api/cajas/{id}` - Eliminar caja

### Cajitas
- `GET /api/cajitas/caja/{caja_id}` - Cajitas de una caja
- `POST /api/cajitas/` - Crear cajita
- `GET /api/cajitas/{id}` - Obtener cajita
- `PUT /api/cajitas/{id}` - Actualizar cajita
- `DELETE /api/cajitas/{id}` - Eliminar cajita

### Notas
- `GET /api/notas/container/{id}/{type}` - Notas de un contenedor
- `POST /api/notas/` - Crear nota
- `GET /api/notas/{id}` - Obtener nota
- `PUT /api/notas/{id}` - Actualizar nota
- `DELETE /api/notas/{id}` - Eliminar nota
- `GET /api/notas/search?q={query}` - Buscar notas
- `GET /api/notas/etiquetas` - Obtener todas las etiquetas

## Modelo de Datos

La jerarquía de datos es:
```
Usuario
  └── Armario
      └── Caja
          ├── Nota
          └── Cajita
              └── Nota
```

## Deploy

La aplicación está configurada para ser desplegada en Render.

### Variables de entorno para producción:
- `MONGODB_URL`: Conexión a MongoDB Atlas
- `DATABASE_NAME`: Nombre de la base de datos
- `SECRET_KEY`: Clave secreta para JWT
- `ALGORITHM`: Algoritmo JWT (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Duración del token

## Seguridad

- Autenticación JWT
- Validación de permisos por usuario
- Sanitización de datos con Pydantic
- CORS configurado para el frontend