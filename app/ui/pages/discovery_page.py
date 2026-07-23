import customtkinter as ctk


from app.ui.pages.base_page import BasePage

from app.ui.components.message_box import MessageBox

from app.services.discovery_service import cargar_discovery
from app.services.metadata_service import cargar_metadata


from app.ui.theme.colors import (
    PRIMARY,
    BACKGROUND,
    TEXT_SECONDARY,
    SURFACE
)


from app.ui.theme.typography import (
    TITLE,
    BODY,
    get_font
)



class DiscoveryPage(BasePage):


    def __init__(
        self,
        parent,
        app,
        crq=None
    ):

        self.crq = crq
        self.discovery = None
        self.metadata_actual = {
            "objects": {}
        }

        super().__init__(
            parent,
            app
        )



    def build(self):


        self.cargar_estado_actual()


        self.configure(
            fg_color=BACKGROUND
        )


        self.crear_ui()



    def crear_ui(self):


        titulo = ctk.CTkLabel(
            self,
            text="Descubrimiento técnico",
            font=get_font(TITLE),
            text_color=PRIMARY
        )


        titulo.pack(
            pady=(40,20)
        )



        crq_text = ctk.CTkLabel(
            self,
            text=self.obtener_nombre_crq(),
            font=get_font(BODY)
        )


        crq_text.pack(
            pady=10
        )



        estado = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=10
        )


        estado.pack(
            padx=50,
            pady=30,
            fill="x"
        )



        label = ctk.CTkLabel(
            estado,
            text=self.obtener_resumen_estado(),
            font=get_font(BODY),
            justify="left"
        )


        label.pack(
            padx=30,
            pady=30
        )



        boton = ctk.CTkButton(
            self,
            text=(
                "Revisar metadata detectada"
                if self.discovery
                else "Ejecutar descubrimiento"
            ),
            fg_color=PRIMARY,
            command=(
                self.abrir_metadata
                if self.discovery
                else self.ejecutar_discovery
            )
        )


        boton.pack(
            pady=20
        )


        boton_metadata = ctk.CTkButton(
            self,
            text="Abrir metadata",
            fg_color="transparent",
            text_color=PRIMARY,
            command=self.abrir_metadata
        )


        boton_metadata.pack(
            pady=(0, 10)
        )


    def cargar_estado_actual(self):


        if not self.crq:

            return


        self.discovery = cargar_discovery(
            self.crq["crq"]
        )

        self.metadata_actual = cargar_metadata(
            self.crq["crq"]
        )


    def obtener_resumen_estado(self):


        lineas = [
            "Estado actual:",
            "",
            "● CRQ seleccionado" if self.crq else "○ Sin CRQ seleccionado",
            (
                "● Discovery disponible"
                if self.discovery
                else "○ Sin discovery almacenado"
            ),
            (
                "● Metadata funcional registrada"
                if self.tiene_metadata()
                else "○ Metadata pendiente"
            ),
            "○ Listo para Xray" if self.discovery and self.tiene_metadata() else "○ Flujo Xray pendiente"
        ]

        return "\n".join(lineas)


    def tiene_metadata(self):


        return bool(
            self.metadata_actual.get(
                "objects",
                {}
            )
        )



    def obtener_nombre_crq(self):


        if self.crq:

            return (
                f"CRQ seleccionado: "
                f"{self.crq.get('crq')}"
            )


        return "Sin CRQ seleccionado"



    def ejecutar_discovery(self):

        MessageBox(
            self,
            (
                "La ejecución automática de discovery con Bruno "
                "aún no está implementada.\n\n"
                "Cuando exista un discovery guardado para este CRQ, "
                "podrás continuar a metadata desde esta pantalla."
            ),
            "warning"
        )


    def abrir_metadata(self):


        self.navigate(
            "metadata",
            crq=self.crq,
            discovery=self.discovery
        )
