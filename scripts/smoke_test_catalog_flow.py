from app.services.planning_service import obtener_o_generar_planning
from app.services.test_catalog_service import construir_descubrimiento_catalogo


def main():

    crq = {
        "crq": "SMOKE-CRQ",
        "sdatool": "SDATOOL-SMOKE",
        "descripcion": "Validación rápida de catálogo local",
        "portafolio": "Movimientos",
        "fecha_instalacion": "2026-07-22",
        "certificaciones": [
            "integrado",
            "accepted",
            "regresion"
        ]
    }

    planning = obtener_o_generar_planning(
        crq
    )
    discovery = construir_descubrimiento_catalogo(
        "movimientos",
        "detalle",
        "v2"
    )

    print("CRQ:", crq["crq"])
    print("Planes base:", len(planning.get("plans", [])))
    print("Request:", discovery["request"].get("bruno_request_id"))
    print("Objetos detectados:", len(discovery["discovery"].get("objects", [])))


if __name__ == "__main__":

    main()

