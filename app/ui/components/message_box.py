import customtkinter as ctk


from app.ui.theme.colors import (
    SUCCESS,
    ERROR,
    WARNING,
    SURFACE,
    BACKGROUND
)


from app.ui.theme.typography import (
    BODY,
    get_font
)

from app.ui.theme.dimensions import (
    MESSAGE_BOX_WIDTH,
    MESSAGE_BOX_HEIGHT
)

from app.ui.theme.styles import (
    SOFT_CARD_STYLE
)



class MessageBox(ctk.CTkToplevel):


    def __init__(
        self,
        parent,
        mensaje,
        tipo="success"
    ):


        super().__init__(
            parent
        )


        self.geometry(
            f"{MESSAGE_BOX_WIDTH}x{MESSAGE_BOX_HEIGHT}"
        )


        self.resizable(
            False,
            False
        )


        self.configure(
            fg_color=BACKGROUND
        )


        colores = {

            "success": SUCCESS,

            "error": ERROR,

            "warning": WARNING
        }


        color = colores.get(
            tipo,
            SUCCESS
        )


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


        label = ctk.CTkLabel(
            card,
            text=mensaje,
            font=get_font(BODY),
            text_color=SURFACE,
            fg_color=color,
            corner_radius=14,
            width=350,
            height=80
        )


        label.pack(
            expand=True,
            pady=24,
            padx=20
        )