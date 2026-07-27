from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import os
from bson import ObjectId

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
    datos['fecha'] = datetime.now()
    datos.setdefault('critico', False)
    resultado = db["Reportes"].insert_one(datos)
    return {'mensaje': 'Reporte guardado', 'id': str(resultado.inserted_id)}

# RF2 - Editar reporte
@app.put('/reportes/{reporte_id}')
def put_reporte(reporte_id: str, datos: dict):
    reporte = db["Reportes"].find_one({"_id": ObjectId(reporte_id)})
    if not reporte:
        return {"error": "El reporte no existe"}

    if "idPrestador" not in datos:
        return {"error": "Falta idPrestador para validar el dueño del reporte"}
    if reporte["idPrestador"] != datos["idPrestador"]:
        return {"error": "No tiene permiso para editar este reporte"}

    if "servicioCompletado" not in datos:
        return {"error": "Falta indicar si el servicio ya está completado"}
    if datos["servicioCompletado"] == True:
        return {"error": "No se puede editar el reporte, el servicio ya fue completado"}

    campos_editables = {}
    if "estado" in datos:
        campos_editables["estado"] = datos["estado"]
    if "prioridad" in datos:
        campos_editables["prioridad"] = datos["prioridad"]
    if "descripcion" in datos:
        campos_editables["descripcion"] = datos["descripcion"]

    if not campos_editables:
        return {"mensaje": "No se enviaron campos editables", "modificados": 0}

    resultado = db["Reportes"].update_one(
        {"_id": ObjectId(reporte_id)},
        {"$set": campos_editables}
    )
    return {"mensaje": "Reporte actualizado", "modificados": resultado.modified_count}

# RF4 - Consultar reportes de una habitación
@app.get('/habitaciones/{habitacion_id}/reportes')
def get_reportes(habitacion_id: str, pagina: int = 1, tamano: int = 10):
    skip = (pagina - 1) * tamano
    reportes = list(
        db["Reportes"]
        .find({"idHabitacion": habitacion_id})
        .sort("fecha", -1)
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
