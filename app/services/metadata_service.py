import json
from pathlib import Path

from app.services.crq_service import construir_nombre_archivo_crq



PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASE_PATH = PROJECT_ROOT / "metadata" / "functional"



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



def cargar_metadata(
    crq_id
):


    path = obtener_path(
        crq_id
    )


    if not path.exists():

        return {
            "objects": {}
        }



    with open(
        path,
        "r",
        encoding="utf-8"
    ) as archivo:


        return json.load(
            archivo
        )



def guardar_metadata(
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



def comparar_metadata(
    discovery,
    metadata_actual
):


    resultado = {}



    objetos_existentes = (
        metadata_actual
        .get(
            "objects",
            {}
        )
    )



    for objeto in discovery.get(
        "objects",
        []
    ):


        path = objeto["path"]


        campos_detectados = (
            objeto["fields"]
        )


        metadata_objeto = (
            objetos_existentes
            .get(
                path,
                {}
            )
        )


        validados = (
            metadata_objeto
            .get(
                "validated_fields",
                []
            )
        )


        ignorados = (
            metadata_objeto
            .get(
                "ignored_fields",
                []
            )
        )



        nuevo = []


        sin_pruebas = []



        for campo in campos_detectados:


            if campo in validados:


                continue



            if campo in ignorados:


                sin_pruebas.append(
                    campo
                )


            else:


                nuevo.append(
                    campo
                )



        resultado[path] = {


            "validated":

            validados,



            "without_tests":

            sin_pruebas,



            "new":

            nuevo

        }



    return resultado