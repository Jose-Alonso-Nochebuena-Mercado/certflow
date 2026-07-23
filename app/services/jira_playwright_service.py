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
        "summary_tag": "#Integration"
    },
    "Acceptance": {
        "label": "#accepted",
        "summary_tag": "#Acceptance"
    },
    "Regression": {
        "label": "#regresion",
        "summary_tag": "#Regression"
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

    try:

        os.kill(
            pid,
            0
        )
        return False

    except OSError:

        return True

    return datetime.now() - creado > timedelta(
        minutes=LOCK_MAX_AGE_MINUTES
    )


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
            "labels": TYPOLOGY_BY_PLAN_NAME[typology_name]["label"],
            "repository_path": "",
            "typology_name": typology_name,
            "begin_date": formatear_fecha_jira(
                contexto["week_ago"]
            ),
            "end_date": formatear_fecha_jira(
                contexto["today"]
            ),
            "associated_test_set_keys": [],
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
                    "labels": TYPOLOGY_BY_PLAN_NAME["Integration"]["label"],
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
                    "labels": TYPOLOGY_BY_PLAN_NAME["Integration"]["label"],
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

