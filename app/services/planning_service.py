import json
from datetime import datetime
from pathlib import Path

from app.services.crq_service import (
    construir_nombre_archivo_crq,
    normalizar_certificaciones
)
from app.services.test_catalog_service import construir_nombre_test_set_display
from app.services.xray_service import (
    clonar_test_sets,
    generar_test_planning,
    generar_tests_para_objeto,
    obtener_reglas_summary
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASE_PATH = PROJECT_ROOT / "metadata" / "plannings"



def asegurar_directorio():

    BASE_PATH.mkdir(
        parents=True,
        exist_ok=True
    )



def obtener_path(crq_id):

    return BASE_PATH / f"{construir_nombre_archivo_crq(crq_id)}.json"



def cargar_planning_crq(crq_id):

    path = obtener_path(
        crq_id
    )

    if not path.exists():

        return None

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as archivo:

        data = json.load(
            archivo
        )

    return normalizar_planning_data(
        data,
        crq_id
    )



def guardar_planning_crq(
    crq_id,
    data
):

    asegurar_directorio()

    payload = normalizar_planning_data(
        data,
        crq_id
    )
    payload["updated_at"] = datetime.now().isoformat(timespec="seconds")

    with open(
        obtener_path(crq_id),
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            payload,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    return payload



def normalizar_planning_data(
    data,
    crq_id=None
):

    if isinstance(
        data,
        list
    ):

        data = {
            "plans": data
        }

    data = dict(
        data or {}
    )

    return {
        "crq": data.get(
            "crq",
            crq_id or ""
        ),
        "updated_at": data.get(
            "updated_at"
        ),
        "last_request": data.get(
            "last_request"
        ),
        "plans": list(
            data.get(
                "plans",
                []
            )
        )
    }



def obtener_o_generar_planning(
    crq,
    metadata=None,
    discovery=None
):

    crq_id = crq.get(
        "crq",
        ""
    )

    existente = cargar_planning_crq(
        crq_id
    ) if crq_id else None

    if existente and existente.get(
        "plans"
    ):

        return existente

    return {
        "crq": crq_id,
        "updated_at": None,
        "last_request": None,
        "plans": generar_test_planning(
            crq,
            metadata,
            discovery
        )
    }



def actualizar_planning_con_seleccion(
    crq,
    request_info,
    selected_objects,
    metadata=None,
    discovery=None
):

    planning_data = obtener_o_generar_planning(
        crq,
        metadata,
        discovery
    )

    plans = planning_data.get(
        "plans",
        []
    )

    certificaciones = normalizar_certificaciones(
        crq.get(
            "certificaciones",
            []
        )
    )

    if not certificaciones:

        certificaciones = [
            "sin_tipologia"
        ]

    integrated_plan = buscar_plan(
        plans,
        "integrado"
    )
    accepted_plan = buscar_plan(
        plans,
        "accepted"
    )
    regression_plan = buscar_plan(
        plans,
        "regresion"
    )

    if integrated_plan:

        sincronizar_test_sets_por_request(
            integrated_plan,
            crq,
            request_info,
            selected_objects
        )

        if accepted_plan:

            accepted_plan["test_sets"] = clonar_test_sets(
                integrated_plan.get(
                    "test_sets",
                    []
                )
            )
            accepted_plan["copied_from"] = "integrado"
            accepted_plan["last_sync"] = datetime.now().isoformat(timespec="seconds")

    elif accepted_plan:

        sincronizar_test_sets_por_request(
            accepted_plan,
            crq,
            request_info,
            selected_objects
        )

    if regression_plan:

        sincronizar_test_sets_por_request(
            regression_plan,
            crq,
            request_info,
            selected_objects
        )

    if not any([
        integrated_plan,
        accepted_plan,
        regression_plan
    ]):

        fallback = plans[0] if plans else None

        if fallback:

            sincronizar_test_sets_por_request(
                fallback,
                crq,
                request_info,
                selected_objects
            )

    planning_data["last_request"] = {
        "service_id": request_info.get("service_id"),
        "service_name": request_info.get("service_name"),
        "transaction_id": request_info.get("transaction_id"),
        "transaction_name": request_info.get("transaction_name"),
        "version_id": request_info.get("version_id"),
        "version_label": request_info.get("version_label"),
        "request_key": request_info.get("request_key"),
        "bruno_request_id": request_info.get("bruno_request_id"),
        "selected_objects": [
            objeto.get("path")
            for objeto in selected_objects
        ]
    }

    return guardar_planning_crq(
        crq.get(
            "crq",
            ""
        ),
        planning_data
    )



def buscar_plan(
    plans,
    tipo_id
):

    for plan in plans:

        if plan.get("tipo_id") == tipo_id:

            return plan

    return None



def sincronizar_test_sets_por_request(
    plan,
    crq,
    request_info,
    selected_objects
):

    request_key = request_info.get(
        "request_key"
    )

    restantes = []

    for test_set in plan.get(
        "test_sets",
        []
    ):

        source = test_set.get(
            "source",
            {}
        )

        if source.get("request_key") == request_key:

            continue

        if (
            selected_objects
            and test_set.get("path") == "General"
            and not source
        ):

            continue

        restantes.append(
            test_set
        )

    nuevos = [
        construir_test_set_desde_objeto(
            crq,
            request_info,
            objeto
        )
        for objeto in selected_objects
    ]

    plan["test_sets"] = restantes + nuevos
    plan["last_sync"] = datetime.now().isoformat(timespec="seconds")



def construir_test_set_desde_objeto(
    crq,
    request_info,
    objeto
):

    reglas = obtener_reglas_summary()

    path = objeto.get(
        "path",
        "General"
    )

    tests_candidatos = {
        test.get("field"): test
        for test in objeto.get(
            "tests",
            []
        )
        if test.get("field")
    }

    selected_fields = objeto.get(
        "selected_fields"
    )

    if selected_fields is None:

        selected_fields = [
            field
            for field in objeto.get(
                "fields",
                []
            )
        ]

    selected_fields = depurar_lista(
        selected_fields
    )

    if selected_fields:

        tests = []

        for field in selected_fields:

            test_catalogo = tests_candidatos.get(
                field,
                {}
            )

            tests.append(
                {
                    "nombre": reglas["test"].format(
                        objeto=path,
                        campo=field,
                        escenario="Base"
                    ),
                    "estado": (
                        "Reutilizado"
                        if test_catalogo.get("status") == "existente"
                        else "Diseñado"
                    ),
                    "field": field,
                    "jira_key": test_catalogo.get(
                        "jira_test",
                        ""
                    ),
                    "jira_url": test_catalogo.get(
                        "jira_url",
                        ""
                    )
                }
            )

    else:

        tests = generar_tests_para_objeto(
            path,
            [],
            reglas
        )

    coverage = objeto.get(
        "coverage",
        {}
    )

    return {
        "path": path,
        "nombre": construir_nombre_test_set_display(
            request_info.get(
                "service_name",
                crq.get(
                    "portafolio",
                    "General"
                )
            ),
            path,
            request_info.get(
                "version_label",
                ""
            ),
            request_info.get(
                "transaction_channel",
                ""
            )
        ),
        "source": {
            "request_key": request_info.get("request_key"),
            "service_id": request_info.get("service_id"),
            "service_name": request_info.get("service_name"),
            "transaction_id": request_info.get("transaction_id"),
            "transaction_name": request_info.get("transaction_name"),
            "transaction_libraries": list(
                request_info.get(
                    "transaction_libraries",
                    []
                )
            ),
            "transaction_channel": request_info.get(
                "transaction_channel",
                ""
            ),
            "repository_folder": request_info.get(
                "repository_folder",
                ""
            ),
            "version_id": request_info.get("version_id"),
            "version_label": request_info.get("version_label"),
            "bruno_request_id": request_info.get("bruno_request_id"),
            "bruno_request": request_info.get(
                "bruno_request",
                {}
            )
        },
        "coverage": {
            "exists": bool(
                coverage.get(
                    "exists"
                )
            ),
            "jira_test_set": coverage.get(
                "jira_test_set",
                ""
            ),
            "jira_url": coverage.get(
                "jira_url",
                ""
            )
        },
        "tests": tests
    }



def depurar_lista(valores):

    resultado = []

    for valor in valores or []:

        limpio = str(valor).strip()

        if limpio and limpio not in resultado:

            resultado.append(
                limpio
            )

    return resultado

