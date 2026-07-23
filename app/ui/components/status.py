import customtkinter as ctk

from app.ui.theme.theme import *


class StatusCard(ctk.CTkFrame):


    def __init__(self,parent):

        super().__init__(

            parent,

            fg_color=SURFACE,

            corner_radius=15

        )


        title = ctk.CTkLabel(

            self,

            text="Estado del sistema",

            font=(
                "Arial",
                18,
                "bold"
            )

        )


        title.pack(
            pady=15
        )


        estados=[

            "🟢 Metadata disponible",

            "🟢 Colecciones Bruno cargadas",

            "🟢 Sistema listo"

        ]


        for e in estados:

            ctk.CTkLabel(

                self,

                text=e

            ).pack(

                anchor="w",

                padx=20,

                pady=5

            )