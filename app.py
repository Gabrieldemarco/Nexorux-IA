# 1. ESTA LÍNEA ES LA CLAVE QUE TE FALTA
from fastapi import FastAPI 
# OJO: Si usas cualquier otra cosa, como 'APIRouter', también debe importarse.

# 2. AHORA SÍ PODRÁ CREAR EL OBJETO APP SIN ERROR
app = FastAPI()

# 3. Tu código de ejemplo (que ya revisamos)
@app.get("/")
def read_root():
    return {"mensaje": "¡Funciona perfectamente!"}
