from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

client = MongoClient(os.environ["MONGO_URI"])
db = client["ISIS2304A02202619"] 

@app.get("/")
def inicio():
    return {"estado": "API funcionando correctamente"}

# RF1 - Crear reporte
@app.post('/habitaciones/{habitacion_id}/reportes')
def post_reporte(habitacion_id: str, datos: dict):
    datos['idHabitacion'] = habitacion_id
    datos['fecha_creacion'] = datetime.now().isoformat()
    datos.setdefault('critico', False)
    resultado = db["reportes"].insert_one(datos)
    return {'mensaje': 'Reporte guardado', 'id': str(resultado.inserted_id)}

# RF4 - Consultar reportes de una habitación 
@app.get('/habitaciones/{habitacion_id}/reportes')
def get_reportes(habitacion_id: str, pagina: int = 1, tamano: int = 10):
    skip = (pagina - 1) * tamano
    reportes = list(
        db["reportes"]
        .find({"idHabitacion": habitacion_id})
        .sort("fecha_creacion", -1)
        .skip(skip)
        .limit(tamano)
    )
    for r in reportes:
        r["_id"] = str(r["_id"])
    return reportes

@app.get('/reportes/{reporte_id}')
def get_reporte(reporte_id: str):
    reporte = db["Reportes"].find_one({"_id": ObjectId(reporte_id)})
    if reporte:
        reporte["_id"] = str(reporte["_id"])
    return reporte

@app.put('/reportes/{reporte_id}')
def put_reporte(reporte_id: str, datos: dict):
    datos["fecha_modificacion"] = datetime.now().isoformat()
    resultado = db["Reportes"].update_one(
        {"_id": ObjectId(reporte_id)},
        {"$set": datos}
    )
    return {"mensaje": "Reporte actualizado", "modificados": resultado.modified_count}