import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import requests

from app.services.config_service import (
    PROJECT_ROOT,
    cargar_bruno_config
)


class BrunoExecutionError(Exception):

    pass


HTTP_METHOD_BLOCKS = (
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head"
)



def obtener_configuracion_bruno():

    config = dict(
        cargar_bruno_config() or {}
    )

    command_template = str(
        config.get(
            "command_template",
            ""
        )
    ).strip()

    response_mode = str(
        config.get(
            "response_mode",
            ""
        )
    ).strip().lower()

    if not response_mode:

        response_mode = inferir_response_mode(
            command_template
        )

    return {
        "enabled": bool(
            config.get(
                "enabled",
                False
            )
        ),
        "preferred_mode": str(
            config.get(
                "preferred_mode",
                "auto"
            )
        ).strip().lower() or "auto",
        "collection_root": str(
            config.get(
                "collection_root",
                "collections"
            )
        ).strip() or "collections",
        "command_template": command_template,
        "response_mode": response_mode,
        "timeout_seconds": int(
            config.get(
                "timeout_seconds",
                90
            )
        ),
        "verify_ssl": bool(
            config.get(
                "verify_ssl",
                True
            )
        ),
        "ca_bundle_path": str(
            config.get(
                "ca_bundle_path",
                ""
            )
        ).strip(),
        "allow_mock_fallback": bool(
            config.get(
                "allow_mock_fallback",
                True
            )
        )
    }


def inferir_response_mode(command_template):

    if "{output_file}" in str(
        command_template or ""
    ):

        return "output_file"

    return "stdout_json"



def resolver_ruta_request(request_info):

    bruno_request = request_info.get(
        "bruno_request",
        {}
    )
    relative_file = str(
        bruno_request.get(
            "file",
            ""
        )
    ).strip()

    if not relative_file:

        return None

    path = Path(
        relative_file
    )

    if path.is_absolute():

        return path

    candidate_project = PROJECT_ROOT / path

    if candidate_project.exists():

        return candidate_project

    collection_root = str(
        obtener_configuracion_bruno().get(
            "collection_root",
            ""
        )
    ).strip()

    if collection_root:

        candidate_collection = Path(
            collection_root
        ) / path

        if candidate_collection.exists():

            return candidate_collection

    return candidate_project



def construir_contexto_bruno(request_info):

    bruno_request = request_info.get(
        "bruno_request",
        {}
    )
    file_abs = resolver_ruta_request(
        request_info
    )

    output_file = Path(
        tempfile.gettempdir()
    ) / f"certflow_bruno_{request_info.get('request_key', 'request').replace('|', '_')}.json"

    return {
        "service_id": request_info.get(
            "service_id",
            ""
        ),
        "service_name": request_info.get(
            "service_name",
            ""
        ),
        "transaction_id": request_info.get(
            "transaction_id",
            ""
        ),
        "transaction_name": request_info.get(
            "transaction_name",
            ""
        ),
        "version_id": request_info.get(
            "version_id",
            ""
        ) or "",
        "version_label": request_info.get(
            "version_label",
            ""
        ) or "",
        "request_key": request_info.get(
            "request_key",
            ""
        ),
        "collection": str(
            bruno_request.get(
                "collection",
                ""
            )
        ).strip(),
        "folder": str(
            bruno_request.get(
                "folder",
                ""
            )
        ).strip(),
        "request": str(
            bruno_request.get(
                "request",
                ""
            )
        ).strip(),
        "logical_path": str(
            bruno_request.get(
                "logical_path",
                ""
            )
        ).strip(),
        "file": str(
            bruno_request.get(
                "file",
                ""
            )
        ).strip(),
        "file_abs": str(file_abs) if file_abs else "",
        "output_file": str(output_file),
        "project_root": str(PROJECT_ROOT)
    }



def puede_ejecutar_bruno_real(request_info):

    config = obtener_configuracion_bruno()

    if not config.get("enabled"):

        return False, "Bruno real está deshabilitado en `config/bruno.json`."

    request_path = resolver_ruta_request(
        request_info
    )

    if not request_path:

        return False, "La request seleccionada no define archivo `.bru`."

    if not request_path.exists():

        return False, f"No existe el archivo Bruno esperado: {request_path}"

    return True, ""



def ejecutar_request_bruno_real(request_info):

    config = obtener_configuracion_bruno()
    disponible, motivo = puede_ejecutar_bruno_real(
        request_info
    )

    if not disponible:

        raise BrunoExecutionError(
            motivo
        )

    contexto = construir_contexto_bruno(
        request_info
    )

    errores = []

    try:

        response_json = ejecutar_request_desde_bru(
            request_info,
            contexto,
            config
        )

        return {
            "mode": "real",
            "executed_at": None,
            "request": request_info,
            "response": response_json,
            "runtime": {
                "strategy": "direct_bru",
                "request_file": contexto.get(
                    "file_abs",
                    ""
                )
            }
        }

    except BrunoExecutionError as error:

        errores.append(
            str(error)
        )

    if not config.get("command_template"):

        raise BrunoExecutionError(
            errores[0]
        )

    command = config["command_template"].format(
        **contexto
    )

    try:

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=config["timeout_seconds"],
            cwd=PROJECT_ROOT,
            check=False
        )

    except subprocess.TimeoutExpired as error:

        errores.append(
            f"Timeout ejecutando Bruno real por comando: {error}"
        )
        raise BrunoExecutionError(
            " | ".join(errores)
        ) from error
    except OSError as error:

        errores.append(
            f"No se pudo ejecutar el comando de Bruno: {error}"
        )
        raise BrunoExecutionError(
            " | ".join(errores)
        ) from error

    if result.returncode != 0:

        detalle = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"

        errores.append(
            f"Falló Bruno real por comando: {detalle}"
        )
        raise BrunoExecutionError(
            " | ".join(errores)
        )


