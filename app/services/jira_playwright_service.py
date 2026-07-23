import json
import importlib.util
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.services.config_service import (
    obtener_configuracion_jira_automatizacion
)
from app.services.crq_service import construir_nombre_archivo_crq


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUTOMATION_DIR = PROJECT_ROOT / "metadata" / "jira_automation"
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_jira_playwright.py"
LOCK_PATH = AUTOMATION_DIR / "playwright.lock"
STATE_PATH = AUTOMATION_DIR / "dummy_e2e_state.json"
LOCK_MAX_AGE_MINUTES = 20

ISSUE_TYPE_BY_ACTION = {
    "Crear Test": "Test",
    "Crear Test Set": "Test Set",
    "Crear Test Plan": "Test Plan",
    "Crear Test Execution": "Test Execution"
}

TYPOLOGY_BY_PLAN_NAME = {
    "Integration": {
        "label": "#integrado",
        "summary_tag": "Integrado"
    },
    "Acceptance": {
        "label": "#accepted",
        "summary_tag": "Aceptación"
    },
    "Regression": {
        "label": "#regresion",
        "summary_tag": "Regresión"
    }
}

DUMMY_CRQ = "CRQ-DUMMY"
DUMMY_DOMAIN = "Movimientos TDC"


class JiraPlaywrightConfigError(Exception):

    pass


class JiraPlaywrightRuntimeError(Exception):

    pass



def asegurar_directorio_automation():

    AUTOMATION_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def automation_ya_en_ejecucion():

    return LOCK_PATH.exists()


def lock_automation_obsoleto():

    if not LOCK_PATH.exists():

        return False

    try:

        data = json.loads(
            LOCK_PATH.read_text(
                encoding="utf-8"
            )
        )
        creado = datetime.fromisoformat(
            str(
                data.get(
                    "created_at",
                    ""
                )
            )
        )
        pid = int(
            data.get(
                "pid",
                0
            ) or 0
        )

    except Exception:

        return True

    if pid <= 0:

        return True

    lock_expirado = datetime.now() - creado > timedelta(
        minutes=LOCK_MAX_AGE_MINUTES
    )

    try:

        os.kill(
            pid,
            0
        )
        return False

    except OSError:

        return True

    except Exception:

        return lock_expirado


def limpiar_lock_obsoleto():

    if lock_automation_obsoleto():

        try:

            LOCK_PATH.unlink()

        except Exception:

            pass


def escribir_lock_automation(pid):

    asegurar_directorio_automation()
    LOCK_PATH.write_text(
        json.dumps(
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "pid": pid
            },
            ensure_ascii=False
        ),
        encoding="utf-8"
    )



def resolver_issue_type_desde_accion(accion):

    return ISSUE_TYPE_BY_ACTION.get(
        str(accion or "").strip(),
        str(accion or "").strip()
    )



def validar_configuracion_jira(config):

    faltantes = []

    if not config.get("jira_base_url"):

        faltantes.append("Jira base URL")

    if not config.get("jira_project_key"):

        faltantes.append("Project Key")

    if not config.get("jira_project_name"):

        faltantes.append("Project Name")

    if faltantes:

        raise JiraPlaywrightConfigError(
            "Falta configurar en Settings > Jira: "
            + ", ".join(faltantes)
        )



def formatear_fecha_jira(fecha):

    return fecha.strftime(
        "%d/%b/%y 09:00 AM"
    )


def normalizar_fecha_jira_desde_texto(valor):

    texto = str(
        valor or ""
    ).strip()

    if not texto:

        return ""

    for formato in [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%b/%y %I:%M %p"
    ]:

        try:

            fecha = datetime.strptime(
                texto,
                formato
            )

            return formatear_fecha_jira(
                fecha
            )

        except ValueError:

            continue

    return texto


def obtener_state_path_crq(crq_id):

    asegurar_directorio_automation()
    nombre = construir_nombre_archivo_crq(
        crq_id
    )
    return AUTOMATION_DIR / f"{nombre}_state.json"


def obtener_plan_base_compartido(planning_data):

    for tipo_id in [
        "integrado",
        "accepted"
    ]:

        for plan in planning_data.get(
            "plans",
            []
        ):

            if plan.get("tipo_id") == tipo_id:

                return plan

    planes = planning_data.get(
        "plans",
        []
    )
    return planes[0] if planes else None


