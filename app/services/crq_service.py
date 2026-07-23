import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

METADATA_DIR = PROJECT_ROOT / "metadata"

CRQ_FILE = METADATA_DIR / "crqs.json"

INVALID_FILENAME_CHARS = set('<>:"/\\|?*')



def normalizar_certificaciones(certificaciones):

    if not certificaciones:

        return []


    normalizadas = []


    for certificacion in certificaciones:

        if isinstance(
            certificacion,
            dict
        ):

            valor = str(
                certificacion.get(
                    "tipo",
                    ""
                )
            ).strip()

        else:

            valor = str(
                certificacion
            ).strip()


        if valor:

            normalizadas.append(
                valor
            )


    return normalizadas


def obtener_crq_id_normalizado(crq_id):

    return str(
        crq_id or ""
    ).strip().upper()


def contiene_caracteres_invalidos_crq(crq_id):

    valor = obtener_crq_id_normalizado(
        crq_id
    )

    if not valor:

        return False

    if valor[-1] in {" ", "."}:

        return True

    return any(
        caracter in INVALID_FILENAME_CHARS
        or ord(caracter) < 32
        for caracter in valor
    )


def construir_nombre_archivo_crq(crq_id):

    valor = obtener_crq_id_normalizado(
        crq_id
    ) or "SIN_CRQ"

    sanitizado = "".join(
        "_"
        if caracter in INVALID_FILENAME_CHARS
        or ord(caracter) < 32
        else caracter
        for caracter in valor
    ).rstrip(" .")

    return sanitizado or "SIN_CRQ"


def normalizar_crq_data(data):

    data = dict(
        data or {}
    )

    data["certificaciones"] = normalizar_certificaciones(
        data.get(
            "certificaciones",
            []
        )
    )

    return data



def cargar_crqs():

    if not CRQ_FILE.exists():

        return {}


    with open(
        CRQ_FILE,
        "r",
        encoding="utf-8"
    ) as archivo:

        crqs = json.load(
            archivo
        )


    return {
        crq_id: normalizar_crq_data(data)
        for crq_id, data in crqs.items()
    }



def guardar_crqs(data):

    data_normalizada = {
        crq_id: normalizar_crq_data(crq_data)
        for crq_id, crq_data in data.items()
    }

    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        CRQ_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            data_normalizada,
            archivo,
            indent=4,
            ensure_ascii=False
        )



def obtener_crqs():

    return cargar_crqs()



def existe_crq(crq_id):

    crqs = cargar_crqs()

    return crq_id in crqs



def guardar_crq(
    crq_id,
    data
):

    crqs = cargar_crqs()


    crqs[crq_id] = normalizar_crq_data(
        data
    )


    guardar_crqs(
        crqs
    )

def listar_crqs():

    return obtener_crqs()

def eliminar_crq(
    crq_id
):


    crqs = cargar_crqs()


    if crq_id in crqs:

        del crqs[crq_id]


        guardar_crqs(
            crqs
        )


        return True


    return False