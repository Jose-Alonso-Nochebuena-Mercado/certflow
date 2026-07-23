import customtkinter as ctk

from app.ui.theme.colors import (
    SUCCESS,
    WARNING,
    TEXT_SECONDARY,
    PRIMARY
)

from app.ui.theme.typography import (
    BODY,
    get_font
)


class MetadataField(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        campo,
        estado,
        command=None
    ):

        super().__init__(
            parent,
            fg_color="transparent"
        )

        self.campo = campo
        self.estado = estado
        self.command = command

        self.crear_ui()


    def crear_ui(self):

        self.grid_columnconfigure(
            0,
            weight=1
        )


        nombre = ctk.CTkLabel(
            self,
            text=self.campo,
            font=get_font(BODY)
        )


        nombre.grid(
            row=0,
            column=0,
            padx=10,
            sticky="w"
        )


        colores = {

            "VALIDADO":
                SUCCESS,

            "NUEVO":
                WARNING,

            "SIN PRUEBAS":
                TEXT_SECONDARY

        }


        estado = ctk.CTkLabel(
            self,
            text=self.estado,
            text_color=colores.get(
                self.estado,
                TEXT_SECONDARY
            )
        )


        estado.grid(
            row=0,
            column=1,
            padx=10
        )


        self.crear_accion()



    def crear_accion(self):

        if self.estado == "VALIDADO":


            boton = ctk.CTkButton(
                self,
                text="Ver prueba",
                width=120,
                command=self.ejecutar
            )


            boton.grid(
                row=0,
                column=2,
                padx=10
            )


        elif self.estado == "NUEVO":


            boton = ctk.CTkButton(
                self,
                text="Crear escenario",
                width=140,
                fg_color=PRIMARY,
                command=self.ejecutar
            )


            boton.grid(
                row=0,
                column=2,
                padx=10
            )


        elif self.estado == "SIN PRUEBAS":


            boton = ctk.CTkButton(
                self,
                text="Crear escenario",
                width=140,
                command=self.ejecutar
            )


            boton.grid(
                row=0,
                column=2,
                padx=10
            )



    def ejecutar(self):

        if self.command:

            self.command(
                self.campo,
                self.estado
            )