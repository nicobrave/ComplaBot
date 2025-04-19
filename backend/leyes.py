import json
from pathlib import Path

RUTA_JSON = Path(__file__).parent / "data" / "leyes_chile_2025.json"

# Convertir a formato lista estándar desde el esquema actual
def cargar_leyes_desde_json():
    with open(RUTA_JSON, encoding="utf-8") as f:
        data = json.load(f)
    
    leyes_planas = []
    for industria, leyes in data.items():
        for ley in leyes:
            leyes_planas.append({
                "titulo": ley.get("Ley", "Ley sin título"),
                "obligaciones": ley.get("Obligaciones clave", []),
                "industria": industria,
                "etapa": "Diagnóstico"  # Asumido por defecto, puedes hacerlo dinámico si lo agregas al JSON
            })
    return leyes_planas

# Cargar las leyes en memoria
TODAS_LAS_LEYES = cargar_leyes_desde_json()

def obtener_leyes_por_industria_y_etapa(industria: str, etapa: str) -> list:
    return [
        ley for ley in TODAS_LAS_LEYES
        if ley["industria"].lower() == industria.lower()
        and ley["etapa"].lower() == etapa.lower()
    ]

def obtener_leyes_por_industria(industria: str) -> list:
    return [
        ley for ley in TODAS_LAS_LEYES
        if ley["industria"].lower() == industria.lower()
    ]

def obtener_todas_las_leyes() -> list:
    return TODAS_LAS_LEYES
