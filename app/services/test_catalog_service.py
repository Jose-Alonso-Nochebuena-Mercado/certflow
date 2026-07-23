import json
import re
from datetime import datetime
from pathlib import Path

from app.services.bruno_runner_service import (
    BrunoExecutionError,
    ejecutar_request_bruno_real,
    obtener_configuracion_bruno
)
from app.services.config_service import (
    guardar_catalogo_servicios,
    obtener_catalogo_servicios
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

COVERAGE_PATH = PROJECT_ROOT / "metadata" / "coverage_catalog.json"


class CatalogoServiciosError(Exception):

    pass



def cargar_inventario_cobertura():

    if not COVERAGE_PATH.exists():

        return {
            "entries": []
        }

    with open(
        COVERAGE_PATH,
        "r",
        encoding="utf-8"
    ) as archivo:

        data = json.load(
            archivo
        )

    return {
        "entries": normalizar_entries_cobertura(
            data.get(
                "entries",
                []
            )
        )
    }



def normalizar_entries_cobertura(entries):

    resultado = []

    for entry in entries or []:

        tests = []

        for test in entry.get(
            "tests",
            []
        ):

            campo = str(
                test.get(
                    "field",
                    ""
                )
            ).strip()

            if not campo:

                continue

            tests.append(
                {
                    "field": campo,
                    "jira_test": str(
                        test.get(
                            "jira_test",
                            ""
                        )
                    ).strip(),
                    "jira_url": str(
                        test.get(
                            "jira_url",
                            ""
                        )
                    ).strip()
                }
            )

        resultado.append(
            {
                "service_id": str(
                    entry.get(
                        "service_id",
                        ""
                    )
                ).strip(),
                "transaction_id": str(
                    entry.get(
                        "transaction_id",
                        ""
                    )
                ).strip(),
                "version_id": normalizar_version_id(
                    entry.get(
                        "version_id"
                    )
                ),
                "object_path": str(
                    entry.get(
                        "object_path",
                        ""
                    )
                ).strip(),
                "jira_test_set": str(
                    entry.get(
                        "jira_test_set",
                        ""
                    )
                ).strip(),
                "jira_url": str(
                    entry.get(
                        "jira_url",
                        ""
                    )
                ).strip(),
                "tests": tests
            }
        )

    return resultado



def obtener_servicios():

    return obtener_catalogo_servicios().get(
        "services",
        []
    )


def slugify_catalog_id(valor):

    base = re.sub(
        r"[^a-z0-9]+",
        "_",
        str(valor or "").strip().lower()
    ).strip("_")

    return base or "item"


def construir_bruno_request(
    collection="",
    folder="",
    request="",
    file="",
    logical_path=""
):

    data = {
        "collection": str(collection).strip(),
        "folder": str(folder).strip(),
        "request": str(request).strip(),
        "file": str(file).strip(),
        "logical_path": str(logical_path).strip()
    }

    return {
        key: value
        for key, value in data.items()
        if value
    }


def humanizar_catalog_label(valor):

    limpio = str(
        valor or ""
    ).replace("_", " ").replace("-", " ").strip()

    return limpio.title() if limpio else ""


def normalizar_librerias(librerias):

    if librerias is None:

        return []

    if isinstance(
        librerias,
        str
    ):

        candidatos = re.split(
            r"[,;\n]+",
            librerias
        )

    else:

        candidatos = librerias

    resultado = []

    for libreria in candidatos:

        valor = str(
            libreria or ""
        ).strip()

        if valor and valor not in resultado:

            resultado.append(
                valor
            )

    return resultado


def normalizar_texto_simple(valor):

    return str(
        valor or ""
    ).strip()


def formatear_object_path_display(path):

    segmentos = [
        compactar_segmento_display(segmento)
        for segmento in str(
            path or ""
        ).split(".")
        if str(segmento).strip()
    ]

    return " > ".join(segmentos) if segmentos else "General"


def compactar_segmento_display(segmento, max_length=18):

    texto = str(
        segmento or ""
    ).strip()

    if len(texto) <= max_length:

        return texto

    return f"{texto[:max_length - 2]}.."


def construir_nombre_test_set_display(
    service_name,
    object_path,
    version_label="",
    channel=""
):

    partes = []
    channel = normalizar_texto_simple(
        channel
    )

    if channel:

        partes.append(
            f"[{channel}]"
        )

    partes.append(
        normalizar_texto_simple(
            service_name
        ) or "Servicio"
    )

    if normalizar_texto_simple(version_label):

        partes.append(
            normalizar_texto_simple(
                version_label
            )
        )

    partes.append(
        formatear_object_path_display(
            object_path
        )
    )

    return " | ".join(partes)


def detectar_version_desde_path(partes_folder):

    if not partes_folder:

        return None

    ultima = str(
        partes_folder[-1]
    ).strip()

    if re.fullmatch(
        r"v\d+",
        ultima,
        flags=re.IGNORECASE
    ):

        return ultima

    return None


def inferir_importacion_desde_bru(relative_path, absolute_path):

    relative_path = str(
        relative_path or ""
    ).strip().replace("\\", "/")

    if not relative_path:

        raise CatalogoServiciosError(
            "La request Bruno no tiene ruta relativa para inferir catálogo."
        )

    path = Path(
        relative_path
    )

    if path.suffix.lower() != ".bru":

        raise CatalogoServiciosError(
            "Solo se pueden importar archivos `.bru`."
        )

    parts = list(
        path.parts
    )

    if len(parts) < 2:

        raise CatalogoServiciosError(
            "La ruta de Bruno debe incluir al menos colección y request."
        )

    collection = parts[0]
    folder_parts = parts[1:-1]
    version_id = detectar_version_desde_path(
        folder_parts
    )

    if version_id:

        transaction_parts = folder_parts[:-1]
        version_label = version_id.upper()

    else:

        transaction_parts = folder_parts
        version_label = ""

    transaction_seed = transaction_parts[-1] if transaction_parts else path.stem
    service_id = slugify_catalog_id(
        collection
    )
    service_name = humanizar_catalog_label(
        collection
    )
    transaction_id = slugify_catalog_id(
        transaction_seed
    )
    transaction_name = humanizar_catalog_label(
        transaction_seed
    )

    logical_path = relative_path[:-4] if relative_path.lower().endswith(".bru") else relative_path

    return {
        "service_id": service_id,
        "service_name": service_name or collection,
        "transaction_id": transaction_id,
        "transaction_name": transaction_name or path.stem,
        "libraries": "",
        "version_id": slugify_catalog_id(version_id) if version_id else "",
        "version_label": version_label,
        "collection": collection,
        "folder": "/".join(folder_parts),
        "request": path.stem,
        "file": str(absolute_path).strip(),
        "logical_path": logical_path,
        "mock_response": ""
    }


def importar_request_bru_catalogo(
    relative_path,
    absolute_path,
    service_name,
    service_id,
    transaction_name,
    transaction_id,
    version_label="",
    version_id="",
    libraries=None,
    channel="",
    repository_folder="",
    mock_response=""
):

    service_name = str(service_name).strip()
    transaction_name = str(transaction_name).strip()

    if not service_name:

        raise CatalogoServiciosError(
            "Debes indicar el nombre del servicio."
        )

    if not transaction_name:

        raise CatalogoServiciosError(
            "Debes indicar el nombre de la transacción."
        )

    service_id = slugify_catalog_id(
        service_id or service_name
    )
    transaction_id = slugify_catalog_id(
        transaction_id or transaction_name
    )
    version_label = str(
        version_label or ""
    ).strip()
    version_id = slugify_catalog_id(
        version_id or version_label
    ) if version_label else ""
    transaction_libraries = normalizar_librerias(
        libraries
    )
    transaction_channel = normalizar_texto_simple(
        channel
    )
    transaction_repository_folder = normalizar_texto_simple(
        repository_folder
    )

    relative_parts = Path(
        str(relative_path).replace("\\", "/")
    ).parts
    collection_name = relative_parts[0] if relative_parts else service_id

    bruno_request = construir_bruno_request(
        collection=collection_name,
        folder="/".join(relative_parts[1:-1]),
        request=Path(relative_path).stem,
        file=str(absolute_path).strip(),
        logical_path=str(relative_path).replace("\\", "/")[:-4]
    )

    catalogo = dict(
        obtener_catalogo_servicios()
    )
    servicios = list(
        catalogo.get(
            "services",
            []
        )
    )

    servicio = next(
        (
            item for item in servicios
            if item.get("id") == service_id
        ),
        None
    )

    if not servicio:

        servicio = {
            "id": service_id,
            "name": service_name,
            "transactions": []
        }
        servicios.append(
            servicio
        )

    else:

        servicio["name"] = service_name

    transacciones = list(
        servicio.get(
            "transactions",
            []
        )
    )

    transaccion = next(
        (
            item for item in transacciones
            if item.get("id") == transaction_id
        ),
        None
    )

    if version_label:

        if not transaccion:

            transaccion = {
                "id": transaction_id,
                "name": transaction_name,
                "versions": [],
                "libraries": transaction_libraries,
                "channel": transaction_channel,
                "repository_folder": transaction_repository_folder
            }
            transacciones.append(
                transaccion
            )

        else:

            transaccion["name"] = transaction_name
            transaccion["libraries"] = transaction_libraries
            transaccion["channel"] = transaction_channel
            transaccion["repository_folder"] = transaction_repository_folder

        versiones = list(
            transaccion.get(
                "versions",
                []
            )
        )

        version = next(
            (
                item for item in versiones
                if item.get("id") == version_id
            ),
            None
        )

        if not version:

            version = {
                "id": version_id,
                "label": version_label
            }
            versiones.append(
                version
            )

        version["label"] = version_label
        version["bruno_request"] = bruno_request

        if str(mock_response).strip():

            version["mock_response"] = str(mock_response).strip()

        transaccion["versions"] = versiones

    else:

        if not transaccion:

            transaccion = {
                "id": transaction_id,
                "name": transaction_name,
                "libraries": transaction_libraries,
                "channel": transaction_channel,
                "repository_folder": transaction_repository_folder
            }
            transacciones.append(
                transaccion
            )

        transaccion["name"] = transaction_name
        transaccion["libraries"] = transaction_libraries
        transaccion["channel"] = transaction_channel
        transaccion["repository_folder"] = transaction_repository_folder
        transaccion["bruno_request"] = bruno_request

        if str(mock_response).strip():

            transaccion["mock_response"] = str(mock_response).strip()

    servicio["transactions"] = transacciones
    guardar_catalogo_servicios(
        {
            "services": servicios
        }
    )

    return {
        "service_id": service_id,
        "transaction_id": transaction_id,
        "version_id": version_id,
        "version_label": version_label,
        "libraries": transaction_libraries,
        "channel": transaction_channel,
        "repository_folder": transaction_repository_folder,
        "request": bruno_request
    }


def agregar_servicio_catalogo(
    service_name,
    service_id=None
):

    service_name = str(service_name).strip()

    if not service_name:

        raise CatalogoServiciosError(
            "Debes capturar el nombre del servicio"
        )

    service_id = slugify_catalog_id(
        service_id or service_name
    )

    catalogo = obtener_catalogo_servicios()
    servicios = list(
        catalogo.get(
            "services",
            []
        )
    )

    if any(
        servicio.get("id") == service_id
        for servicio in servicios
    ):

        raise CatalogoServiciosError(
            f"Ya existe un servicio con id `{service_id}`"
        )

    servicios.append(
        {
            "id": service_id,
            "name": service_name,
            "transactions": []
        }
    )

    guardar_catalogo_servicios(
        {
            "services": servicios
        }
    )

    return service_id


def agregar_transaccion_catalogo(
    service_id,
    transaction_name,
    transaction_id=None,
    bruno_request=None,
    libraries=None,
    channel="",
    repository_folder="",
    mock_response=""
):

    servicio = buscar_servicio(
        service_id
    )

    if not servicio:

        raise CatalogoServiciosError(
            f"Servicio no encontrado: {service_id}"
        )

    transaction_name = str(transaction_name).strip()

    if not transaction_name:

        raise CatalogoServiciosError(
            "Debes capturar el nombre de la transacción"
        )

    transaction_id = slugify_catalog_id(
        transaction_id or transaction_name
    )
    transaction_libraries = normalizar_librerias(
        libraries
    )
    transaction_channel = normalizar_texto_simple(
        channel
    )
    transaction_repository_folder = normalizar_texto_simple(
        repository_folder
    )

    catalogo = obtener_catalogo_servicios()
    servicios = list(
        catalogo.get(
            "services",
            []
        )
    )

    for service in servicios:

        if service.get("id") != service_id:

            continue

        transacciones = list(
            service.get(
                "transactions",
                []
            )
        )

        if any(
            transaccion.get("id") == transaction_id
            for transaccion in transacciones
        ):

            raise CatalogoServiciosError(
                f"Ya existe una transacción con id `{transaction_id}` en `{service_id}`"
            )

        nueva_transaccion = {
            "id": transaction_id,
            "name": transaction_name,
            "libraries": transaction_libraries,
            "channel": transaction_channel,
            "repository_folder": transaction_repository_folder
        }

        if bruno_request:

            nueva_transaccion["bruno_request"] = bruno_request

        if str(mock_response).strip():

            nueva_transaccion["mock_response"] = str(mock_response).strip()

        transacciones.append(
            nueva_transaccion
        )
        service["transactions"] = transacciones
        break

    guardar_catalogo_servicios(
        {
            "services": servicios
        }
    )

    return transaction_id


def agregar_version_catalogo(
    service_id,
    transaction_id,
    version_label,
    version_id=None,
    bruno_request=None,
    libraries=None,
    channel="",
    repository_folder="",
    mock_response=""
):

    transaccion = buscar_transaccion(
        service_id,
        transaction_id
    )

    if not transaccion:

        raise CatalogoServiciosError(
            f"Transacción no encontrada: {transaction_id}"
        )

    version_label = str(version_label).strip()

    if not version_label:

        raise CatalogoServiciosError(
            "Debes capturar la etiqueta de la versión"
        )

    version_id = slugify_catalog_id(
        version_id or version_label
    )
    transaction_libraries = normalizar_librerias(
        libraries
    )
    transaction_channel = normalizar_texto_simple(
        channel
    )
    transaction_repository_folder = normalizar_texto_simple(
        repository_folder
    )

    catalogo = obtener_catalogo_servicios()
    servicios = list(
        catalogo.get(
            "services",
            []
        )
    )

    for service in servicios:

        if service.get("id") != service_id:

            continue

        for transaccion_catalogo in service.get(
            "transactions",
            []
        ):

            if transaccion_catalogo.get("id") != transaction_id:

                continue

            versiones = list(
                transaccion_catalogo.get(
                    "versions",
                    []
                )
            )

            if any(
                version.get("id") == version_id
                for version in versiones
            ):

                raise CatalogoServiciosError(
                    f"Ya existe la versión `{version_id}` en `{transaction_id}`"
                )

            nueva_version = {
                "id": version_id,
                "label": version_label
            }

            if bruno_request:

                nueva_version["bruno_request"] = bruno_request

            if transaction_libraries:

                transaccion_catalogo["libraries"] = transaction_libraries

            if transaction_channel:

                transaccion_catalogo["channel"] = transaction_channel

            if transaction_repository_folder:

                transaccion_catalogo["repository_folder"] = transaction_repository_folder

            if str(mock_response).strip():

                nueva_version["mock_response"] = str(mock_response).strip()

            versiones.append(
                nueva_version
            )
            transaccion_catalogo["versions"] = versiones
            break

    guardar_catalogo_servicios(
        {
            "services": servicios
        }
    )

    return version_id



def buscar_servicio(servicio_id):

    for servicio in obtener_servicios():

        if servicio.get("id") == servicio_id:

            return servicio

    return None



def obtener_transacciones(servicio_id):

    servicio = buscar_servicio(
        servicio_id
    )

    if not servicio:

        return []

    return servicio.get(
        "transactions",
        []
    )



def buscar_transaccion(
    servicio_id,
    transaccion_id
):

    for transaccion in obtener_transacciones(
        servicio_id
    ):

        if transaccion.get("id") == transaccion_id:

            return transaccion

    return None



def obtener_versiones(
    servicio_id,
    transaccion_id
):

    transaccion = buscar_transaccion(
        servicio_id,
        transaccion_id
    )

    if not transaccion:

        return []

    return transaccion.get(
        "versions",
        []
    )



def normalizar_version_id(version_id):

    valor = str(
        version_id or ""
    ).strip()

    return valor or None



def construir_request_key(
    servicio_id,
    transaccion_id,
    version_id=None
):

    partes = [
        str(servicio_id).strip(),
        str(transaccion_id).strip()
    ]

    version_normalizada = normalizar_version_id(
        version_id
    )

    if version_normalizada:

        partes.append(
            version_normalizada
        )

    return "|".join(partes)



def resolver_request(
    servicio_id,
    transaccion_id,
    version_id=None
):

    servicio = buscar_servicio(
        servicio_id
    )

    if not servicio:

        raise CatalogoServiciosError(
            f"Servicio no encontrado: {servicio_id}"
        )

    transaccion = buscar_transaccion(
        servicio_id,
        transaccion_id
    )

    if not transaccion:

        raise CatalogoServiciosError(
            f"Transacción no encontrada: {transaccion_id}"
        )

    versiones = transaccion.get(
        "versions",
        []
    )

    if versiones:

        version_normalizada = normalizar_version_id(
            version_id
        )

        if not version_normalizada:

            raise CatalogoServiciosError(
                "La transacción seleccionada requiere versión"
            )

        version = next(
            (
                item for item in versiones
                if item.get("id") == version_normalizada
            ),
            None
        )

        if not version:

            raise CatalogoServiciosError(
                f"Versión no encontrada: {version_normalizada}"
            )

        request_data = dict(
            version.get(
                "bruno_request",
                {}
            )
        )
        mock_response = version.get(
            "mock_response"
        )
        version_label = version.get(
            "label",
            version_normalizada.upper()
        )

    else:

        version = None
        version_normalizada = None
        version_label = None
        request_data = dict(
            transaccion.get(
                "bruno_request",
                {}
            )
        )
        mock_response = transaccion.get(
            "mock_response"
        )

    logical_path = str(
        request_data.get(
            "logical_path",
            ""
        )
    ).strip()

    return {
        "request_key": construir_request_key(
            servicio_id,
            transaccion_id,
            version_normalizada
        ),
        "service_id": servicio_id,
        "service_name": servicio.get(
            "name",
            servicio_id
        ),
        "transaction_id": transaccion_id,
        "transaction_name": transaccion.get(
            "name",
            transaccion_id
        ),
        "transaction_libraries": normalizar_librerias(
            transaccion.get(
                "libraries",
                []
            )
        ),
        "transaction_channel": normalizar_texto_simple(
            transaccion.get(
                "channel",
                ""
            )
        ),
        "repository_folder": normalizar_texto_simple(
            transaccion.get(
                "repository_folder",
                ""
            )
        ),
        "version_id": version_normalizada,
        "version_label": version_label,
        "has_versions": bool(versiones),
        "bruno_request": request_data,
        "bruno_request_id": logical_path or request_data.get(
            "request",
            ""
        ),
        "mock_response": mock_response
    }



def ejecutar_request_catalogo(
    servicio_id,
    transaccion_id,
    version_id=None
):

    request_info = resolver_request(
        servicio_id,
        transaccion_id,
        version_id
    )

    bruno_config = obtener_configuracion_bruno()
    preferred_mode = bruno_config.get(
        "preferred_mode",
        "auto"
    )

    if preferred_mode != "mock_only":

        try:

            ejecucion_real = ejecutar_request_bruno_real(
                request_info
            )

            ejecucion_real["executed_at"] = datetime.now().isoformat(timespec="seconds")

            return ejecucion_real

        except BrunoExecutionError as error:

            if preferred_mode == "real_only" or not bruno_config.get(
                "allow_mock_fallback",
                True
            ):

                raise CatalogoServiciosError(
                    str(error)
                ) from error

            return ejecutar_request_mock(
                request_info,
                mode="mock_fallback",
                fallback_reason=str(error)
            )

    return ejecutar_request_mock(
        request_info
    )


def ejecutar_request_mock(
    request_info,
    mode="mock",
    fallback_reason=""
):

    mock_response = request_info.get(
        "mock_response"
    )

    if not mock_response:

        raise CatalogoServiciosError(
            "La request seleccionada no tiene mock configurado"
        )

    mock_path = PROJECT_ROOT / mock_response

    if not mock_path.exists():

        raise CatalogoServiciosError(
            f"No se encontró el mock configurado: {mock_response}"
        )

    with open(
        mock_path,
        "r",
        encoding="utf-8"
    ) as archivo:

        response_json = json.load(
            archivo
        )

    return {
        "mode": mode,
        "executed_at": datetime.now().isoformat(timespec="seconds"),
        "request": request_info,
        "response": response_json,
        "fallback_reason": fallback_reason
    }



def construir_descubrimiento_catalogo(
    servicio_id,
    transaccion_id,
    version_id=None
):

    ejecucion = ejecutar_request_catalogo(
        servicio_id,
        transaccion_id,
        version_id
    )

    return {
        **ejecucion,
        "discovery": mapear_respuesta_json(
            ejecucion["response"],
            ejecucion["request"]
        )
    }



def mapear_respuesta_json(
    response_json,
    request_info=None
):

    entries = cargar_inventario_cobertura().get(
        "entries",
        []
    )

    nodos = recolectar_nodos_json(
        response_json
    )

    objetos = []

    for nodo in ordenar_nodos(
        nodos
    ):

        coverage = buscar_cobertura(
            entries,
            request_info,
            nodo["path"]
        )

        tests = construir_tests_candidatos(
            nodo.get(
                "fields",
                []
            ),
            coverage
        )

        objetos.append(
            {
                "path": nodo["path"],
                "kind": nodo["kind"],
                "depth": calcular_depth(
                    nodo["path"]
                ),
                "fields": nodo.get(
                    "fields",
                    []
                ),
                "children": nodo.get(
                    "children",
                    []
                ),
                "field_count": len(
                    nodo.get(
                        "fields",
                        []
                    )
                ),
                "child_count": len(
                    nodo.get(
                        "children",
                        []
                    )
                ),
                "coverage": {
                    "exists": bool(coverage),
                    "jira_test_set": (
                        coverage.get(
                            "jira_test_set",
                            ""
                        )
                        if coverage else ""
                    ),
                    "jira_url": (
                        coverage.get(
                            "jira_url",
                            ""
                        )
                        if coverage else ""
                    ),
                    "reused_tests": len(
                        [
                            test for test in tests
                            if test["status"] == "existente"
                        ]
                    ),
                    "new_tests": len(
                        [
                            test for test in tests
                            if test["status"] == "nuevo"
                        ]
                    )
                },
                "tests": tests
            }
        )

    return {
        "request": request_info,
        "objects": objetos
    }



def buscar_cobertura(
    entries,
    request_info,
    object_path
):

    if not request_info:

        return None

    service_id = request_info.get(
        "service_id"
    )
    transaction_id = request_info.get(
        "transaction_id"
    )
    version_id = normalizar_version_id(
        request_info.get(
            "version_id"
        )
    )

    candidatos = []

    for entry in entries:

        if entry.get("service_id") != service_id:

            continue

        if entry.get("transaction_id") != transaction_id:

            continue

        if entry.get("object_path") != object_path:

            continue

        entry_version = normalizar_version_id(
            entry.get("version_id")
        )

        if entry_version == version_id:

            return entry

        if entry_version is None:

            candidatos.append(
                entry
            )

    return candidatos[0] if candidatos else None



def construir_tests_candidatos(
    fields,
    coverage
):

    coverage_tests = {
        test["field"]: test
        for test in (
            coverage.get(
                "tests",
                []
            )
            if coverage else []
        )
    }

    resultado = []

    for field in fields:

        coverage_test = coverage_tests.get(
            field
        )

        resultado.append(
            {
                "field": field,
                "status": (
                    "existente"
                    if coverage_test
                    else "nuevo"
                ),
                "jira_test": (
                    coverage_test.get(
                        "jira_test",
                        ""
                    )
                    if coverage_test else ""
                ),
                "jira_url": (
                    coverage_test.get(
                        "jira_url",
                        ""
                    )
                    if coverage_test else ""
                )
            }
        )

    return resultado



def ordenar_nodos(nodos):

    return sorted(
        nodos,
        key=lambda item: (
            calcular_depth(
                item["path"]
            ),
            item["path"]
        )
    )



def calcular_depth(path):

    if not path:

        return 0

    return path.count(".") + path.count("[]")



def recolectar_nodos_json(response_json):

    nodos = {}
    root_fields = []

    def asegurar_nodo(
        path,
        kind
    ):

        nodo = nodos.setdefault(
            path,
            {
                "path": path,
                "kind": kind,
                "fields": [],
                "children": []
            }
        )

        if not nodo.get("kind"):

            nodo["kind"] = kind

        return nodo

    def visit_dict(
        value,
        path=""
    ):

        nodo = asegurar_nodo(
            path,
            "object"
        ) if path else None

        for key, child in value.items():

            if isinstance(
                child,
                dict
            ):

                child_path = f"{path}.{key}" if path else key

                if nodo:

                    nodo["children"].append(
                        child_path
                    )

                visit_dict(
                    child,
                    child_path
                )

            elif isinstance(
                child,
                list
            ):

                child_path = f"{path}.{key}[]" if path else f"{key}[]"

                if nodo:

                    nodo["children"].append(
                        child_path
                    )

                visit_list(
                    child,
                    child_path
                )

            else:

                if nodo:

                    nodo["fields"].append(
                        key
                    )

                else:

                    root_fields.append(
                        key
                    )

    def visit_list(
        value,
        path
    ):

        nodo = asegurar_nodo(
            path or "items[]",
            "array"
        )

        if not value:

            return

        for item in value:

            if isinstance(
                item,
                dict
            ):

                for key, child in item.items():

                    if isinstance(
                        child,
                        dict
                    ):

                        child_path = f"{path}.{key}"
                        nodo["children"].append(
                            child_path
                        )
                        visit_dict(
                            child,
                            child_path
                        )

                    elif isinstance(
                        child,
                        list
                    ):

                        child_path = f"{path}.{key}[]"
                        nodo["children"].append(
                            child_path
                        )
                        visit_list(
                            child,
                            child_path
                        )

                    else:

                        nodo["fields"].append(
                            key
                        )

            elif isinstance(
                item,
                list
            ):

                child_path = f"{path}[]"
                nodo["children"].append(
                    child_path
                )
                visit_list(
                    item,
                    child_path
                )

            else:

                nodo["fields"].append(
                    "value"
                )

    if isinstance(
        response_json,
        dict
    ):

        visit_dict(
            response_json
        )

    elif isinstance(
        response_json,
        list
    ):

        visit_list(
            response_json,
            "items[]"
        )

    else:

        nodos["root"] = {
            "path": "root",
            "kind": "value",
            "fields": ["value"],
            "children": []
        }

    if root_fields:

        root_node = asegurar_nodo(
            "root",
            "object"
        )
        root_node["fields"].extend(
            root_fields
        )

    return [
        {
            **nodo,
            "fields": deduplicar(
                nodo.get(
                    "fields",
                    []
                )
            ),
            "children": deduplicar(
                nodo.get(
                    "children",
                    []
                )
            )
        }
        for nodo in nodos.values()
        if nodo.get("path")
    ]



def deduplicar(valores):

    resultado = []

    for valor in valores:

        limpio = str(valor).strip()

        if limpio and limpio not in resultado:

            resultado.append(
                limpio
            )

    return resultado

