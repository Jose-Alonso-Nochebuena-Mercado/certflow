import webbrowser

import customtkinter as ctk

from app.ui.pages.base_page import BasePage

from app.services.crq_service import (
    normalizar_certificaciones
)

from app.services.config_service import (
    obtener_mapa_typology
)

from app.services.discovery_service import (
    cargar_discovery
)

from app.services.metadata_service import (
    cargar_metadata
)

from app.services.planning_service import (
    obtener_o_generar_planning
)

from app.services.xray_service import (
    obtener_enlace_jira
)

from app.ui.theme.colors import (
    PRIMARY,
    PRIMARY_LIGHT,
    PRIMARY_SOFT,
    SECONDARY_HOVER,
    BACKGROUND,
    SURFACE,
    SURFACE_ALT,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_SOFT
)

from app.ui.theme.typography import (
    TITLE,
    SUBTITLE,
    BODY,
    SMALL,
    get_font
)

from app.ui.theme.dimensions import (
    PAGE_HORIZONTAL_PADDING
)


class CRQDetailPage(BasePage):


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
        self.planning = []

        super().__init__(
            parent,
            app
        )


    def build(self):

        self.configure(
            fg_color=BACKGROUND
        )

        self.cargar_datos()
        self.crear_ui()


    def cargar_datos(self):

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

        planning_data = obtener_o_generar_planning(
            self.crq,
            self.metadata_actual,
            self.discovery_actual
        )

        self.planning = planning_data.get(
            "plans",
            []
        )


    def crear_ui(self):

        self.crear_resumen()
        self.crear_planning()


    def crear_resumen(self):

        hero = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        hero.pack(
            fill="x",
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(28, 16)
        )

        acciones = ctk.CTkFrame(
            hero,
            fg_color="transparent"
        )

        acciones.pack(
            anchor="e",
            pady=(0, 12)
        )

        agregar = ctk.CTkButton(
            acciones,
            text="Añadir tests",
            width=118,
            height=36,
            corner_radius=18,
            fg_color=PRIMARY_SOFT,
            hover_color=SECONDARY_HOVER,
            text_color=PRIMARY,
            border_width=1,
            border_color=BORDER,
            command=self.agregar_tests
        )

        agregar.pack(
            side="right"
        )

        discovery = ctk.CTkButton(
            acciones,
            text="Discovery",
            width=100,
            height=36,
            corner_radius=18,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            command=self.ir_discovery
        )

        discovery.pack(
            side="right",
            padx=(0, 10)
        )

        titulo = ctk.CTkLabel(
            hero,
            text=self.crq.get(
                "crq",
                "CRQ sin identificar"
            ),
            font=get_font(TITLE),
            text_color=PRIMARY
        )

        titulo.pack()

        subtitulo = ctk.CTkLabel(
            hero,
            text="Estructura actual del test planning asociado",
            font=get_font(BODY),
            text_color=TEXT_SECONDARY
        )

        subtitulo.pack(
            pady=(10, 0)
        )

        resumen = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=20,
            border_width=1,
            border_color=BORDER
        )

        resumen.pack(
            fill="x",
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(0, 18)
        )

        contenido = ctk.CTkFrame(
            resumen,
            fg_color="transparent"
        )

        contenido.pack(
            fill="x",
            padx=24,
            pady=22
        )

        izquierda = ctk.CTkFrame(
            contenido,
            fg_color="transparent"
        )

        izquierda.pack(
            side="left",
            fill="x",
            expand=True
        )

        derecha = ctk.CTkFrame(
            contenido,
            fg_color="transparent"
        )

        derecha.pack(
            side="right",
            anchor="n"
        )

        descripcion = self.crq.get(
            "descripcion",
            "Sin descripción"
        )

        detalle = ctk.CTkLabel(
            izquierda,
            text=(
                f"SDATOOL: {self.crq.get('sdatool', '-')}\n"
                f"Portafolio: {self.crq.get('portafolio', '-')}\n"
                f"Fecha de instalación: {self.crq.get('fecha_instalacion', '-')}\n"
                f"Descripción: {descripcion}"
            ),
            font=get_font(BODY),
            text_color=TEXT_PRIMARY,
            justify="left"
        )

        detalle.pack(
            anchor="w"
        )

        badges = ctk.CTkFrame(
            izquierda,
            fg_color="transparent"
        )

        badges.pack(
            anchor="w",
            pady=(14, 0)
        )

        self.crear_badges_tipologia(
            badges
        )

        jira_url = obtener_enlace_jira(
            self.crq.get(
                "crq",
                ""
            )
        )

        if jira_url:

            jira_boton = ctk.CTkButton(
                derecha,
                text="Abrir Jira",
                width=108,
                height=36,
                corner_radius=18,
                fg_color=PRIMARY_SOFT,
                hover_color="#DCE8F7",
                text_color=PRIMARY,
                border_width=1,
                border_color=BORDER,
                command=lambda: webbrowser.open(jira_url)
            )

            jira_boton.pack(
                anchor="e"
            )

            jira_texto = ctk.CTkLabel(
                derecha,
                text=jira_url,
                font=get_font(SMALL),
                text_color=TEXT_MUTED
            )

            jira_texto.pack(
                anchor="e",
                pady=(8, 0)
            )

        else:

            estado = ctk.CTkLabel(
                derecha,
                text="Jira no configurado",
                font=get_font(BODY),
                fg_color=SURFACE_ALT,
                text_color=TEXT_SECONDARY,
                corner_radius=14,
                padx=12,
                pady=6
            )

            estado.pack(
                anchor="e"
            )

            ayuda = ctk.CTkLabel(
                derecha,
                text="Define `jira_base_url` en `config/ui.json`",
                font=get_font(SMALL),
                text_color=TEXT_MUTED
            )

            ayuda.pack(
                anchor="e",
                pady=(8, 0)
            )


    def crear_badges_tipologia(self, parent):

        mapa_tipos = obtener_mapa_typology()

        for certificacion in normalizar_certificaciones(
            self.crq.get(
                "certificaciones",
                []
            )
        ):

            badge = ctk.CTkLabel(
                parent,
                text=mapa_tipos.get(
                    certificacion,
                    certificacion
                ),
                font=(
                    "Arial",
                    11,
                    "normal"
                ),
                fg_color=ACCENT_SOFT,
                text_color=PRIMARY,
                corner_radius=11,
                padx=8,
                pady=3
            )

            badge.pack(
                side="left",
                padx=(0, 6)
            )


    def crear_planning(self):

        contenedor = ctk.CTkScrollableFrame(
            self,
            fg_color=SURFACE,
            corner_radius=22,
            border_width=1,
            border_color=BORDER,
            height=420
        )

        contenedor.pack(
            fill="both",
            expand=True,
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(0, 28)
        )

        interior = ctk.CTkFrame(
            contenedor,
            fg_color="transparent"
        )

        interior.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        for plan in self.planning:

            self.crear_plan_card(
                interior,
                plan
            )


    def crear_plan_card(self, parent, plan):

        card = ctk.CTkFrame(
            parent,
            fg_color=SURFACE_ALT,
            corner_radius=18,
            border_width=1,
            border_color=BORDER
        )

        card.pack(
            fill="x",
            pady=(0, 14)
        )

        header = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=20,
            pady=(18, 12)
        )

        titulo = ctk.CTkLabel(
            header,
            text=plan["nombre"],
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        titulo.pack(
            side="left",
            anchor="w"
        )

        tipo = ctk.CTkLabel(
            header,
            text=plan["tipo_nombre"],
            font=get_font(SMALL),
            fg_color=PRIMARY_SOFT,
            text_color=PRIMARY,
            corner_radius=12,
            padx=10,
            pady=4
        )

        tipo.pack(
            side="right"
        )

        for test_set in plan.get(
            "test_sets",
            []
        ):

            self.crear_test_set(
                card,
                test_set
            )


    def crear_test_set(self, parent, test_set):

        frame = ctk.CTkFrame(
            parent,
            fg_color=SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=BORDER
        )

        frame.pack(
            fill="x",
            padx=18,
            pady=(0, 14)
        )

        titulo = ctk.CTkLabel(
            frame,
            text=test_set["nombre"],
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        titulo.pack(
            anchor="w",
            padx=16,
            pady=(14, 6)
        )

        subtitulo = ctk.CTkLabel(
            frame,
            text=f"Objeto: {test_set['path']}",
            font=get_font(SMALL),
            text_color=TEXT_MUTED
        )

        subtitulo.pack(
            anchor="w",
            padx=16,
            pady=(0, 10)
        )

        source = test_set.get(
            "source",
            {}
        )

        if source:

            version = source.get(
                "version_label"
            ) or "Sin versión"
            canal = source.get(
                "transaction_channel"
            ) or "Sin canal"
            carpeta = source.get(
                "repository_folder"
            ) or "Sin carpeta"
            librerias = ", ".join(
                source.get(
                    "transaction_libraries",
                    []
                )
            ) or "Sin librerías"

            origen = ctk.CTkLabel(
                frame,
                text=(
                    f"Origen: {source.get('service_name', '-')} / "
                    f"{version}\n"
                    f"Canal: {canal} · Carpeta Jira: {carpeta}\n"
                    f"Librerías: {librerias}"
                ),
                font=get_font(SMALL),
                text_color=TEXT_SECONDARY,
                justify="left"
            )

            origen.pack(
                anchor="w",
                padx=16,
                pady=(0, 10)
            )

        for test in test_set.get(
            "tests",
            []
        ):

            self.crear_test_row(
                frame,
                test
            )


    def crear_test_row(self, parent, test):

        fila = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        fila.pack(
            fill="x",
            padx=16,
            pady=(0, 8)
        )

        nombre = ctk.CTkLabel(
            fila,
            text=f"• {test['nombre']}",
            font=get_font(SMALL),
            text_color=TEXT_PRIMARY,
            justify="left",
            wraplength=680
        )

        nombre.pack(
            side="left",
            anchor="w"
        )

        estado = ctk.CTkLabel(
            fila,
            text=test["estado"],
            font=get_font(SMALL),
            fg_color=PRIMARY_SOFT,
            text_color=PRIMARY,
            corner_radius=12,
            padx=10,
            pady=4
        )

        estado.pack(
            side="right",
            anchor="e"
        )


    def ir_discovery(self):

        self.navigate(
            "discovery",
            crq=self.crq
        )


    def agregar_tests(self):

        self.navigate(
            "add_tests",
            crq=self.crq
        )

