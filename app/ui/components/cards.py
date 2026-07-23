import customtkinter as ctk

from app.ui.theme.theme import *


class ActionCard(ctk.CTkFrame):


    def __init__(
            self,
            parent,
            title,
            description,
            command
        ):


        super().__init__(

            parent,

            width=260,

            height=200,

            fg_color=SURFACE,

            corner_radius=15

        )


        self.grid_propagate(False)



        lbl = ctk.CTkLabel(

            self,

            text=title,

            font=(
                "Arial",
                18,
                "bold"
            ),

            text_color=TEXT_PRIMARY

        )


        lbl.pack(
            pady=20
        )


        desc = ctk.CTkLabel(

            self,

            text=description,

            wraplength=220,

            text_color=TEXT_SECONDARY

        )


        desc.pack()



        btn = ctk.CTkButton(

            self,

            text="Abrir",

            command=command,

            fg_color=PRIMARY

        )


        btn.pack(

            pady=20

        )