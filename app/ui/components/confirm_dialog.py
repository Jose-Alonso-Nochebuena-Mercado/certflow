import customtkinter as ctk

from app.ui.theme.colors import (
    PRIMARY,
    ERROR,
    SURFACE,
    SURFACE_ALT,
    BORDER,
    PRIMARY_SOFT,
    SECONDARY_HOVER,
    ERROR_SOFT,
    ERROR_BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY
)


from app.ui.theme.typography import (
    TITLE,
    BODY,
    get_font
)

from app.ui.theme.dimensions import (
    DIALOG_WIDTH,
    DIALOG_HEIGHT
)

from app.ui.theme.styles import (
    SOFT_CARD_STYLE,
    SOFT_BADGE_STYLE
)



class ConfirmDialog(ctk.CTkToplevel):


    def __init__(
        self,
        parent,
        titulo,
        mensaje,
        on_confirm
    ):


        super().__init__(
            parent
        )


        self.on_confirm = on_confirm


        self.title(
            titulo
        )


        self.geometry(
            f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}"
        )


        self.resizable(
            False,
            False
        )


        self.configure(
            fg_color=SURFACE
        )


        self.crear_ui(
            mensaje
        )


        self.transient(
            parent
        )


        self.grab_set()



    def crear_ui(
        self,
        mensaje
    ):

        card = ctk.CTkFrame(
            self,
            **SOFT_CARD_STYLE
        )

        card.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=22
        )


        badge = ctk.CTkLabel(
            card,
            text="Acción delicada",
            font=get_font(BODY),
            fg_color=ERROR_SOFT,
            text_color=ERROR,
            **SOFT_BADGE_STYLE
        )

        badge.pack(
            pady=(22, 14)
        )


        titulo = ctk.CTkLabel(
            card,
            text="Eliminar CRQ",
            font=get_font(TITLE),
            text_color=PRIMARY
        )


        titulo.pack(
            pady=(0, 12)
        )



        texto = ctk.CTkLabel(
            card,
            text=mensaje,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY,
            wraplength=350,
            justify="center"
        )


        texto.pack(
            pady=(0, 24)
        )



        botones = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )


        botones.pack(
            pady=(0, 20)
        )



        cancelar = ctk.CTkButton(
            botones,
            text="Cancelar",
            width=130,
            height=38,
            corner_radius=19,
            fg_color=PRIMARY_SOFT,
            hover_color=SECONDARY_HOVER,
            text_color=PRIMARY,
            border_width=1,
            border_color=BORDER,
            command=self.destroy
        )


        cancelar.grid(
            row=0,
            column=0,
            padx=10
        )



        eliminar = ctk.CTkButton(
            botones,
            text="Eliminar",
            width=130,
            height=38,
            corner_radius=19,
            fg_color=ERROR,
            hover_color="#B3261E",
            text_color=SURFACE,
            border_width=1,
            border_color=ERROR_BORDER,
            command=self.confirmar
        )


        eliminar.grid(
            row=0,
            column=1,
            padx=10
        )



    def confirmar(self):


        self.on_confirm()


        self.destroy()