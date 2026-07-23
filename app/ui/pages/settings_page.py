import customtkinter as ctk

from app.services.bruno_catalog_service import (
    BrunoCatalogError,
    listar_bruno_tree
)
from app.services.config_service import (
    cargar_bruno_config,
    cargar_ui_config,
    guardar_bruno_config,
    guardar_ui_config
)
from app.services.test_catalog_service import (
    CatalogoServiciosError,
    importar_request_bru_catalogo,
    inferir_importacion_desde_bru
)
from app.ui.components.message_box import MessageBox
from app.ui.pages.base_page import BasePage
from app.ui.theme.colors import (
    BACKGROUND,
    BORDER,
    PRIMARY,
    PRIMARY_LIGHT,
    PRIMARY_SOFT,
    SURFACE,
    SURFACE_ALT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY
)
from app.ui.theme.dimensions import PAGE_HORIZONTAL_PADDING
from app.ui.theme.styles import SECONDARY_BUTTON, SOFT_CARD_STYLE
from app.ui.theme.typography import BODY, SMALL, SUBTITLE, TITLE, get_font


class SettingsPage(BasePage):


    def build(self):

        self.configure(
            fg_color=BACKGROUND
        )

        self.bruno_config = dict(
            cargar_bruno_config() or {}
        )
        self.ui_config = dict(
            cargar_ui_config() or {}
        )

        self.crear_ui()
        self.render_bruno_tree()


    def crear_ui(self):

        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        self.content.pack(
            fill="both",
            expand=True
        )

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
            text="Configuración",
            font=get_font(TITLE),
            text_color=PRIMARY
        )

        titulo.pack()

        subtitulo = ctk.CTkLabel(
            hero,
            text="Configura la ruta de colecciones Bruno y revisa la estructura real disponible para importar requests `.bru`.",
            font=get_font(BODY),
            text_color=TEXT_SECONDARY,
            wraplength=980,
            justify="center"
        )

        subtitulo.pack(
            pady=(8, 0)
        )

        self.tabview = ctk.CTkTabview(
            self.content,
            fg_color=SURFACE,
            segmented_button_fg_color=PRIMARY_SOFT,
            segmented_button_selected_color=PRIMARY,
            segmented_button_selected_hover_color=PRIMARY_LIGHT,
            segmented_button_unselected_color=SURFACE_ALT,
            segmented_button_unselected_hover_color=PRIMARY_SOFT,
            text_color=TEXT_PRIMARY,
            corner_radius=20,
            border_width=1,
            border_color=BORDER
        )

        self.tabview.pack(
            fill="both",
            expand=True,
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(0, 20)
        )

        self.tabview.add("Bruno")
        self.tabview.add("Jira")
        self.tabview.add("General")

        self.crear_tab_bruno()
        self.crear_tab_jira()
        self.crear_tab_general()


    def crear_campo(
        self,
        parent,
        label_text,
        default_value
    ):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.pack(
            fill="x",
            pady=(0, 10)
        )

        label = ctk.CTkLabel(
            frame,
            text=label_text,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        label.pack(
            anchor="w",
            pady=(0, 4)
        )

        entry = ctk.CTkEntry(
            frame,
            height=40,
            corner_radius=14,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
            text_color=TEXT_PRIMARY
        )

        entry.pack(
            fill="x"
        )
        entry.insert(
            0,
            str(default_value or "")
        )

        return entry


    def crear_combo(
        self,
        parent,
        label_text,
        values,
        current_value
    ):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.pack(
            fill="x",
            pady=(0, 10)
        )

        label = ctk.CTkLabel(
            frame,
            text=label_text,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        label.pack(
            anchor="w",
            pady=(0, 4)
        )

        combo = ctk.CTkComboBox(
            frame,
            values=values,
            height=40,
            corner_radius=14,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_LIGHT,
            dropdown_fg_color=SURFACE,
            dropdown_hover_color=PRIMARY_SOFT,
            dropdown_text_color=TEXT_PRIMARY,
            text_color=TEXT_PRIMARY,
            state="readonly"
        )

        combo.pack(
            fill="x"
        )
        combo.set(
            current_value if current_value in values else values[0]
        )

        return combo


    def crear_tab_bruno(self):

        tab = self.tabview.tab("Bruno")

        contenedor = ctk.CTkFrame(
            tab,
            fg_color="transparent"
        )

        contenedor.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        card = ctk.CTkFrame(
            contenedor,
            **SOFT_CARD_STYLE
        )

        card.pack(
            fill="x",
            pady=(0, 12)
        )

        body = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        body.pack(
            fill="x",
            padx=24,
            pady=22
        )

        titulo = ctk.CTkLabel(
            body,
            text="Configuración Bruno",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        titulo.pack(
            anchor="w",
            pady=(0, 6)
        )

        resumen = ctk.CTkLabel(
            body,
            text=(
                "Modo fijo del proyecto: ejecución real de Bruno. "
                "CertFlow intentará leer el archivo `.bru`, tomar sus datos HTTP y lanzar la request real automáticamente."
            ),
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            wraplength=960,
            justify="left"
        )

        resumen.pack(
            anchor="w",
            pady=(0, 12)
        )

        self.bruno_path_entry = self.crear_campo(
            body,
            "Ruta Bruno Collections",
            self.bruno_config.get(
                "collection_root",
                ""
            )
        )

        self.timeout_entry = self.crear_campo(
            body,
            "Timeout (segundos)",
            str(
                self.bruno_config.get(
                    "timeout_seconds",
                    90
                )
            )
        )

        self.verify_ssl_var = ctk.BooleanVar(
            value=bool(
                self.bruno_config.get(
                    "verify_ssl",
                    True
                )
            )
        )

        verify_ssl = ctk.CTkCheckBox(
            body,
            text="Validar certificado SSL",
            variable=self.verify_ssl_var,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            border_color=PRIMARY
        )

        verify_ssl.pack(
            anchor="w",
            pady=(0, 10)
        )

        self.ca_bundle_entry = self.crear_campo(
            body,
            "CA bundle corporativo (opcional)",
            self.bruno_config.get(
                "ca_bundle_path",
                ""
            )
        )

        self.bruno_mode_label = ctk.CTkLabel(
            body,
            text="Modo efectivo: real · lectura directa desde `.bru` · fallback a mock: desactivado",
            font=get_font(SMALL),
            text_color=TEXT_MUTED,
            justify="left"
        )

        self.bruno_mode_label.pack(
            anchor="w",
            pady=(0, 10)
        )

        acciones = ctk.CTkFrame(
            body,
            fg_color="transparent"
        )

        acciones.pack(
            fill="x",
            pady=(6, 0)
        )

        guardar = ctk.CTkButton(
            acciones,
            text="Guardar Bruno",
            width=160,
            height=40,
            corner_radius=20,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            command=self.guardar_configuracion_bruno
        )

        guardar.pack(
            side="right"
        )

        refrescar = ctk.CTkButton(
            acciones,
            text="Refrescar árbol Bruno",
            width=180,
            height=40,
            corner_radius=20,
            command=self.render_bruno_tree,
            **SECONDARY_BUTTON
        )

        refrescar.pack(
            side="right",
            padx=(0, 10)
        )

        self.vpn_hint = ctk.CTkLabel(
            body,
            text="Antes de ejecutar una request real en Añadir tests, prende tu VPN si el servicio vive en red interna. CertFlow ya resuelve variables dinámicas comunes como {{$guid}}. Si aparece un error SSL corporativo, puedes desactivar temporalmente la validación o indicar un CA bundle.",
            font=get_font(SMALL),
            text_color=TEXT_MUTED,
            wraplength=960,
            justify="left"
        )

        self.vpn_hint.pack(
            anchor="w",
            pady=(10, 0)
        )

        explorer_card = ctk.CTkFrame(
            contenedor,
            **SOFT_CARD_STYLE
        )

        explorer_card.pack(
            fill="both",
            expand=True
        )

        titulo_tree = ctk.CTkLabel(
            explorer_card,
            text="Explorador de colecciones Bruno",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        titulo_tree.pack(
            anchor="w",
            padx=22,
            pady=(18, 6)
        )

        hint = ctk.CTkLabel(
            explorer_card,
            text="Desde aquí puedes validar la ruta base, ver requests `.bru` detectadas e importarlas al catálogo funcional.",
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            wraplength=960,
            justify="left"
        )

        hint.pack(
            anchor="w",
            padx=22,
            pady=(0, 12)
        )

        self.tree_status = ctk.CTkLabel(
            explorer_card,
            text="",
            font=get_font(SMALL),
            text_color=TEXT_MUTED,
            justify="left",
            wraplength=960
        )

        self.tree_status.pack(
            anchor="w",
            padx=22,
            pady=(0, 8)
        )

        self.tree_scroll = ctk.CTkScrollableFrame(
            explorer_card,
            fg_color=SURFACE_ALT,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
            height=300
        )

        self.tree_scroll.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 18)
        )


    def crear_tab_jira(self):

        tab = self.tabview.tab("Jira")

        contenedor = ctk.CTkFrame(
            tab,
            fg_color="transparent"
        )

        contenedor.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        card = ctk.CTkFrame(
            contenedor,
            **SOFT_CARD_STYLE
        )

        card.pack(
            fill="x"
        )

        body = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        body.pack(
            fill="x",
            padx=24,
            pady=22
        )

        titulo = ctk.CTkLabel(
            body,
            text="Configuración Jira / Xray",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        titulo.pack(
            anchor="w",
            pady=(0, 6)
        )

        ayuda = ctk.CTkLabel(
            body,
            text="Define aquí la URL base de Jira y valores temporales por defecto para probar la automatización asistida con Playwright desde el Home. Más adelante, Project/Repository Path se moverán a configuración por servicio/transacción.",
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            wraplength=960,
            justify="left"
        )

        ayuda.pack(
            anchor="w",
            pady=(0, 12)
        )

        self.jira_entry = self.crear_campo(
            body,
            "Jira base URL",
            self.ui_config.get(
                "jira_base_url",
                ""
            )
        )

        self.jira_project_key_entry = self.crear_campo(
            body,
            "Project Key",
            self.ui_config.get(
                "jira_project_key",
                ""
            )
        )

        self.jira_project_name_entry = self.crear_campo(
            body,
            "Project Name",
            self.ui_config.get(
                "jira_project_name",
                ""
            )
        )

        self.jira_repository_path_entry = self.crear_campo(
            body,
            "Test Repository Path",
            self.ui_config.get(
                "jira_test_repository_path",
                ""
            )
        )

        self.jira_browser_channel_entry = self.crear_campo(
            body,
            "Browser channel",
            self.ui_config.get(
                "jira_browser_channel",
                "chrome"
            )
        )

        guardar = ctk.CTkButton(
            body,
            text="Guardar Jira",
            width=150,
            height=40,
            corner_radius=20,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            command=self.guardar_configuracion_jira
        )

        guardar.pack(
            anchor="e",
            pady=(6, 0)
        )


    def crear_tab_general(self):

        tab = self.tabview.tab("General")

        contenedor = ctk.CTkFrame(
            tab,
            fg_color="transparent"
        )

        contenedor.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        card = ctk.CTkFrame(
            contenedor,
            **SOFT_CARD_STYLE
        )

        card.pack(
            fill="x"
        )

        body = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        body.pack(
            fill="x",
            padx=24,
            pady=22
        )

        titulo = ctk.CTkLabel(
            body,
            text="Resumen operativo",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        titulo.pack(
            anchor="w",
            pady=(0, 6)
        )

        self.general_summary_label = ctk.CTkLabel(
            body,
            text="",
            font=get_font(BODY),
            text_color=TEXT_PRIMARY,
            wraplength=960,
            justify="left"
        )

        self.general_summary_label.pack(
            anchor="w"
        )

        self.actualizar_resumen_general()


    def actualizar_resumen_general(self):

        collection_root = self.bruno_config.get(
            "collection_root",
            "Sin definir"
        ) or "Sin definir"
        jira_url = self.ui_config.get(
            "jira_base_url",
            "Sin definir"
        ) or "Sin definir"
        jira_project_key = self.ui_config.get(
            "jira_project_key",
            "Sin definir"
        ) or "Sin definir"
        jira_repository_path = self.ui_config.get(
            "jira_test_repository_path",
            "Sin definir"
        ) or "Sin definir"
        timeout = self.bruno_config.get(
            "timeout_seconds",
            90
        )

        self.general_summary_label.configure(
            text=(
                f"• Bruno se usará en modo real.\n"
                f"• Ruta actual de colecciones: {collection_root}\n"
                f"• Timeout configurado: {timeout} segundos\n"
                f"• Jira base URL: {jira_url}\n"
                f"• Jira project key: {jira_project_key}\n"
                f"• Jira repository path: {jira_repository_path}\n\n"
                "Prueba recomendada: importa una request `.bru` desde la pestaña Bruno, luego ve a `Añadir tests`, prende VPN y valida que el discovery cargue objetos reales."
            )
        )


    def guardar_configuracion_bruno(self):

        timeout_text = self.timeout_entry.get().strip()

        try:

            timeout_value = int(
                timeout_text or "90"
            )

        except ValueError:

            MessageBox(
                self,
                "El timeout de Bruno debe ser numérico.",
                "error"
            )
            return

        bruno_config = dict(
            self.bruno_config
        )
        bruno_config.update(
            {
                "enabled": True,
                "preferred_mode": "real_only",
                "collection_root": self.bruno_path_entry.get().strip(),
                "command_template": self.bruno_config.get(
                    "command_template",
                    ""
                ),
                "response_mode": "",
                "timeout_seconds": timeout_value,
                "verify_ssl": self.verify_ssl_var.get(),
                "ca_bundle_path": self.ca_bundle_entry.get().strip(),
                "allow_mock_fallback": False
            }
        )

        guardar_bruno_config(
            bruno_config
        )

        self.bruno_config = bruno_config

        MessageBox(
            self,
            "Configuración Bruno guardada correctamente.",
            "success"
        )

        self.actualizar_resumen_general()
        self.render_bruno_tree()


    def guardar_configuracion_jira(self):

        ui_config = dict(
            self.ui_config
        )
        ui_config["jira_base_url"] = self.jira_entry.get().strip()
        ui_config["jira_project_key"] = self.jira_project_key_entry.get().strip()
        ui_config["jira_project_name"] = self.jira_project_name_entry.get().strip()
        ui_config["jira_test_repository_path"] = self.jira_repository_path_entry.get().strip()
        ui_config["jira_browser_channel"] = self.jira_browser_channel_entry.get().strip() or "chrome"

        guardar_ui_config(
            ui_config
        )

        self.ui_config = ui_config

        MessageBox(
            self,
            "Configuración Jira guardada correctamente.",
            "success"
        )

        self.actualizar_resumen_general()


    def render_bruno_tree(self):

        for widget in self.tree_scroll.winfo_children():

            widget.destroy()

        try:

            tree = listar_bruno_tree()

        except BrunoCatalogError as error:

            self.tree_status.configure(
                text=str(error)
            )
            self.render_empty_state(
                str(error)
            )
            return

        self.tree_status.configure(
            text=f"Ruta actual: {tree['root']}"
        )

        nodos = tree.get(
            "nodes",
            []
        )

        if not nodos:

            self.render_empty_state(
                "La carpeta de colecciones no contiene elementos visibles."
            )
            return

        for node in nodos:

            self.render_tree_node(
                node,
                depth=0
            )


    def render_tree_node(
        self,
        node,
        depth
    ):

        indent = "    " * depth
        icon = "📁" if node.get("type") == "directory" else "📄"
        suffix = " (.bru)" if node.get("is_request") else ""

        fila = ctk.CTkFrame(
            self.tree_scroll,
            fg_color="transparent"
        )

        fila.pack(
            fill="x",
            padx=12,
            pady=(0, 4)
        )

        label = ctk.CTkLabel(
            fila,
            text=f"{indent}{icon} {node.get('name', '')}{suffix}",
            font=get_font(SMALL),
            text_color=TEXT_PRIMARY,
            justify="left",
            anchor="w"
        )

        label.pack(
            side="left",
            anchor="w"
        )

        if node.get("is_request"):

            importar = ctk.CTkButton(
                fila,
                text="Importar",
                width=96,
                height=30,
                corner_radius=15,
                command=lambda current=node: self.abrir_importacion_request(current),
                **SECONDARY_BUTTON
            )

            importar.pack(
                side="right"
            )

        relative = node.get(
            "relative_path",
            ""
        )

        if relative:

            path_label = ctk.CTkLabel(
                self.tree_scroll,
                text=f"{indent}   {relative}",
                font=get_font(SMALL),
                text_color=TEXT_MUTED,
                justify="left",
                anchor="w"
            )

            path_label.pack(
                anchor="w",
                padx=12,
                pady=(0, 6)
            )

        for child in node.get(
            "children",
            []
        ):

            self.render_tree_node(
                child,
                depth + 1
            )


    def abrir_importacion_request(
        self,
        node
    ):

        try:

            inferred = inferir_importacion_desde_bru(
                node.get("relative_path", ""),
                node.get("absolute_path", "")
            )

        except CatalogoServiciosError as error:

            MessageBox(
                self,
                str(error),
                "error"
            )
            return

        BrunoImportDialog(
            self,
            node,
            inferred,
            self.importar_request_catalogo
        )


    def importar_request_catalogo(
        self,
        node,
        data
    ):

        resultado = importar_request_bru_catalogo(
            relative_path=node.get("relative_path", ""),
            absolute_path=node.get("absolute_path", ""),
            service_name=data.get("service_name", ""),
            service_id=data.get("service_id", ""),
            transaction_name=data.get("transaction_name", ""),
            transaction_id=data.get("transaction_id", ""),
            version_label=data.get("version_label", ""),
            version_id=data.get("version_id", ""),
            libraries=data.get("libraries", ""),
            channel=data.get("channel", ""),
            repository_folder=data.get("repository_folder", "")
        )

        version_text = resultado.get(
            "version_label",
            ""
        ) or "Sin versión"

        MessageBox(
            self,
            (
                f"Request importada al catálogo.\n\n"
                f"Servicio: {resultado.get('service_id', '-') }\n"
                f"Transacción: {resultado.get('transaction_id', '-') }\n"
                f"Versión: {version_text}\n"
                f"Canal: {resultado.get('channel', '-') or 'Sin canal'}\n"
                f"Carpeta Jira: {resultado.get('repository_folder', '-') or 'Sin carpeta'}\n"
                f"Librerías: {', '.join(resultado.get('libraries', [])) or 'Sin librerías'}"
            ),
            "success"
        )


    def render_empty_state(
        self,
        text
    ):

        label = ctk.CTkLabel(
            self.tree_scroll,
            text=text,
            font=get_font(BODY),
            text_color=TEXT_MUTED,
            wraplength=900,
            justify="left"
        )

        label.pack(
            anchor="w",
            padx=14,
            pady=18
        )


class BrunoImportDialog(ctk.CTkToplevel):


    def __init__(
        self,
        parent,
        node,
        inferred,
        on_submit
    ):

        super().__init__(
            parent
        )

        self.node = node
        self.inferred = inferred
        self.on_submit = on_submit
        self.inputs = {}

        self.title(
            "Importar request Bruno"
        )
        self.geometry(
            "560x620"
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
            text="Importar request al catálogo",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        titulo.pack(
            anchor="w",
            padx=18,
            pady=(18, 10)
        )

        resumen = ctk.CTkLabel(
            card,
            text=(
                f"Archivo: {node.get('name', '')}\n"
                f"Ruta relativa: {node.get('relative_path', '')}"
            ),
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=500
        )

        resumen.pack(
            anchor="w",
            padx=18,
            pady=(0, 10)
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

        campos = [
            ("service_name", "Nombre del servicio", inferred.get("service_name", "")),
            ("service_id", "Id del servicio", inferred.get("service_id", "")),
            ("transaction_name", "Nombre de la transacción", inferred.get("transaction_name", "")),
            ("transaction_id", "Id de la transacción", inferred.get("transaction_id", "")),
            ("channel", "Canal", inferred.get("channel", "")),
            ("repository_folder", "Carpeta Jira/Xray", inferred.get("repository_folder", "")),
            ("libraries", "Librerías consumidas (separadas por coma)", inferred.get("libraries", "")),
            ("version_label", "Etiqueta de versión", inferred.get("version_label", "")),
            ("version_id", "Id de versión", inferred.get("version_id", ""))
        ]

        for key, label_text, default in campos:

            frame = ctk.CTkFrame(
                body,
                fg_color="transparent"
            )

            frame.pack(
                fill="x",
                padx=6,
                pady=(0, 10)
            )

            label = ctk.CTkLabel(
                frame,
                text=label_text,
                font=get_font(SMALL),
                text_color=TEXT_PRIMARY
            )

            label.pack(
                anchor="w",
                pady=(0, 4)
            )

            entry = ctk.CTkEntry(
                frame,
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

        importar = ctk.CTkButton(
            footer,
            text="Importar",
            width=120,
            height=38,
            corner_radius=19,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            command=self.submit
        )

        importar.pack(
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
                self.node,
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