def construir_identificador_test_set(test_set):

    payload = dict(
        test_set.get(
            "issue_payload",
            {}
        )
    )

    return "|".join(
        [
            str(test_set.get("path", "")).strip(),
            str(payload.get("summary", "")).strip(),
            str(payload.get("repository_path", "")).strip()
        ]
    )


def construir_identificador_test(test_set, test):

    payload = dict(
        test.get(
            "issue_payload",
            {}
        )
    )

    return "|".join(
        [
            str(test_set.get("path", "")).strip(),
            str(test.get("field", "")).strip(),
            str(payload.get("summary", "")).strip()
        ]
    )


def construir_payload_planning_desde_crq(
    crq,
    planning_data
):

    config = obtener_configuracion_jira_automatizacion()
    validar_configuracion_jira(
        config
    )

    crq_id = str(
        crq.get("crq", "")
    ).strip()

    if not crq_id:

        raise JiraPlaywrightRuntimeError(
            "El CRQ actual no tiene identificador para construir la automatización de Jira/Xray."
        )

    workflow = []
    test_step_ids = {}
    test_set_step_ids = {}
    base_plan = obtener_plan_base_compartido(
        planning_data
    )

    if base_plan:

        for test_set_index, test_set in enumerate(base_plan.get("test_sets", []), start=1):

            if not test_set.get("enabled", True):

                continue

            test_refs = []

            for test_index, test in enumerate(test_set.get("tests", []), start=1):

                field_name = str(
                    test.get("field", "")
                ).strip()

                if not field_name:

                    continue

                test_signature = construir_identificador_test(
                    test_set,
                    test
                )

                if test_signature in test_step_ids:

                    test_refs.append(
                        test_step_ids[test_signature]
                    )
                    continue

                test_payload = dict(
                    test.get("issue_payload", {})
                )
                step_id = f"test_{len(test_step_ids) + 1}"
                workflow.append(
                    {
                        "id": step_id,
                        "kind": "issue",
                        "issue": {
                            "type": "Test",
                            "summary": test_payload.get("summary", f"{crq_id} | Test {test_index}"),
                            "description": test_payload.get("description", ""),
                            "actions": test_payload.get("actions", test.get("actions", "")),
                            "repository_path": test_payload.get("repository_path", ""),
                            "auto_submit": True
                        }
                    }
                )
                test_step_ids[test_signature] = step_id
                test_refs.append(
                    step_id
                )

            test_set_signature = construir_identificador_test_set(
                test_set
            )

            if test_set_signature in test_set_step_ids:

                continue

            test_set_payload = dict(
                test_set.get("issue_payload", {})
            )
            step_id = f"test_set_{len(test_set_step_ids) + 1}"
            workflow.append(
                {
                    "id": step_id,
                    "kind": "issue",
                    "issue": {
                        "type": "Test Set",
                        "summary": test_set_payload.get("summary", f"{crq_id} | Test Set {test_set_index}"),
                        "description": test_set_payload.get("description", ""),
                        "repository_path": test_set_payload.get("repository_path", ""),
                        "test_key_refs": test_refs,
                        "auto_submit": True
                    }
                }
            )
            test_set_step_ids[test_set_signature] = step_id

    for plan_index, plan in enumerate(planning_data.get("plans", []), start=1):

        enabled_test_set_refs = []

        for test_set in plan.get("test_sets", []):

            if not test_set.get("enabled", True):

                continue

            signature = construir_identificador_test_set(
                test_set
            )
            ref = test_set_step_ids.get(
                signature
            )

            if ref and ref not in enabled_test_set_refs:

                enabled_test_set_refs.append(
                    ref
                )

        plan_payload = dict(
            plan.get("issue_payload", {})
        )

        workflow.append(
            {
                "id": f"test_plan_{plan_index}",
                "kind": "issue",
                "issue": {
                    "type": "Test Plan",
                    "summary": plan_payload.get("summary", f"[{crq_id}] {plan.get('tipo_nombre', 'Plan')}"),
                    "description": plan_payload.get("description", ""),
                    "typology_name": plan_payload.get("typology_name", plan.get("tipo_nombre", "")),
                    "begin_date": normalizar_fecha_jira_desde_texto(plan_payload.get("begin_date", "")),
                    "end_date": normalizar_fecha_jira_desde_texto(plan_payload.get("end_date", "")),
                    "associated_test_set_key_refs": enabled_test_set_refs,
                    "auto_submit": True
                }
            }
        )

    if not workflow:

        raise JiraPlaywrightRuntimeError(
            "No hay Tests, Test Sets o Test Plans listos para crear en Jira/Xray."
        )

    state_path = obtener_state_path_crq(
        crq_id
    )

    return {
        "mode": "planning_e2e",
        "source": "test_case_design",
        "browser_channel": config.get(
            "jira_browser_channel",
            "chrome"
        ),
        "start_url": config.get(
            "jira_base_url",
            ""
        ),
        "project": {
            "key": config.get(
                "jira_project_key",
                ""
            ),
            "name": config.get(
                "jira_project_name",
                ""
            )
        },
        "state_path": str(
            state_path
        ),
        "workflow": workflow
    }


