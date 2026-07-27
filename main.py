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
    datos['idHabitacion'] = int(habitacion_id)
    datos['fecha'] = datetime.now()   #(punto 4)
    datos.setdefault('critico', False)
    datos.setdefault('conformidad', None)
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

# RF3 - Consultar reportes de una habitación
@app.delete('/reportes/{reporte_id}')
def delete_reporte(reporte_id: str, idPrestador: int):
    reporte = db["Reportes"].find_one({"_id": ObjectId(reporte_id)})
    if not reporte:
        return {"error": "El reporte no existe"}
 
    if reporte["idPrestador"] != idPrestador:
        return {"error": "No tiene permiso para eliminar este reporte"}
 
    db["Reportes"].delete_one({"_id": ObjectId(reporte_id)})
    return {"mensaje": "Reporte eliminado"}



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


# RF5 - Marcar reporte como crítico (administrador)
@app.put('/reportes/{reporte_id}/critico')
def put_critico(reporte_id: str, datos: dict):
    if "critico" not in datos:
        return {"error": "Falta el campo critico (true/false)"}
 
    reporte = db["Reportes"].find_one({"_id": ObjectId(reporte_id)})
    if not reporte:
        return {"error": "El reporte no existe"}
 
    db["Reportes"].update_one(
        {"_id": ObjectId(reporte_id)},
        {"$set": {"critico": bool(datos["critico"])}}
    )
    return {"mensaje": "Reporte actualizado", "critico": bool(datos["critico"])}

# RF7 - Agregar / editar observación del administrador (se sobreescribe)
@app.put('/reportes/{reporte_id}/observacion')
def put_observacion(reporte_id: str, datos: dict):
    if "texto" not in datos or "idAdmin" not in datos:
        return {"error": "Faltan campos texto e idAdmin"}
 
    reporte = db["Reportes"].find_one({"_id": ObjectId(reporte_id)})
    if not reporte:
        return {"error": "El reporte no existe"}
 
    observacion = {
        "texto": datos["texto"],
        "idAdmin": datos["idAdmin"],
        "fechaObservacion": datetime.now()
    }
 
    db["Reportes"].update_one(
        {"_id": ObjectId(reporte_id)},
        {"$set": {"observacion": observacion}}
    )
    return {"mensaje": "Observación guardada", "observacion": {
        "texto": observacion["texto"],
        "idAdmin": observacion["idAdmin"],
        "fechaObservacion": observacion["fechaObservacion"].isoformat()
    }}

# RF8 - Eliminar reporte (administrador, sin importar el dueño)
@app.delete('/admin/reportes/{reporte_id}')
def delete_reporte_admin(reporte_id: str):
    reporte = db["Reportes"].find_one({"_id": ObjectId(reporte_id)})
    if not reporte:
        return {"error": "El reporte no existe"}
 
    db["Reportes"].delete_one({"_id": ObjectId(reporte_id)})
    return {"mensaje": "Reporte eliminado por administrador"}

# RF9 - Cierre de reporte con conformidad
@app.put('/reportes/{reporte_id}/conformidad')
def put_conformidad(reporte_id: str, datos: dict):
    if "conformidad" not in datos:
        return {"error": "Falta el campo conformidad (true/false)"}
 
    reporte = db["Reportes"].find_one({"_id": ObjectId(reporte_id)})
    if not reporte:
        return {"error": "El reporte no existe"}
 
    conformidad = datos["conformidad"]
 
    if conformidad == False and not datos.get("motivoInconformidad"):
        return {"error": "motivoInconformidad es obligatorio cuando conformidad es false"}
 
    campos = {"conformidad": conformidad}
    if conformidad == False:
        campos["motivoInconformidad"] = datos["motivoInconformidad"]
    else:
        campos["motivoInconformidad"] = None
 
    db["Reportes"].update_one(
        {"_id": ObjectId(reporte_id)},
        {"$set": campos}
    )
    return {"mensaje": "Conformidad registrada", "conformidad": conformidad}
 

@app.get('/reportes/{reporte_id}')
def get_reporte(reporte_id: str):
    reporte = db["Reportes"].find_one({"_id": ObjectId(reporte_id)})
    if reporte:
        reporte["_id"] = str(reporte["_id"])
    return reporte
