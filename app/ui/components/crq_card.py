import customtkinter as ctk

from app.services.config_service import obtener_mapa_typology
from app.services.crq_service import normalizar_certificaciones

from app.ui.theme.colors import (
    PRIMARY,
    PRIMARY_LIGHT,
    PRIMARY_SOFT,
    SURFACE,
    SURFACE_ALT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ERROR,
    ERROR_SOFT,
    ERROR_BORDER,
    ACCENT_SOFT,
    BORDER
)

from app.ui.theme.typography import (
    SUBTITLE,
    BODY,
    SMALL,
    get_font
)


class CRQCard(ctk.CTkFrame):


    def __init__(
        self,
        parent,
        crq,
        callback_continuar,
        callback_eliminar,
        callback_agregar
    ):


        super().__init__(
            parent,
            width=320,
            height=210,
            fg_color=SURFACE,
            corner_radius=18,
            border_width=1,
            border_color=BORDER
        )


        self.grid_propagate(False)

        self.crq = crq
        self.callback_continuar = callback_continuar
        self.callback_eliminar = callback_eliminar
        self.callback_agregar = callback_agregar

        self.typology_map = obtener_mapa_typology()


        self.crear_ui()


    def crear_ui(self):


        contenedor = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        contenedor.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )


        header = ctk.CTkFrame(
            contenedor,
            fg_color="transparent"
        )

        header.pack(
            fill="x"
        )


        titulo = ctk.CTkLabel(
            header,
            text=self.crq.get("crq"),
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        titulo.pack(
            side="left",
            anchor="w"
        )


        info = ctk.CTkFrame(
            contenedor,
            fg_color="transparent"
        )

        info.pack(
            fill="x",
            pady=(16, 10)
        )


        sdatool = ctk.CTkLabel(
            info,
            text=self.crq.get(
                "sdatool",
                "Sin SDATOOL"
            ),
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        sdatool.pack(
            anchor="w"
        )


        portafolio = ctk.CTkLabel(
            info,
            text=self.crq.get(
                "portafolio",
                "Sin portafolio"
            ),
            font=get_font(SMALL),
            fg_color=SURFACE_ALT,
            text_color=TEXT_SECONDARY,
            corner_radius=12,
            padx=10,
            pady=4
        )

        portafolio.pack(
            anchor="w",
            pady=(8, 0)
        )


        descripcion = ctk.CTkLabel(
            contenedor,
            text=self.crq.get(
                "descripcion",
                "Sin descripción"
            ),
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            wraplength=248,
            justify="left"
        )

        descripcion.pack(
            anchor="w",
            pady=(0, 12)
        )


        footer = ctk.CTkFrame(
            contenedor,
            fg_color="transparent"
        )

        footer.pack(
            fill="x"
        )


        badges = ctk.CTkFrame(
            footer,
            fg_color="transparent"
        )

        badges.pack(
            fill="x",
            anchor="w"
        )

        self.crear_badges_certificacion(
            badges
        )


        acciones = ctk.CTkFrame(
            contenedor,
            fg_color="transparent"
        )

        acciones.pack(
            fill="x",
            pady=(12, 0)
        )


        eliminar = ctk.CTkButton(
            acciones,
            text="✕",
            width=32,
            height=32,
            corner_radius=16,
            font=(
                "Arial",
                14,
                "bold"
            ),
            fg_color=ERROR_SOFT,
            text_color=ERROR,
            hover_color="#F9DADB",
            border_width=1,
            border_color=ERROR_BORDER,
            command=self.eliminar
        )

        eliminar.pack(
            side="left"
        )


        agregar = ctk.CTkButton(
            acciones,
            text="+",
            width=32,
            height=32,
            corner_radius=16,
            font=(
                "Arial",
                15,
                "bold"
            ),
            fg_color=PRIMARY_SOFT,
            text_color=PRIMARY,
            hover_color="#DCE8F7",
            border_width=1,
            border_color=BORDER,
            command=self.agregar
        )

        agregar.pack(
            side="left",
            padx=(8, 0)
        )


        continuar = ctk.CTkButton(
            acciones,
            text="Abrir",
            width=72,
            height=32,
            corner_radius=16,
            font=(
                "Arial",
                12,
                "bold"
            ),
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            command=self.continuar
        )

        continuar.pack(
            side="right"
        )


    def crear_badges_certificacion(
        self,
        parent
    ):


        certificaciones = normalizar_certificaciones(
            self.crq.get(
                "certificaciones",
                []
            )
        )


        if not certificaciones:

            badge = ctk.CTkLabel(
                parent,
                text="Sin tipología",
                font=get_font(SMALL),
                text_color=TEXT_MUTED
            )

            badge.pack(
                side="left"
            )

            return


        for certificacion in certificaciones[:2]:

            badge = ctk.CTkLabel(
                parent,
                text=self.typology_map.get(
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


        if len(certificaciones) > 2:

            extra = ctk.CTkLabel(
                parent,
                text=f"+{len(certificaciones) - 2}",
                font=(
                    "Arial",
                    11,
                    "normal"
                ),
                fg_color=SURFACE_ALT,
                text_color=TEXT_MUTED,
                corner_radius=11,
                padx=7,
                pady=3
            )

            extra.pack(
                side="left"
            )


    def continuar(self):


        self.callback_continuar(
            self.crq
        )



    def eliminar(self):


        self.callback_eliminar(
            self.crq
        )


    def agregar(self):


        self.callback_agregar(
            self.crq
        )
