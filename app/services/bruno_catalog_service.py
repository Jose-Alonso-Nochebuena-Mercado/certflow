from pathlib import Path

from app.services.bruno_runner_service import obtener_configuracion_bruno


class BrunoCatalogError(Exception):

    pass



def obtener_bruno_collection_root():

    config = obtener_configuracion_bruno()
    collection_root = str(
        config.get(
            "collection_root",
            ""
        )
    ).strip()

    if not collection_root:

        raise BrunoCatalogError(
            "No hay ruta de colecciones configurada en Bruno."
        )

    root_path = Path(
        collection_root
    )

    if not root_path.is_absolute():

        raise BrunoCatalogError(
            "La ruta de colecciones Bruno debe ser absoluta para poder explorar carpetas fuera del workspace."
        )

    if not root_path.exists():

        raise BrunoCatalogError(
            f"No existe la ruta configurada para Bruno: {root_path}"
        )

    if not root_path.is_dir():

        raise BrunoCatalogError(
            f"La ruta configurada no es una carpeta válida: {root_path}"
        )

    return root_path



def listar_bruno_tree(
    max_depth=4
):

    root_path = obtener_bruno_collection_root()

    return {
        "root": str(root_path),
        "nodes": construir_nodos(
            root_path,
            root_path,
            depth=0,
            max_depth=max_depth
        )
    }



def construir_nodos(
    current_path,
    root_path,
    depth,
    max_depth
):

    children = []

    if depth > max_depth:

        return children

    try:

        entries = sorted(
            current_path.iterdir(),
            key=lambda path: (
                not path.is_dir(),
                path.name.lower()
            )
        )

    except OSError as error:

        raise BrunoCatalogError(
            f"No fue posible leer la carpeta Bruno `{current_path}`: {error}"
        ) from error

    for entry in entries:

        relative_path = entry.relative_to(
            root_path
        )

        node = {
            "name": entry.name,
            "relative_path": relative_path.as_posix(),
            "absolute_path": str(entry),
            "type": "directory" if entry.is_dir() else "file"
        }

        if entry.is_file() and entry.suffix.lower() == ".bru":

            node["is_request"] = True

        if entry.is_dir() and depth < max_depth:

            node["children"] = construir_nodos(
                entry,
                root_path,
                depth + 1,
                max_depth
            )

        children.append(
            node
        )

    return children

