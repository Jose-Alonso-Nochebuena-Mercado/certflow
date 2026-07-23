import customtkinter as ctk

from app.services.crq_service import normalizar_certificaciones
from app.services.discovery_service import cargar_discovery
from app.services.metadata_service import cargar_metadata
from app.services.planning_service import actualizar_planning_con_seleccion
from app.services.test_catalog_service import (
    CatalogoServiciosError,
    agregar_servicio_catalogo,
    agregar_transaccion_catalogo,
    agregar_version_catalogo,
    actualizar_repository_folder_catalogo,
    construir_bruno_request,
    construir_descubrimiento_catalogo,
    obtener_servicios,
    obtener_transacciones,
    obtener_versiones,
    resolver_request
)
from app.services.config_service import obtener_mapa_typology
from app.ui.components.message_box import MessageBox
from app.ui.pages.base_page import BasePage
from app.ui.theme.colors import (
    ACCENT_SOFT,
    BACKGROUND,
    BORDER,
    PRIMARY,
    PRIMARY_LIGHT,
    PRIMARY_SOFT,
    SECONDARY_HOVER,
    SURFACE,
    SURFACE_ALT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_SOFT
)
from app.ui.theme.dimensions import PAGE_HORIZONTAL_PADDING
from app.ui.theme.styles import SECONDARY_BUTTON, SOFT_CARD_STYLE
from app.ui.theme.typography import BODY, SMALL, SUBTITLE, TITLE, get_font


SIN_OPCIONES = "Sin opciones"
SIN_TRANSACCIONES = "Sin transacciones"
NO_APLICA = "No aplica"
SIN_SERVICIOS = "Sin servicios configurados"