def obtener_contexto_dummy():

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    hoy = datetime.now()
    hace_semana = hoy - timedelta(days=7)

    return {
        "timestamp": timestamp,
        "today": hoy,
        "week_ago": hace_semana,
        "crq": DUMMY_CRQ,
        "domain": DUMMY_DOMAIN
    }


def construir_summary_dummy_test(numero, contexto):

    return (
        f"[DUMMY] Test {numero} | "
        f"{contexto['domain']} | "
        f"{contexto['timestamp']}"
    )


def construir_summary_dummy_test_set(numero, contexto):

    suffix = f" {numero}" if str(numero).strip() else ""

    return (
        f"[DUMMY] Test Set{suffix} | "
        f"{contexto['domain']} | "
        f"{contexto['timestamp']}"
    )


def construir_summary_dummy_test_plan(
    typology_name,
    contexto
):

    summary_tag = TYPOLOGY_BY_PLAN_NAME.get(
        typology_name,
        {}
    ).get(
        "summary_tag",
        f"#{typology_name}"
    )

    return (
        f"{contexto['crq']} | "
        f"{summary_tag} | "
        f"{contexto['domain']} | "
        f"{contexto['timestamp']}"
    )


def cargar_estado_dummy_e2e():

    if not STATE_PATH.exists():

        return {}

    with open(
        STATE_PATH,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(
            archivo
        )


def obtener_test_set_keys_dummy():

    completed = dict(
        cargar_estado_dummy_e2e().get(
            "completed",
            {}
        )
    )
    keys = [
        completed.get(step_id, {}).get("jira_key", "")
        for step_id in (
            "test_set_1",
            "test_set_2"
        )
    ]

    keys = [
        key
        for key in keys
        if key
    ]

    if keys:

        return keys

    fallback = [
        data.get("jira_key", "")
        for data in completed.values()
        if data.get("type") == "Test Set" and data.get("jira_key")
    ]

    return fallback


def construir_issue_dummy(issue_type, repository_path):

    contexto = obtener_contexto_dummy()

    if issue_type == "Test Set":

        return {
            "type": issue_type,
            "summary": construir_summary_dummy_test_set(
                None,
                contexto
            ),
            "description": (
                "Test Set dummy generado desde el Home para validar la creación asistida en Jira/Xray.\n\n"
                "Incluye nombre y descripción de prueba para revisar la automatización antes de conectarla al flujo real."
            ),
            "labels": "",
            "repository_path": repository_path,
            "test_keys": [],
            "auto_submit": True
        }

    if issue_type == "Test Plan":

        typology_name = "Integration"
        test_set_keys = obtener_test_set_keys_dummy()

        return {
            "type": issue_type,
            "summary": construir_summary_dummy_test_plan(
                typology_name,
                contexto
            ),
            "description": (
                "Test Plan dummy generado desde el Home para validar la creación asistida en Jira/Xray.\n\n"
                f"Tipología: {typology_name}\n"
                "Se usará después como base para la integración con el flujo real por CRQ."
            ),
            "labels": "",
            "repository_path": "",
            "typology_name": typology_name,
            "begin_date": formatear_fecha_jira(
                contexto["week_ago"]
            ),
            "end_date": formatear_fecha_jira(
                contexto["today"]
            ),
            "associated_test_set_keys": test_set_keys,
            "auto_submit": True
        }

    return {
        "type": issue_type,
        "summary": (
            f"[DUMMY] {issue_type} de prueba | "
            f"{contexto['domain']} | "
            f"{contexto['timestamp']}"
        ),
        "description": (
            "Registro de prueba generado desde el Home de CertFlow para validar "
            "la automatización asistida con Playwright.\n\n"
            f"Issue Type: {issue_type}\n"
            "Origen: Botones temporales del Home\n"
            "Nota: este payload usa información dummy antes de conectar el flujo real "
            "de selección de objetos, campos y escenarios."
        ),
        "actions": (
            "1. Abrir el formulario Create de Jira.\n"
            "2. Seleccionar proyecto e issue type.\n"
            "3. Validar que el formulario quede listo para captura.\n"
            "4. Dejar el registro listo para revisión manual."
        ),
        "labels": "",
        "repository_path": repository_path,
        "auto_submit": False
    }


def construir_payload_dummy(issue_type):

    config = obtener_configuracion_jira_automatizacion()
    validar_configuracion_jira(
        config
    )

    issue_type = str(
        issue_type or "Test"
    ).strip() or "Test"
    repository_path = config.get(
        "jira_test_repository_path",
        ""
    )

    return {
        "mode": "assisted",
        "source": "home_dummy_buttons",
        "browser_channel": config.get(
            "jira_browser_channel",
            "chrome"
        ),
        "start_url": config.get(
            "jira_base_url",
            ""
        ),
        "project": {
            "key": config.get(
                "jira_project_key",
                ""
            ),
            "name": config.get(
                "jira_project_name",
                ""
            )
        },
        "issue": construir_issue_dummy(
            issue_type,
            repository_path
        )
    }


def construir_payload_dummy_e2e():

    config = obtener_configuracion_jira_automatizacion()
    validar_configuracion_jira(
        config
    )

    contexto = obtener_contexto_dummy()
    repository_path = config.get(
        "jira_test_repository_path",
        ""
    )

    return {
        "mode": "dummy_e2e",
        "source": "home_dummy_e2e",
        "browser_channel": config.get(
            "jira_browser_channel",
            "chrome"
        ),
        "start_url": config.get(
            "jira_base_url",
            ""
        ),
        "project": {
            "key": config.get(
                "jira_project_key",
                ""
            ),
            "name": config.get(
                "jira_project_name",
                ""
            )
        },
        "state_path": str(STATE_PATH),
        "workflow": [
            {
                "id": "test_1",
                "kind": "issue",
                "issue": {
                    "type": "Test",
                    "summary": construir_summary_dummy_test(
                        1,
                        contexto
                    ),
                    "description": "Test dummy 1 para validar el E2E completo de Jira/Xray.",
                    "actions": (
                        "1. Ejecutar flujo dummy.\n"
                        "2. Validar creación automática del Test."
                    ),
                    "labels": "",
                    "repository_path": repository_path,
                    "auto_submit": True
                }
            },
            {
                "id": "test_2",
                "kind": "issue",
                "issue": {
                    "type": "Test",
                    "summary": construir_summary_dummy_test(
                        2,
                        contexto
                    ),
                    "description": "Test dummy 2 para validar el E2E completo de Jira/Xray.",
                    "actions": (
                        "1. Ejecutar flujo dummy.\n"
                        "2. Validar creación automática del Test."
                    ),
                    "labels": "",
                    "repository_path": repository_path,
                    "auto_submit": True
                }
            },
            {
                "id": "test_set_1",
                "kind": "issue",
                "issue": {
                    "type": "Test Set",
                    "summary": construir_summary_dummy_test_set(
                        1,
                        contexto
                    ),
                    "description": "Test Set dummy 1 asociado al Test dummy 1.",
                    "labels": "",
                    "repository_path": repository_path,
                    "test_key_refs": [
                        "test_1"
                    ],
                    "auto_submit": True
                }
            },
            {
                "id": "test_set_2",
                "kind": "issue",
                "issue": {
                    "type": "Test Set",
                    "summary": construir_summary_dummy_test_set(
                        2,
                        contexto
                    ),
                    "description": "Test Set dummy 2 asociado al Test dummy 2.",
                    "labels": "",
                    "repository_path": repository_path,
                    "test_key_refs": [
                        "test_2"
                    ],
                    "auto_submit": True
                }
            },
            {
                "id": "test_plan_1",
                "kind": "issue",
                "issue": {
                    "type": "Test Plan",
                    "summary": construir_summary_dummy_test_plan(
                        "Integration",
                        contexto
                    ),
                    "description": "Test Plan dummy asociado a los tests creados en el flujo E2E.",
                    "labels": "",
                    "typology_name": "Integration",
                    "begin_date": formatear_fecha_jira(
                        contexto["week_ago"]
                    ),
                    "end_date": formatear_fecha_jira(
                        contexto["today"]
                    ),
                    "associated_test_set_key_refs": [
                        "test_set_1",
                        "test_set_2"
                    ],
                    "auto_submit": True
                }
            }
        ]
    }



def escribir_payload(payload):

    asegurar_directorio_automation()

    payload_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    ) + f"_{uuid4().hex[:8]}"
    path = AUTOMATION_DIR / f"{payload_id}.json"

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            payload,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    return path


