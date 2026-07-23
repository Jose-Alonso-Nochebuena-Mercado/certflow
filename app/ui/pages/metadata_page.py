import customtkinter as ctk

from app.ui.pages.base_page import BasePage

from app.ui.theme.colors import (
    PRIMARY,
    BACKGROUND,
    SURFACE
)

from app.ui.theme.typography import (
    TITLE,
    BODY,
    get_font
)

from app.services.metadata_service import (
    comparar_metadata,
    cargar_metadata
)

from app.services.config_service import (
    obtener_mapa_typology
)

from app.services.crq_service import (
    normalizar_certificaciones
)

from app.ui.components.metadata_field import (
    MetadataField
)


class MetadataPage(BasePage):

    def __init__(
        self,
        parent,
        app,
        crq=None,
        discovery=None
    ):

        self.crq = crq
        self.discovery = discovery
        self.resultado = {}
        self.metadata_actual = {
            "objects": {}
        }

        super().__init__(
            parent,
            app
        )


    def build(self):

        self.configure(
            fg_color=BACKGROUND
        )

        self.analizar_metadata()
        self.crear_ui()


    def crear_ui(self):

        titulo = ctk.CTkLabel(
            self,
            text="Validación de metadata",
            font=get_font(TITLE),
            text_color=PRIMARY
        )

        titulo.pack(
            pady=(30, 20)
        )


        crq_label = ctk.CTkLabel(
            self,
            text=self.obtener_crq(),
            font=get_font(BODY)
        )

        crq_label.pack()


        detalle_crq = ctk.CTkLabel(
            self,
            text=self.obtener_detalle_crq(),
            font=get_font(BODY),
            justify="center"
        )

        detalle_crq.pack(
            pady=(8, 0)
        )


        self.contenedor = ctk.CTkScrollableFrame(
            self,
            fg_color=SURFACE,
            width=700,
            height=400
        )

        self.contenedor.pack(
            padx=40,
            pady=30,
            fill="both",
            expand=True
        )


        self.mostrar_objetos()


        boton = ctk.CTkButton(
            self,
            text="Continuar certificación",
            fg_color=PRIMARY,
            command=self.continuar
        )

        boton.pack(
            pady=20
        )


    def obtener_crq(self):

        if self.crq:

            return (
                f"CRQ: "
                f"{self.crq.get('crq')}"
            )

        return "Sin CRQ"


    def obtener_detalle_crq(self):

        if not self.crq:

            return ""


        certificaciones = self.crq.get(
            "certificaciones",
            []
        )

        certificaciones = normalizar_certificaciones(
            certificaciones
        )

        nombres_certificaciones = self.obtener_nombres_certificaciones(
            certificaciones
        )


        return (
            f"SDATOOL: {self.crq.get('sdatool', '-')}   |   "
            f"Portafolio: {self.crq.get('portafolio', '-')}   |   "
            f"Certificaciones: {', '.join(nombres_certificaciones) if nombres_certificaciones else '-'}"
        )


    def obtener_nombres_certificaciones(
        self,
        certificaciones
    ):

        mapa_tipos = obtener_mapa_typology()

        return [
            mapa_tipos.get(
                certificacion,
                certificacion
            )
            for certificacion in certificaciones
        ]


    def obtener_mensaje_vacio(self):

        if self.discovery:

            return "No existen diferencias entre el discovery y la metadata actual"


        if self.tiene_metadata_actual():

            return "Se encontró metadata funcional guardada, pero aún no hay discovery técnico para compararla"


        return "Este CRQ aún no tiene discovery técnico ni metadata funcional registrada"



    def mostrar_objetos(self):
        if not self.resultado:

            self.mostrar_mensaje(
                self.obtener_mensaje_vacio()
            )

            return


        for path, datos in self.resultado.items():

            self.crear_objeto_card(
                path,
                datos
            )



    def crear_objeto_card(
        self,
        path,
        datos
    ):


        frame = ctk.CTkFrame(
            self.contenedor,
            fg_color=SURFACE,
            corner_radius=10
        )


        frame.pack(
            fill="x",
            pady=10,
            padx=10
        )


        titulo = ctk.CTkLabel(
            frame,
            text=path,
            font=get_font(BODY),
            text_color=PRIMARY
        )


        titulo.pack(
            anchor="w",
            padx=20,
            pady=10
        )


        for campo in datos.get(
            "validated",
            []
        ):

            self.agregar_campo(
                frame,
                campo,
                "VALIDADO"
            )


        for campo in datos.get(
            "without_tests",
            []
        ):

            self.agregar_campo(
                frame,
                campo,
                "SIN PRUEBAS"
            )


        for campo in datos.get(
            "new",
            []
        ):

            self.agregar_campo(
                frame,
                campo,
                "NUEVO"
            )



    def agregar_campo(
        self,
        parent,
        campo,
        estado
    ):


        field = MetadataField(
            parent,
            campo,
            estado,
            self.accion_campo
        )


        field.pack(
            fill="x",
            pady=5
        )



    def accion_campo(
        self,
        campo,
        estado
    ):

        print(
            "Campo seleccionado:",
            campo,
            "Estado:",
            estado
        )


    def analizar_metadata(self):

        if not self.crq:

            return


        self.metadata_actual = cargar_metadata(
            self.crq["crq"]
        )


        if self.discovery:

            self.resultado = comparar_metadata(
                self.discovery,
                self.metadata_actual
            )

            return


        if self.tiene_metadata_actual():

            self.resultado = self.construir_resultado_desde_metadata()


    def tiene_metadata_actual(self):

        return bool(
            self.metadata_actual.get(
                "objects",
                {}
            )
        )


    def construir_resultado_desde_metadata(self):

        resultado = {}


        for path, datos in self.metadata_actual.get(
            "objects",
            {}
        ).items():

            resultado[path] = {
                "validated": datos.get(
                    "validated_fields",
                    []
                ),
                "without_tests": datos.get(
                    "ignored_fields",
                    []
                ),
                "new": []
            }


        return resultado



    def continuar(self):

        print(
            "Continuar con metadata"
        )



    def mostrar_mensaje(
        self,
        texto
    ):


        label = ctk.CTkLabel(
            self,
            text=texto,
            font=get_font(BODY)
        )


        label.pack(
            pady=50
        )