class AddTestsPage(BasePage):


    def __init__(
        self,
        parent,
        app,
        crq=None
    ):

        self.crq = crq or {}
        self.metadata_actual = {
            "objects": {}
        }
        self.discovery_actual = None
        self.catalog_services = obtener_servicios()
        self.discovery_result = None
        self.request_info = None
        self.object_states = {}
        self.object_tree_state = {}
        self.service_lookup = {}
        self.transaction_lookup = {}
        self.version_lookup = {}
        self.auto_execute_enabled = False
        self.last_request_key = None
        self.last_execution_result = None
        self.repository_path_input = None

        super().__init__(
            parent,
            app
        )


    def build(self):

        self.configure(
            fg_color=BACKGROUND
        )

        self.cargar_contexto()
        self.crear_ui()
        self.inicializar_catalogo()


    def cargar_contexto(self):

        crq_id = self.crq.get(
            "crq",
            ""
        )

        if not crq_id:

            return

        self.metadata_actual = cargar_metadata(
            crq_id
        )
        self.discovery_actual = cargar_discovery(
            crq_id
        )


    def crear_ui(self):

        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        self.content.pack(
            fill="both",
            expand=True,
            padx=0,
            pady=0
        )

        self.crear_hero()
        self.crear_selector_request()
        self.crear_paneles_resultado()
        self.crear_footer()


    def crear_hero(self):

        hero = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        hero.pack(
            fill="x",
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(24, 12)
        )

        titulo = ctk.CTkLabel(
            hero,
            text="Añadir tests",
            font=get_font(TITLE),
            text_color=PRIMARY
        )

        titulo.pack()

        subtitulo = ctk.CTkLabel(
            hero,
            text=(
                f"CRQ activo: {self.crq.get('crq', 'Sin seleccionar')} · "
                "Selecciona una request real de Bruno y decide qué nodos del JSON se convertirán en test sets."
            ),
            font=get_font(BODY),
            text_color=TEXT_SECONDARY,
            wraplength=980,
            justify="center"
        )

        subtitulo.pack(
            pady=(8, 0)
        )


    def crear_selector_request(self):

        card = ctk.CTkFrame(
            self.content,
            **SOFT_CARD_STYLE
        )

        card.pack(
            fill="x",
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(0, 12)
        )

        contenido = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        contenido.pack(
            fill="x",
            padx=24,
            pady=22
        )

        grid = ctk.CTkFrame(
            contenido,
            fg_color="transparent"
        )

        grid.pack(
            fill="x"
        )

        for columna in range(4):

            grid.grid_columnconfigure(
                columna,
                weight=1,
                uniform="selectors"
            )

        self.service_combo = self.crear_combo_selector(
            grid,
            0,
            "1. Servicio",
            command=self.on_service_change
        )

        self.transaction_combo = self.crear_combo_selector(
            grid,
            1,
            "2. Transacción",
            command=self.on_transaction_change
        )

        self.version_combo = self.crear_combo_selector(
            grid,
            2,
            "3. Versión",
            command=self.on_version_change
        )

        acciones = ctk.CTkFrame(
            grid,
            fg_color="transparent"
        )

        acciones.grid(
            row=0,
            column=3,
            sticky="nsew",
            padx=(8, 0)
        )

        ayuda = ctk.CTkLabel(
            acciones,
            text=(
                "La request se ejecuta automáticamente al cambiar servicio, "
                "transacción o versión."
            ),
            font=get_font(SMALL),
            text_color=TEXT_MUTED,
            wraplength=200,
            justify="left"
        )

        ayuda.pack(
            anchor="w",
            pady=(24, 0)
        )

        self.request_preview = ctk.CTkLabel(
            contenido,
            text="Selecciona una combinación del catálogo para ver la request asociada.",
            font=get_font(BODY),
            text_color=TEXT_PRIMARY,
            justify="left",
            wraplength=980
        )

        self.request_preview.pack(
            anchor="w",
            pady=(16, 0)
        )

        repository_frame = ctk.CTkFrame(
            contenido,
            fg_color="transparent"
        )

        repository_frame.pack(
            fill="x",
            pady=(14, 0)
        )

        repository_title = ctk.CTkLabel(
            repository_frame,
            text="Repository path para Jira/Xray",
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        repository_title.pack(
            anchor="w",
            pady=(0, 6)
        )

        repository_hint = ctk.CTkLabel(
            repository_frame,
            text=(
                "Este path aplica a todos los Tests y Test Sets de la request seleccionada. "
                "Si ya se capturó antes para esta transacción, aparecerá aquí por defecto y seguirá siendo editable."
            ),
            font=get_font(SMALL),
            text_color=TEXT_MUTED,
            justify="left",
            wraplength=940
        )

        repository_hint.pack(
            anchor="w",
            pady=(0, 8)
        )

        self.repository_path_input = ctk.CTkEntry(
            repository_frame,
            height=40,
            corner_radius=12,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            placeholder_text="Ejemplo: Movimientos TDC"
        )

        self.repository_path_input.pack(
            fill="x"
        )

        acciones_catalogo = ctk.CTkFrame(
            contenido,
            fg_color="transparent"
        )

        acciones_catalogo.pack(
            fill="x",
            pady=(14, 0)
        )

        nuevo_servicio = ctk.CTkButton(
            acciones_catalogo,
            text="+ Servicio",
            width=110,
            height=34,
            corner_radius=17,
            command=self.abrir_dialogo_nuevo_servicio,
            **SECONDARY_BUTTON
        )

        nuevo_servicio.pack(
            side="left"
        )

        nueva_transaccion = ctk.CTkButton(
            acciones_catalogo,
            text="+ Transacción",
            width=132,
            height=34,
            corner_radius=17,
            command=self.abrir_dialogo_nueva_transaccion,
            **SECONDARY_BUTTON
        )

        nueva_transaccion.pack(
            side="left",
            padx=(8, 0)
        )

        nueva_version = ctk.CTkButton(
            acciones_catalogo,
            text="+ Versión",
            width=112,
            height=34,
            corner_radius=17,
            command=self.abrir_dialogo_nueva_version,
            **SECONDARY_BUTTON
        )

        nueva_version.pack(
            side="left",
            padx=(8, 0)
        )

        self.execution_status_label = ctk.CTkLabel(
            acciones_catalogo,
            text="Modo activo: pendiente",
            font=get_font(SMALL),
            text_color=TEXT_MUTED,
            justify="right"
        )

        self.execution_status_label.pack(
            side="right"
        )

        estrategia = ctk.CTkFrame(
            contenido,
            fg_color=PRIMARY_SOFT,
            corner_radius=16,
            border_width=1,
            border_color=BORDER
        )

        estrategia.pack(
            fill="x",
            pady=(14, 0)
        )

        self.strategy_label = ctk.CTkLabel(
            estrategia,
            text=self.obtener_texto_estrategia(),
            font=get_font(SMALL),
            text_color=PRIMARY,
            justify="left",
            wraplength=940
        )

        self.strategy_label.pack(
            anchor="w",
            padx=16,
            pady=12
        )


    def crear_combo_selector(
        self,
        parent,
        column,
        titulo,
        command
    ):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0, 8)
        )

        label = ctk.CTkLabel(
            frame,
            text=titulo,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        label.pack(
            anchor="w",
            pady=(0, 6)
        )

        combo = ctk.CTkComboBox(
            frame,
            values=[SIN_OPCIONES],
            height=42,
            corner_radius=14,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_LIGHT,
            dropdown_fg_color=SURFACE,
            dropdown_hover_color=PRIMARY_SOFT,
            dropdown_text_color=TEXT_PRIMARY,
            text_color=TEXT_PRIMARY,
            command=command,
            state="readonly"
        )

        combo.pack(
            fill="x"
        )

        return combo


    def crear_paneles_resultado(self):

        columnas = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        columnas.pack(
            fill="both",
            expand=True,
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(0, 12)
        )

        columnas.grid_columnconfigure(
            0,
            weight=1,
            uniform="result_cols"
        )
        columnas.grid_columnconfigure(
            1,
            weight=1,
            uniform="result_cols"
        )
        columnas.grid_rowconfigure(
            0,
            weight=1
        )

        mapa_card = ctk.CTkFrame(
            columnas,
            **SOFT_CARD_STYLE
        )

        mapa_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        review_card = ctk.CTkFrame(
            columnas,
            **SOFT_CARD_STYLE
        )

        review_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(8, 0)
        )

        self.mapa_header = ctk.CTkLabel(
            mapa_card,
            text="Mapa de objetos",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        self.mapa_header.pack(
            anchor="w",
            padx=22,
            pady=(18, 6)
        )

        mapa_hint = ctk.CTkLabel(
            mapa_card,
            text="Selecciona los nodos que quieras convertir en test sets. El mapa es manual a propósito para evitar heurísticas prematuras.",
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            wraplength=460,
            justify="left"
        )

        mapa_hint.pack(
            anchor="w",
            padx=22,
            pady=(0, 10)
        )

        self.objects_scroll = ctk.CTkScrollableFrame(
            mapa_card,
            fg_color=SURFACE_ALT,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
            height=250
        )

        self.objects_scroll.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 18)
        )

        self.review_header = ctk.CTkLabel(
            review_card,
            text="Revisión de tests",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        self.review_header.pack(
            anchor="w",
            padx=22,
            pady=(18, 6)
        )

        review_hint = ctk.CTkLabel(
            review_card,
            text="Para cada nodo seleccionado puedes conservar o quitar tests base por campo antes de guardarlos en el planning.",
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            wraplength=460,
            justify="left"
        )

        review_hint.pack(
            anchor="w",
            padx=22,
            pady=(0, 10)
        )

        self.tests_scroll = ctk.CTkScrollableFrame(
            review_card,
            fg_color=SURFACE_ALT,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
            height=250
        )

        self.tests_scroll.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 18)
        )

        self.render_object_map()
        self.render_selected_tests()
        self.actualizar_estado_ejecucion()


    def crear_footer(self):

        footer = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        footer.pack(
            fill="x",
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(0, 18)
        )

        cancelar = ctk.CTkButton(
            footer,
            text="Cancelar",
            width=140,
            height=40,
            corner_radius=20,
            command=self.volver_a_detalle,
            **SECONDARY_BUTTON
        )

        cancelar.pack(
            side="right"
        )

        guardar = ctk.CTkButton(
            footer,
            text="Continuar con diseño de tests",
            width=240,
            height=40,
            corner_radius=20,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            command=self.continuar_a_diseno_tests
        )

        guardar.pack(
            side="right",
            padx=(0, 10)
        )

        ayuda = ctk.CTkLabel(
            footer,
            text="Primero se guarda la selección en planning y enseguida se abre la pantalla para diseñar bodies, escenarios y expectativas por campo.",
            font=get_font(SMALL),
            text_color=TEXT_MUTED,
            justify="left",
            wraplength=520
        )

        ayuda.pack(
            side="left",
            anchor="w"
        )


    def inicializar_catalogo(self):

        self.auto_execute_enabled = False

        if not self.catalog_services:

            self.service_lookup = {
                SIN_SERVICIOS: None
            }
            self.service_combo.configure(
                values=list(self.service_lookup.keys())
            )
            self.service_combo.set(
                SIN_SERVICIOS
            )
            self.transaction_combo.configure(
                values=[SIN_TRANSACCIONES]
            )
            self.transaction_combo.set(
                SIN_TRANSACCIONES
            )
            self.version_combo.configure(
                values=[NO_APLICA]
            )
            self.version_combo.set(
                NO_APLICA
            )
            self.version_combo.configure(
                state="disabled"
            )
            self.auto_execute_enabled = True
            return

        self.service_lookup = {
            servicio.get("name", servicio.get("id")): servicio.get("id")
            for servicio in self.catalog_services
        }

        valores = list(
            self.service_lookup.keys()
        )

        self.service_combo.configure(
            values=valores
        )
        self.service_combo.set(
            valores[0]
        )

        self.on_service_change(
            valores[0]
        )

        self.auto_execute_enabled = True
        self.ejecutar_request_automatico()


    def on_service_change(self, value):

        service_id = self.service_lookup.get(
            value
        )

        transacciones = obtener_transacciones(
            service_id
        ) if service_id else []

        self.transaction_lookup = {
            transaccion.get("name", transaccion.get("id")): transaccion.get("id")
            for transaccion in transacciones
        }

        if not self.transaction_lookup:

            self.transaction_combo.configure(
                values=[SIN_TRANSACCIONES]
            )
            self.transaction_combo.set(
                SIN_TRANSACCIONES
            )
            self.version_lookup = {}
            self.version_combo.configure(
                values=[NO_APLICA],
                state="disabled"
            )
            self.version_combo.set(
                NO_APLICA
            )
            self.actualizar_request_preview()
            return

        valores = list(
            self.transaction_lookup.keys()
        )

        self.transaction_combo.configure(
            values=valores
        )
        self.transaction_combo.set(
            valores[0]
        )

        self.on_transaction_change(
            valores[0]
        )

        self.ejecutar_request_automatico()


    def on_transaction_change(self, value):

        service_id = self.get_selected_service_id()
        transaction_id = self.transaction_lookup.get(
            value
        )

        versiones = obtener_versiones(
            service_id,
            transaction_id
        ) if service_id and transaction_id else []

        self.version_lookup = {
            version.get("label", version.get("id", "").upper()): version.get("id")
            for version in versiones
        }

        if self.version_lookup:

            valores = list(
                self.version_lookup.keys()
            )
            self.version_combo.configure(
                values=valores,
                state="readonly"
            )
            self.version_combo.set(
                valores[0]
            )

        else:

            self.version_combo.configure(
                values=[NO_APLICA],
                state="disabled"
            )
            self.version_combo.set(
                NO_APLICA
            )

        self.actualizar_request_preview()
        self.ejecutar_request_automatico()


    def on_version_change(self, _value):

        self.actualizar_request_preview()
        self.ejecutar_request_automatico()


    def get_selected_service_id(self):

        return self.service_lookup.get(
            self.service_combo.get()
        )


    def get_selected_transaction_id(self):

        return self.transaction_lookup.get(
            self.transaction_combo.get()
        )


    def get_selected_version_id(self):

        if self.version_combo.cget("state") == "disabled":

            return None

        return self.version_lookup.get(
            self.version_combo.get()
        )


    def actualizar_request_preview(self):

        service_id = self.get_selected_service_id()
        transaction_id = self.get_selected_transaction_id()
        version_id = self.get_selected_version_id()

        if not service_id or not transaction_id:

            self.request_preview.configure(
                text="Selecciona una combinación válida del catálogo para continuar."
            )
            return

        try:

            request_info = resolver_request(
                service_id,
                transaction_id,
                version_id
            )

        except CatalogoServiciosError as error:

            self.request_preview.configure(
                text=str(error)
            )
            return

        bruno_request = request_info.get(
            "bruno_request",
            {}
        )
        version_texto = request_info.get(
            "version_label"
        ) or "Sin versión"

        self.request_preview.configure(
            text=(
                f"Request Bruno: {request_info.get('bruno_request_id', '-') }\n"
                f"Archivo esperado: {bruno_request.get('file', '-') }\n"
                f"Colección: {bruno_request.get('collection', '-') } · "
                f"Transacción: {request_info.get('transaction_name', '-') } · "
                f"Versión: {version_texto}\n"
                f"Canal: {request_info.get('transaction_channel', '') or 'Sin canal'} · "
                f"Carpeta Jira: {request_info.get('repository_folder', '') or 'Sin carpeta'}\n"
                f"Librerías: {', '.join(request_info.get('transaction_libraries', [])) or 'Sin librerías'}\n"
                "Modo actual: ejecución real desde el archivo `.bru`. Si la request requiere red interna, activa VPN antes de probar."
            )
        )

        self.sincronizar_repository_path_input(
            request_info
        )


    def ejecutar_request_automatico(self):

        if not self.auto_execute_enabled:

            return

        service_id = self.get_selected_service_id()
        transaction_id = self.get_selected_transaction_id()
        version_id = self.get_selected_version_id()

        if not service_id or not transaction_id:

            return

        try:

            request_info = resolver_request(
                service_id,
                transaction_id,
                version_id
            )

        except CatalogoServiciosError:

            return

        request_key = request_info.get(
            "request_key"
        )

        if request_key == self.last_request_key:

            return

        self.ejecutar_request(
            silent=True
        )


    def ejecutar_request(
        self,
        silent=False
    ):

        service_id = self.get_selected_service_id()
        transaction_id = self.get_selected_transaction_id()
        version_id = self.get_selected_version_id()

        if not service_id or not transaction_id:

            if not silent:

                MessageBox(
                    self,
                    "Debes seleccionar servicio y transacción antes de ejecutar la request.",
                    "warning"
                )
            return

        try:

            resultado = construir_descubrimiento_catalogo(
                service_id,
                transaction_id,
                version_id
            )

        except CatalogoServiciosError as error:

            self.discovery_result = None
            self.last_execution_result = {
                "mode": "error",
                "fallback_reason": str(error)
            }
            self.last_request_key = None
            self.actualizar_estado_ejecucion(
                self.last_execution_result
            )
            self.review_header.configure(
                text="Revisión de tests · ejecución no disponible"
            )
            self.mapa_header.configure(
                text="Mapa de objetos"
            )
            self.render_object_map()
            self.render_selected_tests()

            if not silent:

                MessageBox(
                    self,
                    str(error),
                    "error"
                )
            return

        self.discovery_result = resultado.get(
            "discovery"
        )
        self.request_info = resultado.get(
            "request"
        )
        self.last_execution_result = resultado
        self.last_request_key = self.request_info.get(
            "request_key"
        )
        self.object_states = {}
        self.object_tree_state = {}

        for objeto in self.discovery_result.get(
            "objects",
            []
        ):

            self.object_states[
                objeto["path"]
            ] = {
                "selected": ctk.BooleanVar(value=False),
                "field_vars": {
                    test["field"]: ctk.BooleanVar(value=True)
                    for test in objeto.get(
                        "tests",
                        []
                    )
                }
            }

            self.object_tree_state[
                objeto["path"]
            ] = {
                "expanded": False,
                "show_details": False
            }

        self.mapa_header.configure(
            text=(
                f"Mapa de objetos · {len(self.discovery_result.get('objects', []))} nodos detectados"
            )
        )
        self.review_header.configure(
            text=(
                f"Revisión de tests · ejecución {resultado.get('mode', 'real')}"
            )
        )

        self.actualizar_estado_ejecucion(
            resultado
        )

        self.render_object_map()
        self.render_selected_tests()


    def actualizar_estado_ejecucion(
        self,
        resultado=None
    ):

        resultado = resultado or self.last_execution_result

        if not resultado:

            self.execution_status_label.configure(
                text="Modo activo: pendiente"
            )
            return

        mode = resultado.get(
            "mode",
            "real"
        )
        texto = f"Modo activo: {mode}"

        fallback_reason = str(
            resultado.get(
                "fallback_reason",
                ""
            )
        ).strip()

        if fallback_reason:

            texto = f"{texto} · detalle: {fallback_reason}"

        self.execution_status_label.configure(
            text=texto
        )

        if mode == "error" and "SSL" in fallback_reason.upper():

            self.request_preview.configure(
                text=(
                    f"{self.request_preview.cget('text')}\n"
                    "Sugerencia: revisa `Configuración > Bruno` y prueba desactivar temporalmente `Validar certificado SSL` o captura el CA bundle corporativo."
                )
            )


    def abrir_dialogo_nuevo_servicio(self):

        CatalogFormDialog(
            self,
            "Nuevo servicio",
            [
                ("service_name", "Nombre del servicio", "Movimientos"),
                ("service_id", "Id técnico opcional", "movimientos")
            ],
            self.guardar_nuevo_servicio
        )


    def guardar_nuevo_servicio(
        self,
        data
    ):

        service_id = agregar_servicio_catalogo(
            data.get("service_name"),
            data.get("service_id")
        )

        self.recargar_catalogo_desde_archivo(
            service_id=service_id
        )


    def abrir_dialogo_nueva_transaccion(self):

        service_id = self.get_selected_service_id()

        if not service_id:

            MessageBox(
                self,
                "Selecciona primero un servicio para agregar una transacción.",
                "warning"
            )
            return

        CatalogFormDialog(
            self,
            f"Nueva transacción en {service_id}",
            [
                ("transaction_name", "Nombre de la transacción", "Detalle"),
                ("transaction_id", "Id técnico opcional", "detalle"),
                ("channel", "Canal", "GLOMO"),
                ("repository_folder", "Carpeta Jira/Xray", "Movimientos TDC"),
                ("libraries", "Librerías consumidas (coma separada)", ""),
                ("collection", "Colección Bruno", service_id),
                ("folder", "Folder Bruno", "detalle"),
                ("request", "Request Bruno", "get_detalle"),
                ("file", "Archivo .bru", f"collections/{service_id}/detalle/get_detalle.bru"),
                ("logical_path", "Ruta lógica", f"{service_id}/detalle/get_detalle")
            ],
            lambda data: self.guardar_nueva_transaccion(
                service_id,
                data
            )
        )


    def guardar_nueva_transaccion(
        self,
        service_id,
        data
    ):

        bruno_request = self.construir_bruno_request_desde_form(
            data
        )

        transaction_id = agregar_transaccion_catalogo(
            service_id,
            data.get("transaction_name"),
            data.get("transaction_id"),
            bruno_request=bruno_request,
            libraries=data.get("libraries", ""),
            channel=data.get("channel", ""),
            repository_folder=data.get("repository_folder", "")
        )

        self.recargar_catalogo_desde_archivo(
            service_id=service_id,
            transaction_id=transaction_id
        )


    def abrir_dialogo_nueva_version(self):

        service_id = self.get_selected_service_id()
        transaction_id = self.get_selected_transaction_id()

        if not service_id or not transaction_id:

            MessageBox(
                self,
                "Selecciona primero servicio y transacción para agregar una versión.",
                "warning"
            )
            return

        CatalogFormDialog(
            self,
            f"Nueva versión en {transaction_id}",
            [
                ("version_label", "Etiqueta visible", "V1"),
                ("version_id", "Id técnico opcional", "v1"),
                ("channel", "Canal", "GLOMO"),
                ("repository_folder", "Carpeta Jira/Xray", "Movimientos TDC"),
                ("libraries", "Librerías consumidas (coma separada)", ""),
                ("collection", "Colección Bruno", service_id),
                ("folder", "Folder Bruno", f"{transaction_id}/v1"),
                ("request", "Request Bruno", f"get_{transaction_id}_v1"),
                ("file", "Archivo .bru", f"collections/{service_id}/{transaction_id}/v1/get_{transaction_id}_v1.bru"),
                ("logical_path", "Ruta lógica", f"{service_id}/{transaction_id}/v1/get_{transaction_id}_v1")
            ],
            lambda data: self.guardar_nueva_version(
                service_id,
                transaction_id,
                data
            )
        )


    def guardar_nueva_version(
        self,
        service_id,
        transaction_id,
        data
    ):

        bruno_request = self.construir_bruno_request_desde_form(
            data
        )

        version_id = agregar_version_catalogo(
            service_id,
            transaction_id,
            data.get("version_label"),
            data.get("version_id"),
            bruno_request=bruno_request,
            libraries=data.get("libraries", ""),
            channel=data.get("channel", ""),
            repository_folder=data.get("repository_folder", "")
        )

        self.recargar_catalogo_desde_archivo(
            service_id=service_id,
            transaction_id=transaction_id,
            version_id=version_id
        )


    def construir_bruno_request_desde_form(
        self,
        data
    ):

        bruno_request = construir_bruno_request(
            collection=data.get("collection", ""),
            folder=data.get("folder", ""),
            request=data.get("request", ""),
            file=data.get("file", ""),
            logical_path=data.get("logical_path", "")
        )

        return bruno_request or None


    def recargar_catalogo_desde_archivo(
        self,
        service_id=None,
        transaction_id=None,
        version_id=None
    ):

        self.catalog_services = obtener_servicios()
        self.auto_execute_enabled = False
        self.last_request_key = None

        self.service_lookup = {
            servicio.get("name", servicio.get("id")): servicio.get("id")
            for servicio in self.catalog_services
        }

        service_label = self.buscar_label_servicio(
            service_id
        ) if service_id else None

        values = list(
            self.service_lookup.keys()
        )

        self.service_combo.configure(
            values=values or [SIN_SERVICIOS]
        )

        if not values:

            self.service_combo.set(
                SIN_SERVICIOS
            )
            self.auto_execute_enabled = True
            return

        self.service_combo.set(
            service_label or values[0]
        )
        self.on_service_change(
            self.service_combo.get()
        )

        if transaction_id:

            transaction_label = self.buscar_label_transaccion(
                self.get_selected_service_id(),
                transaction_id
            )

            if transaction_label:

                self.transaction_combo.set(
                    transaction_label
                )
                self.on_transaction_change(
                    transaction_label
                )

        if version_id:

            version_label = self.buscar_label_version(
                self.get_selected_service_id(),
                self.get_selected_transaction_id(),
                version_id
            )

            if version_label:

                self.version_combo.set(
                    version_label
                )
                self.on_version_change(
                    version_label
                )

        self.auto_execute_enabled = True
        self.ejecutar_request_automatico()


    def buscar_label_servicio(
        self,
        service_id
    ):

        for label, value in self.service_lookup.items():

            if value == service_id:

                return label

        return None


    def buscar_label_transaccion(
        self,
        service_id,
        transaction_id
    ):

        for transaccion in obtener_transacciones(
            service_id
        ):

            if transaccion.get("id") == transaction_id:

                return transaccion.get(
                    "name",
                    transaction_id
                )

        return None


    def buscar_label_version(
        self,
        service_id,
        transaction_id,
        version_id
    ):

        for version in obtener_versiones(
            service_id,
            transaction_id
        ):

            if version.get("id") == version_id:

                return version.get(
                    "label",
                    version_id.upper()
                )

        return None


    def render_object_map(self):

        self.clear_container_widgets(
            self.objects_scroll
        )

        objetos = []

        if self.discovery_result:

            objetos = self.discovery_result.get(
                "objects",
                []
            )

        if not objetos:

            self.render_empty_state(
                self.objects_scroll,
                "Todavía no hay un mapa disponible. Verifica la request `.bru`, la conectividad VPN y si el archivo necesita variables adicionales antes de descubrir nodos JSON."
            )
            return

        arbol = self.construir_arbol_objetos(
            objetos
        )

        for nodo in arbol:

            self.render_object_tree_node(
                nodo,
                depth=0
            )


    def calcular_estado_cobertura_nodo(self, nodo):

        coverage = nodo["item"].get(
            "coverage",
            {}
        )
        existe_actual = bool(
            coverage.get("exists")
        )
        children = nodo.get(
            "children",
            []
        )

        if not children:

            if existe_actual:

                return {
                    "status": "complete",
                    "label": "Cubierto",
                    "fg_color": "#EAF7F0",
                    "border_color": "#B9E2C8",
                    "badge_color": "#EAF7F0",
                    "badge_text_color": "#2E7D32"
                }

            return {
                "status": "empty",
                "label": "Sin plan",
                "fg_color": "#F4F6FA",
                "border_color": BORDER,
                "badge_color": "#F4F6FA",
                "badge_text_color": TEXT_MUTED
            }

        child_states = [
            self.calcular_estado_cobertura_nodo(child)
            for child in children
        ]

        all_children_complete = all(
            child["status"] == "complete"
            for child in child_states
        )
        any_child_with_plan = any(
            child["status"] in (
                "complete",
                "partial"
            )
            for child in child_states
        )

        if existe_actual and all_children_complete:

            return {
                "status": "complete",
                "label": "Cubierto",
                "fg_color": "#EAF7F0",
                "border_color": "#B9E2C8",
                "badge_color": "#EAF7F0",
                "badge_text_color": "#2E7D32"
            }

        if existe_actual or any_child_with_plan:

            return {
                "status": "partial",
                "label": "Parcial",
                "fg_color": "#FFF7D6",
                "border_color": "#F2D77C",
                "badge_color": "#FFF7D6",
                "badge_text_color": "#8A6A00"
            }

        return {
            "status": "empty",
            "label": "Sin plan",
            "fg_color": "#F4F6FA",
            "border_color": BORDER,
            "badge_color": "#F4F6FA",
            "badge_text_color": TEXT_MUTED
        }


    def construir_arbol_objetos(self, objetos):

        lookup = {
            objeto["path"]: objeto
            for objeto in objetos
        }

        children_by_parent = {}
        roots = []

        for objeto in objetos:

            parent_path = self.obtener_parent_path(
                objeto["path"]
            )

            node = {
                "item": objeto,
                "children": []
            }

            children_by_parent.setdefault(
                parent_path,
                []
            ).append(node)

        for parent_path, children in children_by_parent.items():

            children.sort(
                key=lambda current: current["item"]["path"]
            )

            if parent_path is None or parent_path not in lookup:

                roots.extend(
                    children
                )
                continue

            parent_nodes = children_by_parent.get(
                self.obtener_parent_path(parent_path),
                []
            )

            for parent_node in parent_nodes:

                if parent_node["item"]["path"] == parent_path:

                    parent_node["children"].extend(
                        children
                    )
                    break

        return sorted(
            roots,
            key=lambda current: current["item"]["path"]
        )


    def obtener_parent_path(self, path):

        path = str(
            path or ""
        ).strip()

        if not path:

            return None

        if "." not in path:

            return None

        return path.rsplit(
            ".",
            1
        )[0]


    def obtener_segmento_path(self, path):

        path = str(
            path or ""
        ).strip()

        if not path:

            return "root"

        return path.split(".")[-1]


    def render_object_tree_node(
        self,
        nodo,
        depth
    ):

        objeto = nodo["item"]
        path = objeto["path"]
        tree_state = self.object_tree_state.setdefault(
            path,
            {
                "expanded": False,
                "show_details": False
            }
        )
        has_children = bool(
            nodo.get("children")
        )

        state = self.object_states.get(
            path,
            {}
        )
        coverage_state = self.calcular_estado_cobertura_nodo(
            nodo
        )

        card = ctk.CTkFrame(
            self.objects_scroll,
            fg_color=coverage_state["fg_color"],
            corner_radius=14,
            border_width=1,
            border_color=coverage_state["border_color"]
        )

        card.pack(
            fill="x",
            padx=(4 + depth * 18, 4),
            pady=(0, 10)
        )

        top = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        top.pack(
            fill="x",
            padx=14,
            pady=(12, 6)
        )

        if has_children:

            toggle = ctk.CTkButton(
                top,
                text="▾" if tree_state.get("expanded") else "▸",
                width=28,
                height=28,
                corner_radius=14,
                fg_color="transparent",
                hover_color=PRIMARY_SOFT,
                text_color=PRIMARY,
                border_width=0,
                command=lambda current=path: self.toggle_object_node(current)
            )

            toggle.pack(
                side="left",
                padx=(0, 6)
            )

        else:

            espacio = ctk.CTkLabel(
                top,
                text="•",
                font=get_font(BODY),
                text_color=TEXT_MUTED,
                width=18
            )

            espacio.pack(
                side="left",
                padx=(0, 10)
            )

        label_text = self.obtener_segmento_path(objeto['path'])

        checkbox = ctk.CTkCheckBox(
            top,
            text=label_text,
            variable=state.get("selected"),
            font=get_font(BODY),
            text_color=TEXT_PRIMARY,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            border_color=PRIMARY,
            command=lambda current=nodo: self.on_object_selected(current)
        )

        checkbox.pack(
            side="left",
            anchor="w"
        )

        info_button = ctk.CTkButton(
            top,
            text=(
                "Ocultar info"
                if tree_state.get("show_details")
                else "Ver info"
            ),
            width=90,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color=PRIMARY_SOFT,
            text_color=PRIMARY,
            border_width=1,
            border_color=BORDER,
            command=lambda current=path: self.toggle_object_details(current)
        )

        info_button.pack(
            side="right",
            padx=(0, 8)
        )

        badge = ctk.CTkLabel(
            top,
            text=coverage_state["label"],
            font=get_font(SMALL),
            fg_color=coverage_state["badge_color"],
            text_color=coverage_state["badge_text_color"],
            corner_radius=12,
            padx=10,
            pady=4
        )

        badge.pack(
            side="right"
        )

        if tree_state.get("show_details"):

            ruta = ctk.CTkLabel(
                card,
                text=f"Ruta completa: {objeto['path']}",
                font=get_font(SMALL),
                text_color=TEXT_MUTED,
                justify="left",
                wraplength=440
            )

            ruta.pack(
                anchor="w",
                padx=14,
                pady=(0, 4)
            )

            detalle = ctk.CTkLabel(
                card,
                text=(
                    f"Tipo: {objeto.get('kind', 'object')} · "
                    f"Campos directos: {objeto.get('field_count', 0)} · "
                    f"Hijos: {objeto.get('child_count', 0)} · "
                    f"Profundidad: {objeto.get('depth', 0)}"
                ),
                font=get_font(SMALL),
                text_color=TEXT_SECONDARY,
                justify="left"
            )

            detalle.pack(
                anchor="w",
                padx=14,
                pady=(0, 6)
            )

            campos = ", ".join(
                objeto.get(
                    "fields",
                    []
                )[:6]
            ) or "Sin campos directos"

            resumen = ctk.CTkLabel(
                card,
                text=f"Campos: {campos}",
                font=get_font(SMALL),
                text_color=TEXT_MUTED,
                justify="left",
                wraplength=440
            )

            resumen.pack(
                anchor="w",
                padx=14,
                pady=(0, 12)
            )

        else:

            separador = ctk.CTkFrame(
                card,
                fg_color="transparent",
                height=2
            )

            separador.pack(
                fill="x",
                pady=(0, 8)
            )

        if tree_state.get("expanded"):

            for child in nodo.get(
                "children",
                []
            ):

                self.render_object_tree_node(
                    child,
                    depth + 1
                )


    def toggle_object_node(self, path):

        tree_state = self.object_tree_state.setdefault(
            path,
            {
                "expanded": False,
                "show_details": False
            }
        )
        tree_state["expanded"] = not tree_state.get(
            "expanded",
            False
        )
        self.render_object_map()


    def toggle_object_details(self, path):

        tree_state = self.object_tree_state.setdefault(
            path,
            {
                "expanded": False,
                "show_details": False
            }
        )
        tree_state["show_details"] = not tree_state.get(
            "show_details",
            False
        )
        self.render_object_map()


    def on_object_selected(self, nodo):

        seleccionado = bool(
            self.object_states.get(
                nodo["item"]["path"],
                {}
            ).get(
                "selected"
            ).get()
        )

        self.aplicar_seleccion_subarbol(
            nodo,
            seleccionado
        )
        self.render_selected_tests()
        self.render_object_map()


    def aplicar_seleccion_subarbol(
        self,
        nodo,
        seleccionado
    ):

        objeto = nodo["item"]
        state = self.object_states.get(
            objeto["path"],
            {}
        )
        variable = state.get(
            "selected"
        )

        if variable:

            variable.set(
                seleccionado
            )

        for child in nodo.get(
            "children",
            []
        ):

            self.aplicar_seleccion_subarbol(
                child,
                seleccionado
            )


    def render_selected_tests(self):

        self.clear_container_widgets(
            self.tests_scroll
        )

        objetos = self.get_selected_objects()

        if not objetos:

            self.render_empty_state(
                self.tests_scroll,
                "Selecciona uno o más nodos del mapa para revisar los tests base por campo."
            )
            return

        for objeto in objetos:

            state = self.object_states.get(
                objeto["path"],
                {}
            )
            field_vars = state.get(
                "field_vars",
                {}
            )

            card = ctk.CTkFrame(
                self.tests_scroll,
                fg_color=SURFACE,
                corner_radius=14,
                border_width=1,
                border_color=BORDER
            )

            card.pack(
                fill="x",
                padx=4,
                pady=(0, 10)
            )

            titulo = ctk.CTkLabel(
                card,
                text=objeto["path"],
                font=get_font(BODY),
                text_color=TEXT_PRIMARY
            )

            titulo.pack(
                anchor="w",
                padx=14,
                pady=(12, 4)
            )

            coverage = objeto.get(
                "coverage",
                {}
            )

            subtitulo = ctk.CTkLabel(
                card,
                text=(
                    f"Test set existente: {coverage.get('jira_test_set', 'No')} · "
                    f"Tests reutilizados: {coverage.get('reused_tests', 0)} · "
                    f"Tests nuevos: {coverage.get('new_tests', 0)}"
                ),
                font=get_font(SMALL),
                text_color=TEXT_SECONDARY,
                justify="left",
                wraplength=440
            )

            subtitulo.pack(
                anchor="w",
                padx=14,
                pady=(0, 8)
            )

            tests = objeto.get(
                "tests",
                []
            )

            if not tests:

                vacio = ctk.CTkLabel(
                    card,
                    text="Nodo estructural sin campos directos. Si lo guardas, se crea un test set placeholder para completarlo después.",
                    font=get_font(SMALL),
                    text_color=TEXT_MUTED,
                    justify="left",
                    wraplength=440
                )

                vacio.pack(
                    anchor="w",
                    padx=14,
                    pady=(0, 12)
                )
                continue

            for test in tests:

                fila = ctk.CTkFrame(
                    card,
                    fg_color="transparent"
                )

                fila.pack(
                    fill="x",
                    padx=14,
                    pady=(0, 8)
                )

                checkbox = ctk.CTkCheckBox(
                    fila,
                    text=test["field"],
                    variable=field_vars.get(test["field"]),
                    font=get_font(SMALL),
                    text_color=TEXT_PRIMARY,
                    fg_color=PRIMARY,
                    hover_color=PRIMARY_LIGHT,
                    border_color=PRIMARY
                )

                checkbox.pack(
                    side="left",
                    anchor="w"
                )

                detalle = test["status"].title()

                if test.get("jira_test"):

                    detalle = f"{detalle} · {test['jira_test']}"

                estado = ctk.CTkLabel(
                    fila,
                    text=detalle,
                    font=get_font(SMALL),
                    fg_color=PRIMARY_SOFT,
                    text_color=PRIMARY,
                    corner_radius=12,
                    padx=8,
                    pady=3
                )

                estado.pack(
                    side="right"
                )


    def continuar_a_diseno_tests(self):

        if not self.request_info or not self.discovery_result:

            MessageBox(
                self,
                "Ejecuta primero una request del catálogo antes de continuar al diseño de tests.",
                "warning"
            )
            return

        seleccionados = []

        for objeto in self.get_selected_objects():

            state = self.object_states.get(
                objeto["path"],
                {}
            )
            field_vars = state.get(
                "field_vars",
                {}
            )

            selected_fields = [
                field
                for field, variable in field_vars.items()
                if variable.get()
            ]

            seleccionados.append(
                {
                    **objeto,
                    "selected_fields": selected_fields
                }
            )

        if not seleccionados:

            MessageBox(
                self,
                "Selecciona al menos un nodo del mapa antes de continuar.",
                "warning"
            )
            return

        repository_path = self.obtener_repository_path_actual()

        if not repository_path:

            MessageBox(
                self,
                "Captura el repository path antes de continuar. Ese valor se reutilizará para todos los Tests y Test Sets de esta request.",
                "warning"
            )
            return

        self.request_info["repository_folder"] = repository_path

        service_id = self.request_info.get("service_id")
        transaction_id = self.request_info.get("transaction_id")

        if service_id and transaction_id:

            try:

                actualizar_repository_folder_catalogo(
                    service_id,
                    transaction_id,
                    repository_path,
                    version_id=self.request_info.get("version_id")
                )

            except CatalogoServiciosError as error:

                MessageBox(
                    self,
                    str(error),
                    "warning"
                )
                return

        planning_data = actualizar_planning_con_seleccion(
            self.crq,
            self.request_info,
            seleccionados,
            self.metadata_actual,
            self.discovery_actual
        )

        self.navigate(
            "test_design",
            crq=self.crq,
            planning_data=planning_data,
            request_info=self.request_info,
            response_data=(self.last_execution_result or {}).get(
                "response"
            )
        )


    def sincronizar_repository_path_input(self, request_info):

        if not self.repository_path_input:

            return

        valor = str(
            (request_info or {}).get(
                "repository_folder",
                ""
            ) or ""
        ).strip()

        self.repository_path_input.delete(0, "end")
        self.repository_path_input.insert(0, valor)


    def obtener_repository_path_actual(self):

        if not self.repository_path_input:

            return ""

        return self.repository_path_input.get().strip()


    def get_selected_objects(self):

        if not self.discovery_result:

            return []

        resultado = []

        for objeto in self.discovery_result.get(
            "objects",
            []
        ):

            state = self.object_states.get(
                objeto["path"],
                {}
            )
            variable = state.get(
                "selected"
            )

            if variable and variable.get():

                resultado.append(
                    objeto
                )

        return resultado


    def obtener_texto_estrategia(self):

        tipologias = normalizar_certificaciones(
            self.crq.get(
                "certificaciones",
                []
            )
        )

        mapa = obtener_mapa_typology()
        nombres = [
            mapa.get(
                tipologia,
                tipologia
            )
            for tipologia in tipologias
        ]

        detalle = ", ".join(nombres) if nombres else "Sin tipología"

        return (
            f"Typologies del CRQ: {detalle}. "
            "Regla activa: Integrado es la base, Aceptación replica Integración cuando ambas existen y Regresión permanece como planning independiente."
        )


    def volver_a_detalle(self):

        self.navigate(
            "crq_detail",
            crq=self.crq
        )


    def clear_container_widgets(
        self,
        container
    ):

        for widget in container.winfo_children():

            widget.destroy()


    def render_empty_state(
        self,
        container,
        text
    ):

        label = ctk.CTkLabel(
            container,
            text=text,
            font=get_font(BODY),
            text_color=TEXT_MUTED,
            wraplength=420,
            justify="left"
        )

        label.pack(
            anchor="w",
            padx=12,
            pady=16
        )