def lanzar_automatizacion_jira(payload):

    if not SCRIPT_PATH.exists():

        raise JiraPlaywrightRuntimeError(
            f"No se encontró el runner de Playwright: {SCRIPT_PATH}"
        )

    if importlib.util.find_spec("playwright") is None:

        raise JiraPlaywrightRuntimeError(
            "Playwright no está instalado en este entorno. Ejecuta `pip install -r requirements.txt` y `python -m playwright install chrome`. La automatización usa un perfil de navegador separado, por lo que el login a Jira se hace una primera vez en esa ventana."
        )

    limpiar_lock_obsoleto()

    if automation_ya_en_ejecucion():

        raise JiraPlaywrightRuntimeError(
            "Ya hay una automatización de Jira/Playwright en ejecución o quedó un lock reciente. Cierra la ventana de automatización actual y vuelve a intentar en unos segundos."
        )

    payload_path = escribir_payload(
        payload
    )

    proceso = subprocess.Popen(
        [
            sys.executable,
            str(SCRIPT_PATH),
            str(payload_path)
        ],
        cwd=str(PROJECT_ROOT)
    )

    escribir_lock_automation(
        proceso.pid
    )

    return payload_path


def lanzar_creacion_dummy_desde_home(accion):

    issue_type = resolver_issue_type_desde_accion(
        accion
    )

    payload = construir_payload_dummy(
        issue_type
    )

    return lanzar_automatizacion_jira(
        payload
    )