def ejecutar_request_bruno_preview(
    request_info,
    body_override_text=None
):

    config = obtener_configuracion_bruno()
    disponible, motivo = puede_ejecutar_bruno_real(
        request_info
    )

    if not disponible:

        raise BrunoExecutionError(
            motivo
        )

    contexto = construir_contexto_bruno(
        request_info
    )

    return ejecutar_request_desde_bru(
        request_info,
        contexto,
        config,
        body_override_text=body_override_text,
        include_http_metadata=True
    )

    response_json = resolver_response_real(
        config,
        contexto,
        result.stdout
    )

    return {
        "mode": "real",
        "executed_at": None,
        "request": request_info,
        "response": response_json,
        "runtime": {
            "command": command,
            "response_mode": config.get(
                "response_mode",
                "stdout_json"
            )
        }
    }



def resolver_response_real(
    config,
    contexto,
    stdout_text
):

    response_mode = config.get(
        "response_mode",
        "stdout_json"
    )

    if response_mode == "output_file":

        output_path = Path(
            contexto["output_file"]
        )

        if not output_path.exists():

            raise BrunoExecutionError(
                f"Bruno finalizó pero no generó output file: {output_path}"
            )

        with open(
            output_path,
            "r",
            encoding="utf-8"
        ) as archivo:

            return json.load(
                archivo
            )

    payload = stdout_text.strip()

    if not payload:

        raise BrunoExecutionError(
            "Bruno real no devolvió contenido JSON en stdout."
        )

    try:

        return json.loads(
            payload
        )

    except json.JSONDecodeError as error:

        raise BrunoExecutionError(
            "El stdout de Bruno no contiene JSON válido. "
            "Revisa `response_mode` o ajusta `command_template` para emitir solo la respuesta JSON."
        ) from error


def ejecutar_request_desde_bru(
    request_info,
    contexto,
    config,
    body_override_text=None,
    include_http_metadata=False
):

    request_path = resolver_ruta_request(
        request_info
    )

    if not request_path or not request_path.exists():

        raise BrunoExecutionError(
            "No se encontró el archivo `.bru` para ejecución directa."
        )

    definicion = parsear_archivo_bru(
        request_path
    )

    method = definicion.get(
        "method",
        "GET"
    ).upper()
    url = resolver_valor_bru(
        definicion.get(
            "url",
            ""
        ),
        "URL"
    )

    headers = {
        key: resolver_valor_bru(
            value,
            f"header `{key}`"
        )
        for key, value in definicion.get(
            "headers",
            {}
        ).items()
    }

    params = {
        key: resolver_valor_bru(
            value,
            f"query `{key}`"
        )
        for key, value in definicion.get(
            "query",
            {}
        ).items()
    }

    body_info = definicion.get(
        "body",
        {}
    )
    body_text = str(
        body_override_text
    ) if body_override_text is not None else (
        resolver_valor_bru(
            body_info.get(
                "content",
                ""
            ),
            "body"
        ) if body_info else ""
    )

    request_kwargs = {
        "method": method,
        "url": url,
        "headers": headers,
        "params": params,
        "timeout": config.get(
            "timeout_seconds",
            90
        ),
        "verify": construir_verify_ssl(
            config
        )
    }

    body_type = body_info.get(
        "type",
        ""
    ) if body_info else ""

    if body_text:

        if body_type == "json":

            try:

                request_kwargs["json"] = json.loads(
                    body_text
                )

            except json.JSONDecodeError:

                request_kwargs["data"] = body_text
                headers.setdefault(
                    "Content-Type",
                    "application/json"
                )

        else:

            request_kwargs["data"] = body_text

    try:

        response = requests.request(
            **request_kwargs
        )

    except requests.exceptions.SSLError as error:

        raise BrunoExecutionError(
            "La request llegó al endpoint pero falló la validación SSL/TLS. "
            "Revisa si necesitas desactivar verificación SSL temporalmente o configurar un CA bundle corporativo en Bruno. "
            f"Detalle: {error}"
        ) from error
    except requests.RequestException as error:

        raise BrunoExecutionError(
            f"No fue posible ejecutar la request real desde `.bru`: {error}"
        ) from error

    if response.status_code >= 400:

        detalle = response.text[:400].strip() or response.reason or f"HTTP {response.status_code}"

        raise BrunoExecutionError(
            f"La request respondió con error HTTP {response.status_code}: {detalle}"
        )

    try:

        response_json = response.json()

        if include_http_metadata:

            return {
                "status_code": response.status_code,
                "reason": response.reason,
                "headers": dict(response.headers),
                "elapsed_ms": int(response.elapsed.total_seconds() * 1000),
                "response": response_json
            }

        return response_json

    except ValueError as error:

        raise BrunoExecutionError(
            "La respuesta del servicio no es JSON válido. "
            "CertFlow necesita una respuesta JSON para construir el mapa de objetos."
        ) from error


