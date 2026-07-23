import customtkinter as ctk
from datetime import datetime

from app.ui.pages.base_page import BasePage

from models.crq_model import CRQ

from app.ui.theme.colors import (
    PRIMARY,
    PRIMARY_LIGHT,
    PRIMARY_SOFT,
    BACKGROUND,
    SURFACE,
    SURFACE_ALT,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED
)
from app.ui.theme.typography import (
    TITLE,
    SUBTITLE,
    BODY,
    SMALL,
    get_font
)
from app.ui.theme.dimensions import (
    FORM_INPUT_WIDTH,
    FORM_CARD_WIDTH,
    FORM_PADDING_HORIZONTAL,
    BUTTON_HEIGHT
)
from app.ui.theme.styles import (
    SECONDARY_BUTTON,
    SOFT_CARD_STYLE
)

from app.services.crq_service import (
    contiene_caracteres_invalidos_crq,
    guardar_crq,
    existe_crq
)

from app.services.config_service import (
    obtener_portafolios,
    obtener_typology
)

from app.ui.components.message_box import MessageBox
from app.ui.components.date_picker import DatePicker


class NewCRQPage(BasePage):


    def build(self):

        self.portafolios = obtener_portafolios()
        self.tipos = obtener_typology()

        self.configure(
            fg_color=BACKGROUND
        )

        self.crear_ui()


    def crear_ui(self):

        self.crear_hero()

        self.form_card = ctk.CTkFrame(
            self,
            width=FORM_CARD_WIDTH,
            **SOFT_CARD_STYLE
        )

        self.form_card.pack(
            fill="both",
            expand=True,
            padx=FORM_PADDING_HORIZONTAL,
            pady=(0, 24)
        )

        cuerpo = ctk.CTkScrollableFrame(
            self.form_card,
            fg_color="transparent"
        )

        cuerpo.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=(8, 0)
        )

        contenido = ctk.CTkFrame(
            cuerpo,
            fg_color="transparent"
        )

        contenido.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        contenido.grid_columnconfigure(
            0,
            weight=1,
            uniform="new_crq_cols"
        )

        contenido.grid_columnconfigure(
            1,
            weight=1,
            uniform="new_crq_cols"
        )

        izquierda = ctk.CTkFrame(
            contenido,
            fg_color="transparent"
        )

        izquierda.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 12)
        )

        derecha = ctk.CTkFrame(
            contenido,
            fg_color="transparent"
        )

        derecha.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(12, 0)
        )

        self.crear_seccion_generales(
            izquierda
        )

        self.crear_seccion_tipologias(
            izquierda
        )

        self.descripcion = self.crear_campo_descripcion(
            derecha,
            "Descripción",
            height=220,
            helper_text="Puede dejar notas amplias del CRQ; este campo tiene scroll interno."
        )

        self.crear_footer(
            self.form_card
        )


    def crear_hero(self):

        hero = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        hero.pack(
            fill="x",
            padx=FORM_PADDING_HORIZONTAL,
            pady=(28, 14)
        )

        titulo = ctk.CTkLabel(
            hero,
            text="Nuevo CRQ",
            font=get_font(TITLE),
            text_color=PRIMARY
        )

        titulo.pack()

        descripcion = ctk.CTkLabel(
            hero,
            text="Capture la información base para comenzar el planning de certificación.",
            font=get_font(BODY),
            text_color=TEXT_SECONDARY
        )

        descripcion.pack(
            pady=(8, 0)
        )


    def crear_seccion_generales(self, parent):

        encabezado = self.crear_encabezado_seccion(
            parent,
            "Datos generales",
            "Información principal del CRQ y del portafolio asociado."
        )

        encabezado.pack(
            fill="x"
        )

        grid = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        grid.pack(
            fill="x",
            pady=(16, 8)
        )

        grid.grid_columnconfigure(
            0,
            weight=1,
            uniform="form_cols"
        )
        grid.grid_columnconfigure(
            1,
            weight=1,
            uniform="form_cols"
        )

        self.sdatool = self.crear_campo_texto(
            grid,
            0,
            0,
            "SDATOOL"
        )

        self.crq = self.crear_campo_texto(
            grid,
            0,
            1,
            "CRQ"
        )

        self.portafolio = self.crear_campo_combo(
            grid,
            1,
            0,
            "Portafolio",
            self.obtener_valores_portafolio()
        )

        self.fecha = self.crear_campo_fecha(
            grid,
            1,
            1,
            "Fecha instalación"
        )

        if self.portafolios:

            self.portafolio.set(
                self.portafolios[0]
            )

    def crear_seccion_tipologias(self, parent):

        encabezado = self.crear_encabezado_seccion(
            parent,
            "Typology",
            "Seleccione una o varias certificaciones que formarán parte del test planning."
        )

        encabezado.pack(
            fill="x"
        )

        self.typologies = {}

        opciones = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        opciones.pack(
            fill="x",
            pady=(14, 0)
        )

        for columna in range(2):

            opciones.grid_columnconfigure(
                columna,
                weight=1,
                uniform="typology_cols"
            )

        for indice, tipo in enumerate(self.tipos):

            variable = ctk.BooleanVar()

            tarjeta = ctk.CTkFrame(
                opciones,
                fg_color=SURFACE_ALT,
                corner_radius=16,
                border_width=1,
                border_color=BORDER
            )

            tarjeta.grid(
                row=indice // 2,
                column=indice % 2,
                padx=6,
                pady=(0, 10),
                sticky="ew"
            )

            check = ctk.CTkCheckBox(
                tarjeta,
                text=tipo["nombre"],
                variable=variable,
                font=get_font(BODY),
                checkbox_width=18,
                checkbox_height=18,
                fg_color=PRIMARY,
                hover_color=PRIMARY_LIGHT,
                border_color=PRIMARY,
                text_color=TEXT_PRIMARY
            )

            check.pack(
                anchor="w",
                padx=16,
                pady=(10, 2)
            )

            label = ctk.CTkLabel(
                tarjeta,
                text=tipo["label"],
                font=get_font(SMALL),
                text_color=TEXT_MUTED
            )

            label.pack(
                anchor="w",
                padx=42,
                pady=(0, 10)
            )

            self.typologies[
                tipo["id"]
            ] = variable


    def crear_footer(self, parent):

        footer = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        footer.pack(
            fill="x",
            side="bottom",
            anchor="s",
            padx=28,
            pady=(12, 18)
        )

        cancelar = ctk.CTkButton(
            footer,
            text="Cancelar",
            width=130,
            height=BUTTON_HEIGHT,
            corner_radius=20,
            command=self.go_back,
            **SECONDARY_BUTTON
        )

        cancelar.pack(
            side="right"
        )

        crear = ctk.CTkButton(
            footer,
            text="Crear CRQ",
            width=140,
            height=BUTTON_HEIGHT,
            corner_radius=20,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            text_color=BACKGROUND,
            command=self.crear_crq
        )

        crear.pack(
            side="right",
            padx=(0, 10)
        )


    def crear_encabezado_seccion(
        self,
        parent,
        titulo,
        descripcion
    ):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        titulo_label = ctk.CTkLabel(
            frame,
            text=titulo,
            font=get_font(SUBTITLE),
            text_color=TEXT_PRIMARY
        )

        titulo_label.pack(
            anchor="w"
        )

        descripcion_label = ctk.CTkLabel(
            frame,
            text=descripcion,
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY
        )

        descripcion_label.pack(
            anchor="w",
            pady=(6, 0)
        )

        return frame


    def crear_campo_texto(
        self,
        parent,
        row,
        column,
        titulo
    ):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.grid(
            row=row,
            column=column,
            padx=10,
            pady=10,
            sticky="ew"
        )

        label = ctk.CTkLabel(
            frame,
            text=titulo,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        label.pack(
            anchor="w",
            pady=(0, 6)
        )

        entrada = ctk.CTkEntry(
            frame,
            width=FORM_INPUT_WIDTH,
            height=42,
            corner_radius=14,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
            text_color=TEXT_PRIMARY
        )

        entrada.pack(
            fill="x"
        )

        return entrada


    def crear_campo_combo(
        self,
        parent,
        row,
        column,
        titulo,
        valores
    ):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.grid(
            row=row,
            column=column,
            padx=10,
            pady=10,
            sticky="ew"
        )

        label = ctk.CTkLabel(
            frame,
            text=titulo,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        label.pack(
            anchor="w",
            pady=(0, 6)
        )

        combo = ctk.CTkComboBox(
            frame,
            values=valores,
            width=FORM_INPUT_WIDTH,
            height=42,
            corner_radius=14,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_LIGHT,
            dropdown_fg_color=SURFACE,
            dropdown_hover_color=PRIMARY_SOFT,
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY
        )

        combo.pack(
            fill="x"
        )

        return combo


    def crear_campo_fecha(
        self,
        parent,
        row,
        column,
        titulo
    ):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.grid(
            row=row,
            column=column,
            padx=10,
            pady=10,
            sticky="ew"
        )

        label = ctk.CTkLabel(
            frame,
            text=titulo,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        label.pack(
            anchor="w",
            pady=(0, 6)
        )

        picker = DatePicker(
            frame,
            initial_date=datetime.now().strftime(
                "%Y-%m-%d"
            ),
            width=FORM_INPUT_WIDTH,
            height=42
        )

        picker.pack(
            fill="x"
        )

        return picker


    def crear_campo_descripcion(
        self,
        parent,
        titulo,
        height=90,
        helper_text=None
    ):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.pack(
            fill="x",
            pady=(8, 0)
        )

        label = ctk.CTkLabel(
            frame,
            text=titulo,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        label.pack(
            anchor="w",
            pady=(0, 6)
        )

        if helper_text:

            helper = ctk.CTkLabel(
                frame,
                text=helper_text,
                font=get_font(SMALL),
                text_color=TEXT_MUTED
            )

            helper.pack(
                anchor="w",
                pady=(0, 8)
            )

        texto = ctk.CTkTextbox(
            frame,
            height=height,
            corner_radius=14,
            fg_color=SURFACE_ALT,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT_PRIMARY
        )

        texto.pack(
            fill="x"
        )

        return texto


    def crear_crq(self):

        datos = self.obtener_datos_formulario()

        mensaje_error = self.validar_formulario(
            datos
        )

        if mensaje_error:

            MessageBox(
                self,
                mensaje_error,
                "warning"
            )

            return

        if existe_crq(
            datos["crq"]
        ):

            MessageBox(
                self,
                f"El CRQ {datos['crq']} ya existe",
                "error"
            )

            return

        crq = CRQ(
            crq=datos["crq"],
            sdatool=datos["sdatool"],
            descripcion=datos["descripcion"],
            portafolio=datos["portafolio"],
            fecha_instalacion=datos["fecha_instalacion"],
            certificaciones=datos["certificaciones"]
        )

        guardar_crq(
            datos["crq"],
            crq.to_dict()
        )

        crq_creado = {
            "crq": datos["crq"],
            **crq.to_dict()
        }

        MessageBox(
            self,
            (
                f"CRQ {datos['crq']} creado correctamente.\n\n"
                "Continuaremos con la selección de servicio y el armado inicial del planning."
            ),
            "success"
        )

        self.navigate(
            "add_tests",
            crq=crq_creado
        )


    def obtener_datos_formulario(self):

        return {
            "sdatool": self.sdatool.get().strip().upper(),
            "crq": self.crq.get().strip().upper(),
            "descripcion": self.descripcion.get(
                "1.0",
                "end"
            ).strip(),
            "portafolio": self.portafolio.get().strip(),
            "fecha_instalacion": self.fecha.get().strip(),
            "certificaciones": self.obtener_certificaciones_seleccionadas()
        }


    def obtener_certificaciones_seleccionadas(self):

        return [
            typology_id
            for typology_id, variable in self.typologies.items()
            if variable.get()
        ]


    def validar_formulario(self, datos):

        if not datos["sdatool"]:

            return "Debe ingresar SDATOOL"

        if not datos["crq"]:

            return "Debe ingresar CRQ"

        if contiene_caracteres_invalidos_crq(
            datos["crq"]
        ):

            return "El CRQ contiene caracteres no válidos para Windows (por ejemplo: < > : \" / \\ | ? *)"

        if not datos["portafolio"] or datos["portafolio"] == "Sin portafolios configurados":

            return "Debe seleccionar un portafolio válido"

        if not datos["fecha_instalacion"]:

            return "Debe ingresar la fecha de instalación"

        if not self.fecha_valida(
            datos["fecha_instalacion"]
        ):

            return "La fecha debe tener formato YYYY-MM-DD"

        if not datos["certificaciones"]:

            return "Seleccione al menos una certificación"

        return None


    def obtener_valores_portafolio(self):

        if self.portafolios:

            return self.portafolios


        return [
            "Sin portafolios configurados"
        ]


    def fecha_valida(
        self,
        fecha
    ):

        try:

            datetime.strptime(
                fecha,
                "%Y-%m-%d"
            )

            return True

        except ValueError:

            return False