def lanzar_dummy_e2e_desde_home():

    payload = construir_payload_dummy_e2e()

    return lanzar_automatizacion_jira(
        payload
    )


def construir_payload_dummy_test_plan_only():

    config = obtener_configuracion_jira_automatizacion()
    validar_configuracion_jira(
        config
    )

    test_set_keys = obtener_test_set_keys_dummy()

    if not test_set_keys:

        raise JiraPlaywrightRuntimeError(
            "No se encontraron Test Set dummy previos en el estado persistido. Primero ejecuta la prueba E2E completa para crear los Test y Test Set base."
        )

    contexto = obtener_contexto_dummy()

    return {
        "mode": "dummy_test_plan_only",
        "source": "home_dummy_test_plan_only",
        "browser_channel": config.get(
            "jira_browser_channel",
            "chrome"
        ),
        "start_url": config.get(
            "jira_base_url",
            ""
        ),
        "project": {
            "key": config.get(
                "jira_project_key",
                ""
            ),
            "name": config.get(
                "jira_project_name",
                ""
            )
        },
        "workflow": [
            {
                "kind": "issue",
                "issue": {
                    "type": "Test Plan",
                    "summary": construir_summary_dummy_test_plan(
                        "Integration",
                        contexto
                    ),
                    "description": (
                        "Test Plan dummy relanzado desde el Home para validar la creación asistida en Jira/Xray.\n\n"
                        "Este flujo reutiliza únicamente los Test Set ya creados previamente."
                    ),
                    "labels": "",
                    "typology_name": "Integration",
                    "begin_date": formatear_fecha_jira(
                        contexto["week_ago"]
                    ),
                    "end_date": formatear_fecha_jira(
                        contexto["today"]
                    ),
                    "associated_test_set_keys": test_set_keys,
                    "auto_submit": True
                }
            }
        ]
    }


def lanzar_dummy_test_plan_desde_home():

    payload = construir_payload_dummy_test_plan_only()

    return lanzar_automatizacion_jira(
        payload
    )
