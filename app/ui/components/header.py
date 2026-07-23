import customtkinter as ctk

from app.ui.theme.colors import (
    PRIMARY,
    BACKGROUND,
    HEADER_DIVIDER,
    HEADER_ACTION_SEPARATOR,
    TEXT_PRIMARY,
    BUTTON_DISABLED_TEXT
)

from app.ui.theme.typography import (
    TITLE,
    get_font
)

from app.ui.theme.dimensions import (
    HEADER_HEIGHT,
    HEADER_CONTENT_PADDING_X,
    HEADER_CONTENT_PADDING_Y,
    HEADER_LEFT_SLOT_WIDTH,
    HEADER_RIGHT_SLOT_WIDTH,
    HEADER_SLOT_HEIGHT
)

from app.ui.theme.styles import (
    HEADER_ACTION_GROUP,
    ICON_BUTTON_LIGHT
)


class Header(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        app
    ):

        super().__init__(
            parent,
            height=HEADER_HEIGHT,
            fg_color=PRIMARY
        )

        self.app = app

        self.crear_ui()



    def crear_ui(self):

        self.pack_propagate(False)

        contenido = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        contenido.pack(
            fill="both",
            expand=True,
            padx=HEADER_CONTENT_PADDING_X,
            pady=HEADER_CONTENT_PADDING_Y
        )

        contenido.grid_columnconfigure(
            0,
            weight=0
        )

        contenido.grid_columnconfigure(
            1,
            weight=1
        )

        contenido.grid_columnconfigure(
            2,
            weight=0
        )

        left_slot = ctk.CTkFrame(
            contenido,
            fg_color="transparent",
            width=HEADER_LEFT_SLOT_WIDTH,
            height=HEADER_SLOT_HEIGHT
        )

        left_slot.grid(
            row=0,
            column=0,
            sticky="w"
        )

        left_slot.grid_propagate(False)

        center_slot = ctk.CTkFrame(
            contenido,
            fg_color="transparent"
        )

        center_slot.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        center_slot.grid_columnconfigure(
            0,
            weight=1
        )

        right_slot = ctk.CTkFrame(
            contenido,
            fg_color="transparent",
            width=HEADER_RIGHT_SLOT_WIDTH,
            height=HEADER_SLOT_HEIGHT
        )

        right_slot.grid(
            row=0,
            column=2,
            sticky="e"
        )

        right_slot.grid_propagate(False)


        self.crear_marca_izquierda(
            left_slot
        )


        titulo = ctk.CTkLabel(
            center_slot,
            text="CertFlow",
            text_color=BACKGROUND,
            font=get_font(TITLE)
        )


        titulo.grid(
            row=0,
            column=0,
            pady=6,
            sticky="n"
        )



        self.crear_acciones_derecha(
            right_slot
        )


        divisor = ctk.CTkFrame(
            self,
            height=1,
            fg_color=HEADER_DIVIDER
        )

        divisor.pack(
            fill="x"
        )



    def crear_marca_izquierda(
        self,
        parent
    ):

        marca = ctk.CTkLabel(
            parent,
            text="BBVA",
            text_color=BACKGROUND,
            font=(
                "Arial",
                26,
                "bold"
            )
        )

        marca.pack(
            anchor="w",
            pady=6
        )


    def crear_acciones_derecha(
        self,
        parent
    ):

        contenedor = ctk.CTkFrame(
            parent,
            **HEADER_ACTION_GROUP
        )

        contenedor.pack(
            anchor="e",
            pady=2
        )

        self.btn_home = self.crear_boton_header(
            contenedor,
            text="⌂",
            command=self.ir_inicio
        )

        self.btn_home.pack(
            side="left",
            padx=(6, 4),
            pady=6
        )

        self.crear_separador_accion(
            contenedor
        )

        self.btn_back = self.crear_boton_header(
            contenedor,
            text="↶",
            command=self.ir_atras
        )

        self.btn_back.pack(
            side="left",
            padx=4,
            pady=6
        )

        self.crear_separador_accion(
            contenedor
        )

        self.btn_settings = self.crear_boton_header(
            contenedor,
            text="⚙",
            command=self.abrir_configuracion,
            destacado=True
        )

        self.btn_settings.pack(
            side="left",
            padx=(4, 6),
            pady=6
        )


    def crear_separador_accion(
        self,
        parent
    ):

        separador = ctk.CTkFrame(
            parent,
            width=1,
            height=20,
            fg_color=HEADER_ACTION_SEPARATOR
        )

        separador.pack(
            side="left",
            padx=2,
            pady=10
        )


    def crear_boton_header(
        self,
        parent,
        text,
        command,
        destacado=False
    ):

        return ctk.CTkButton(
            parent,
            text=text,
            font=(
                "Arial",
                16,
                "bold"
            ),
            command=command,
            **{
                **ICON_BUTTON_LIGHT,
                "fg_color": "#FFFFFF" if destacado else ICON_BUTTON_LIGHT["fg_color"]
            }
        )


    def ir_inicio(self):

        if not hasattr(
            self.app,
            "router"
        ):

            return

        self.app.router.navigate(
            "home",
            add_to_history=False
        )


    def ir_atras(self):

        if not hasattr(
            self.app,
            "router"
        ):

            return

        self.app.router.go_back()


    def refresh_navigation(self):

        if not hasattr(
            self,
            "btn_home"
        ) or not hasattr(
            self.app,
            "router"
        ):

            return

        en_home = self.app.router.current_route == "home"
        puede_regresar = bool(
            self.app.router.history
        )

        self.actualizar_estado_boton(
            self.btn_home,
            habilitado=not en_home,
            resaltado=en_home
        )

        self.actualizar_estado_boton(
            self.btn_back,
            habilitado=puede_regresar,
            resaltado=False
        )


    def actualizar_estado_boton(
        self,
        boton,
        habilitado,
        resaltado=False
    ):

        boton.configure(
            state="normal",
            fg_color=(
                "#EDF4FC"
                if resaltado
                else ICON_BUTTON_LIGHT["fg_color"]
            ),
            hover_color=ICON_BUTTON_LIGHT["hover_color"] if habilitado else ICON_BUTTON_LIGHT["fg_color"],
            text_color=TEXT_PRIMARY if habilitado or resaltado else BUTTON_DISABLED_TEXT,
            border_width=0,
            border_color=ICON_BUTTON_LIGHT["border_color"],
            command=(
                self.ir_inicio
                if boton is self.btn_home and habilitado
                else self.ir_atras
                if boton is self.btn_back and habilitado
                else (lambda: None)
            )
        )



    def abrir_configuracion(self):

        if not hasattr(
            self.app,
            "router"
        ):

            return

        self.app.router.navigate(
            "settings"
        )