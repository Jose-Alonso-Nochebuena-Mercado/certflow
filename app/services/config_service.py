import json
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = PROJECT_ROOT / "config"

BASE_PATH = PROJECT_ROOT / "config" / "xray"

UI_CONFIG_PATH = PROJECT_ROOT / "config" / "ui.json"

SERVICES_CATALOG_PATH = CONFIG_PATH / "services_catalog.json"

BRUNO_CONFIG_PATH = CONFIG_PATH / "bruno.json"


def cargar_json_desde_ruta(ruta):

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(archivo)


def guardar_json_en_ruta(
    ruta,
    data
):

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            data,
            archivo,
            indent=4,
            ensure_ascii=False
        )


def cargar_json(nombre):

    ruta = BASE_PATH / nombre

    return cargar_json_desde_ruta(
        ruta
    )



@lru_cache(maxsize=None)
def obtener_portafolios():

    data = cargar_json(
        "test_plan.json"
    )

    return data.get(
        "portafolio_apps",
        data.get(
            "Portafolio_apps",
            []
        )
    )



@lru_cache(maxsize=None)
def obtener_typology():

    data = cargar_json(
        "typology.json"
    )

    return data["types"]


def obtener_mapa_typology():

    return {
        tipo["id"]: tipo["nombre"]
        for tipo in obtener_typology()
    }


@lru_cache(maxsize=1)
def cargar_ui_config():

    if not UI_CONFIG_PATH.exists():

        return {}

    return cargar_json_desde_ruta(
        UI_CONFIG_PATH
    )


def guardar_ui_config(data):

    guardar_json_en_ruta(
        UI_CONFIG_PATH,
        data
    )

    cargar_ui_config.cache_clear()


@lru_cache(maxsize=1)
def obtener_catalogo_servicios():

    if not SERVICES_CATALOG_PATH.exists():

        return {
            "services": []
        }

    return cargar_json_desde_ruta(
        SERVICES_CATALOG_PATH
    )


def guardar_catalogo_servicios(data):

    guardar_json_en_ruta(
        SERVICES_CATALOG_PATH,
        data
    )

    obtener_catalogo_servicios.cache_clear()


@lru_cache(maxsize=1)
def cargar_bruno_config():

    if not BRUNO_CONFIG_PATH.exists():

        return {}

    return cargar_json_desde_ruta(
        BRUNO_CONFIG_PATH
    )


def guardar_bruno_config(data):

    guardar_json_en_ruta(
        BRUNO_CONFIG_PATH,
        data
    )

    cargar_bruno_config.cache_clear()


def obtener_jira_base_url():

    return cargar_ui_config().get(
        "jira_base_url",
        ""
    ).strip()


def obtener_configuracion_jira_automatizacion():

    config = dict(
        cargar_ui_config() or {}
    )

    return {
        "jira_base_url": str(
            config.get(
                "jira_base_url",
                ""
            ) or ""
        ).strip(),
        "jira_project_key": str(
            config.get(
                "jira_project_key",
                ""
            ) or ""
        ).strip(),
        "jira_project_name": str(
            config.get(
                "jira_project_name",
                ""
            ) or ""
        ).strip(),
        "jira_test_repository_path": str(
            config.get(
                "jira_test_repository_path",
                ""
            ) or ""
        ).strip(),
        "jira_browser_channel": str(
            config.get(
                "jira_browser_channel",
                "chrome"
            ) or "chrome"
        ).strip() or "chrome"
    }

