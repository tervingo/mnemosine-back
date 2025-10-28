from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from routers import armarios, cajas, cajitas, notas, auth, reminders, cron
from database.connection import connect_to_mongo, close_mongo_connection

load_dotenv()

app = FastAPI(
    title="Mnemosyne API",
    description="API para gestión de notas organizadas jerárquicamente",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://mymir.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(armarios.router, prefix="/api/armarios", tags=["armarios"])
app.include_router(cajas.router, prefix="/api/cajas", tags=["cajas"])
app.include_router(cajitas.router, prefix="/api/cajitas", tags=["cajitas"])
app.include_router(notas.router, prefix="/api/notas", tags=["notas"])
app.include_router(reminders.router, prefix="/api", tags=["reminders"])
app.include_router(cron.router, prefix="/api", tags=["cron"])

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Mnemosyne API v1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)