class CatalogFormDialog(ctk.CTkToplevel):


    def __init__(
        self,
        parent,
        title,
        fields,
        on_submit
    ):

        super().__init__(
            parent
        )

        self.on_submit = on_submit
        self.inputs = {}

        self.title(
            title
        )
        self.geometry(
            "520x520"
        )
        self.resizable(
            False,
            False
        )
        self.configure(
            fg_color=BACKGROUND
        )
        self.transient(
            parent.winfo_toplevel()
        )
        self.grab_set()

        card = ctk.CTkFrame(
            self,
            **SOFT_CARD_STYLE
        )

        card.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        titulo = ctk.CTkLabel(
            card,
            text=title,
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        titulo.pack(
            anchor="w",
            padx=18,
            pady=(18, 10)
        )

        body = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent"
        )

        body.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 12)
        )

        for key, label_text, default in fields:

            field = ctk.CTkFrame(
                body,
                fg_color="transparent"
            )

            field.pack(
                fill="x",
                padx=6,
                pady=(0, 10)
            )

            label = ctk.CTkLabel(
                field,
                text=label_text,
                font=get_font(SMALL),
                text_color=TEXT_PRIMARY
            )

            label.pack(
                anchor="w",
                pady=(0, 4)
            )

            entry = ctk.CTkEntry(
                field,
                height=38,
                corner_radius=12,
                fg_color=SURFACE_ALT,
                border_color=BORDER,
                text_color=TEXT_PRIMARY
            )

            entry.pack(
                fill="x"
            )
            entry.insert(
                0,
                str(default or "")
            )

            self.inputs[key] = entry

        footer = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        footer.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        cancelar = ctk.CTkButton(
            footer,
            text="Cancelar",
            width=120,
            height=38,
            corner_radius=19,
            command=self.destroy,
            **SECONDARY_BUTTON
        )

        cancelar.pack(
            side="right"
        )

        guardar = ctk.CTkButton(
            footer,
            text="Guardar",
            width=120,
            height=38,
            corner_radius=19,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            command=self.submit
        )

        guardar.pack(
            side="right",
            padx=(0, 8)
        )


    def submit(self):

        data = {
            key: entry.get().strip()
            for key, entry in self.inputs.items()
        }

        try:

            self.on_submit(
                data
            )

        except CatalogoServiciosError as error:

            MessageBox(
                self,
                str(error),
                "error"
            )
            return

        self.destroy()


