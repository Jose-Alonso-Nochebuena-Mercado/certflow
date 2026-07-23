from app.services.config_service import (
    cargar_json,
    obtener_jira_base_url,
    obtener_mapa_typology
)

from app.services.crq_service import (
    normalizar_certificaciones
)


def obtener_reglas_summary():

    return cargar_json(
        "reglas/summary.json"
    )



def obtener_enlace_jira(crq_id):

    base_url = obtener_jira_base_url()

    if not base_url:

        return None

    if "{crq}" in base_url:

        return base_url.format(
            crq=crq_id
        )

    return f"{base_url.rstrip('/')}/browse/{crq_id}"



def generar_test_planning(
    crq,
    metadata=None,
    discovery=None
):

    reglas = obtener_reglas_summary()

    mapa_tipos = obtener_mapa_typology()

    certificaciones = normalizar_certificaciones(
        crq.get(
            "certificaciones",
            []
        )
    )

    objetos = obtener_objetos_fuente(
        metadata,
        discovery
    )

    if not certificaciones:

        certificaciones = [
            "sin_tipologia"
        ]

    resultado = []
    base_integracion = None

    for certificacion in certificaciones:

        nombre_tipo = mapa_tipos.get(
            certificacion,
            certificacion.replace("_", " ").title()
        )

        plan = {
            "tipo_id": certificacion,
            "tipo_nombre": nombre_tipo,
            "estrategia": obtener_estrategia_plan(
                certificacion,
                base_integracion is not None
            ),
            "nombre": reglas["test_plan"].format(
                sdatool=crq.get("sdatool", "-"),
                crq=crq.get("crq", "-"),
                tipo=nombre_tipo
            ),
            "jira_url": obtener_enlace_jira(
                crq.get("crq", "")
            ),
            "test_sets": []
        }

        if certificacion == "accepted" and base_integracion:

            plan["test_sets"] = clonar_test_sets(
                base_integracion
            )

            resultado.append(plan)
            continue

        for objeto in objetos:

            path = objeto["path"]
            campos = objeto.get(
                "fields",
                []
            )

            test_set = {
                "path": path,
                "nombre": reglas["test_set"].format(
                    aplicacion=crq.get("portafolio", "General"),
                    objeto=path
                ),
                "tests": generar_tests_para_objeto(
                    path,
                    campos,
                    reglas
                )
            }

            plan["test_sets"].append(
                test_set
            )

        resultado.append(
            plan
        )

        if certificacion == "integrado":

            base_integracion = plan["test_sets"]

    return resultado


def obtener_estrategia_plan(
    certificacion,
    existe_base_integracion
):

    if certificacion == "integrado":

        return (
            "Plan de pruebas de afectación. "
            "Incluye los test sets y tests definidos para la certificación."
        )

    if certificacion == "accepted":

        if existe_base_integracion:

            return (
                "Copia de la base de Integración. "
                "Debe validarse si el usuario quiere agregar o quitar test sets o tests."
            )

        return (
            "Plan de Aceptación sin base previa de Integración. "
            "Debe definirse manualmente."
        )

    if certificacion == "regresion":

        return (
            "Plan separado para No afectación / Regresión. "
            "No reutiliza automáticamente la estructura de afectación."
        )

    return "Plan generado a partir de la configuración actual del CRQ."


def clonar_test_sets(test_sets):

    resultado = []

    for test_set in test_sets:

        clon = {
            key: value
            for key, value in test_set.items()
            if key != "tests"
        }

        clon["tests"] = [
            {
                **test,
                "estado": "Pendiente de validación"
            }
            for test in test_set.get(
                "tests",
                []
            )
        ]

        resultado.append(
            clon
        )

    return resultado



def obtener_objetos_fuente(
    metadata,
    discovery
):

    if metadata and metadata.get("objects"):

        objetos = []

        for path, datos in metadata.get(
            "objects",
            {}
        ).items():

            campos = []
            campos.extend(
                datos.get(
                    "validated_fields",
                    []
                )
            )
            campos.extend(
                datos.get(
                    "ignored_fields",
                    []
                )
            )

            objetos.append(
                {
                    "path": path,
                    "fields": depurar_campos(campos)
                }
            )

        return objetos

    if discovery and discovery.get("objects"):

        return [
            {
                "path": objeto.get(
                    "path",
                    "General"
                ),
                "fields": depurar_campos(
                    objeto.get(
                        "fields",
                        []
                    )
                )
            }
            for objeto in discovery.get(
                "objects",
                []
            )
        ]

    return [
        {
            "path": "General",
            "fields": []
        }
    ]



def generar_tests_para_objeto(
    objeto,
    campos,
    reglas
):

    if not campos:

        return [
            {
                "nombre": "Sin tests asociados todavía",
                "estado": "Pendiente de definición"
            }
        ]

    tests = []

    for campo in campos:

        tests.append(
            {
                "nombre": reglas["test"].format(
                    objeto=objeto,
                    campo=campo,
                    escenario="Base"
                ),
                "estado": "Diseñado"
            }
        )

    return tests



def depurar_campos(campos):

    resultado = []

    for campo in campos:

        valor = str(campo).strip()

        if valor and valor not in resultado:

            resultado.append(
                valor
            )

    return resultado