def parsear_archivo_bru(request_path):

    try:

        content = request_path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        content = request_path.read_text(
            encoding="utf-8-sig"
        )

    bloques = extraer_bloques_bru(
        content
    )
    method_block = next(
        (
            bloque for bloque in HTTP_METHOD_BLOCKS
            if bloque in bloques
        ),
        None
    )

    if not method_block:

        raise BrunoExecutionError(
            f"El archivo `.bru` no define un bloque HTTP reconocible en `{request_path.name}`."
        )

    request_config = parsear_bloque_key_value(
        bloques.get(
            method_block,
            ""
        )
    )
    url = request_config.get(
        "url",
        ""
    ).strip()

    if not url:

        raise BrunoExecutionError(
            f"El archivo `.bru` no contiene URL en el bloque `{method_block}`."
        )

    return {
        "method": method_block,
        "url": url,
        "headers": parsear_bloque_key_value(
            bloques.get(
                "headers",
                ""
            )
        ),
        "query": parsear_bloque_key_value(
            bloques.get(
                "query",
                ""
            )
        ),
        "body": extraer_body_bru(
            bloques
        )
    }


def extraer_bloques_bru(content):

    bloques = {}
    nombre_actual = None
    buffer = []
    nivel = 0

    for line in content.splitlines():

        stripped = line.strip()

        if nombre_actual is None:

            match = re.match(
                r"^([\w:-]+)\s*\{$",
                stripped
            )

            if not match:

                continue

            nombre_actual = match.group(1).lower()
            nivel = 1
            buffer = []
            continue

        apertura = line.count("{")
        cierre = line.count("}")
        siguiente_nivel = nivel + apertura - cierre

        if not (
            stripped == "}"
            and siguiente_nivel == 0
        ):

            buffer.append(
                line
            )

        nivel = siguiente_nivel

        if nivel == 0:

            bloques[nombre_actual] = "\n".join(
                buffer
            ).strip()
            nombre_actual = None
            buffer = []

    return bloques


def parsear_bloque_key_value(raw_block):

    resultado = {}

    for line in str(
        raw_block or ""
    ).splitlines():

        stripped = line.strip()

        if not stripped or stripped.startswith("#"):

            continue

        if ":" not in stripped:

            continue

        key, value = stripped.split(
            ":",
            1
        )
        resultado[key.strip()] = value.strip()

    return resultado


def extraer_body_bru(bloques):

    for nombre, contenido in bloques.items():

        if not nombre.startswith("body"):

            continue

        if nombre == "body:json":

            return {
                "type": "json",
                "content": str(contenido or "").strip()
            }

        return {
            "type": nombre.split(":", 1)[1] if ":" in nombre else "raw",
            "content": str(contenido or "").strip()
        }

    return {
        "type": "",
        "content": ""
    }


def resolver_valor_bru(valor, contexto):

    texto = str(
        valor or ""
    ).strip()

    def replace_dynamic(match):

        variable = str(
            match.group(1) or ""
        ).strip()

        if not variable.startswith("$"):

            return match.group(0)

        return resolver_variable_dinamica_bruno(
            variable,
            contexto
        )

    texto = re.sub(
        r"\{\{\s*([^}]+?)\s*\}\}",
        replace_dynamic,
        texto
    )

    variables = re.findall(
        r"\{\{\s*([^}]+?)\s*\}\}",
        texto
    )

    if variables:

        listado = ", ".join(
            sorted(set(variables))
        )

        raise BrunoExecutionError(
            f"La request `.bru` contiene variables sin resolver en {contexto}: {listado}."
        )

    return texto


def resolver_variable_dinamica_bruno(variable, contexto):

    normalized = str(
        variable or ""
    ).strip().lower()

    if normalized in ("$guid", "$uuid"):

        return str(
            uuid4()
        )

    if normalized == "$timestamp":

        return str(
            int(time.time())
        )

    if normalized in ("$timestampms", "$timestamp_ms"):

        return str(
            int(time.time() * 1000)
        )

    if normalized in ("$isotimestamp", "$iso_timestamp"):

        return datetime.now(
            timezone.utc
        ).isoformat()

    if normalized in ("$date", "$today"):

        return datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%d")

    raise BrunoExecutionError(
        f"La variable dinámica de Bruno `{variable}` no está soportada todavía en {contexto}."
    )


def construir_verify_ssl(config):

    ca_bundle_path = str(
        config.get(
            "ca_bundle_path",
            ""
        )
    ).strip()

    if ca_bundle_path:

        return ca_bundle_path

    return bool(
        config.get(
            "verify_ssl",
            True
        )
    )


