import json
from pathlib import Path

from app.services.crq_service import construir_nombre_archivo_crq



PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASE_PATH = PROJECT_ROOT / "metadata" / "discoveries"



def asegurar_directorio():


    if not BASE_PATH.exists():

        BASE_PATH.mkdir(
            parents=True,
            exist_ok=True
        )


def obtener_path(
    crq_id
):


    return BASE_PATH / f"{construir_nombre_archivo_crq(crq_id)}.json"



def guardar_discovery(
    crq_id,
    data
):


    asegurar_directorio()


    path = obtener_path(
        crq_id
    )


    with open(
        path,
        "w",
        encoding="utf-8"
    ) as archivo:


        json.dump(
            data,
            archivo,
            indent=4,
            ensure_ascii=False
        )



def cargar_discovery(
    crq_id
):


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


        return json.load(
            archivo
        )



def obtener_paths(
    objeto,
    path_actual=""
):


    resultados = []


    if isinstance(
        objeto,
        dict
    ):


        for key, value in objeto.items():


            nuevo_path = (
                f"{path_actual}.{key}"
                if path_actual
                else key
            )


            if isinstance(
                value,
                dict
            ):


                resultados.extend(
                    obtener_paths(
                        value,
                        nuevo_path
                    )
                )


            else:


                resultados.append(
                    nuevo_path
                )


    return resultados



def analizar_response(
    response_json
):


    campos = obtener_paths(
        response_json
    )


    objetos = {}


    for campo in campos:


        partes = campo.split(".")


        objeto = ".".join(
            partes[:-1]
        )


        atributo = partes[-1]


        if objeto not in objetos:

            objetos[objeto] = []


        objetos[objeto].append(
            atributo
        )



    resultado = []


    for objeto, campos in objetos.items():


        resultado.append(

            {

                "path": objeto,

                "fields": campos

            }

        )


    return {

        "objects": resultado

    }