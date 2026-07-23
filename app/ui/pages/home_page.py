import customtkinter as ctk

from app.ui.pages.base_page import BasePage

from app.ui.theme.colors import (
    PRIMARY,
    PRIMARY_LIGHT,
    BACKGROUND,
    SURFACE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

from app.ui.theme.typography import (
    TITLE,
    SUBTITLE,
    BODY,
    get_font
)

from app.ui.theme.dimensions import (
    PAGE_HORIZONTAL_PADDING,
    CIRCULAR_BUTTON_SIZE,
    CIRCULAR_BUTTON_RADIUS
)

from app.services.crq_service import (
    listar_crqs,
    eliminar_crq as eliminar_crq_service
)

from app.ui.components.crq_card import (
    CRQCard
)

from app.ui.components.confirm_dialog import (
    ConfirmDialog
)

from app.ui.components.message_box import (
    MessageBox
)

class HomePage(BasePage):


    def build(self):

        self.configure(
            fg_color=BACKGROUND
        )

        self.crear_contenido()



    def crear_contenido(self):
        top_section = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )


        top_section.pack(
            fill="x",
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(36, 16)
        )


        top_section.grid_columnconfigure(
            0,
            weight=0
        )

        top_section.grid_columnconfigure(
            1,
            weight=1
        )

        top_section.grid_columnconfigure(
            2,
            weight=0
        )


        left_slot = ctk.CTkFrame(
            top_section,
            fg_color="transparent",
            width=140,
            height=50
        )

        left_slot.grid(
            row=0,
            column=0,
            sticky="w"
        )

        left_slot.grid_propagate(False)

        hero = ctk.CTkFrame(
            top_section,
            fg_color="transparent"
        )

        hero.grid(
            row=0,
            column=1,
            sticky="n"
        )

        right_slot = ctk.CTkFrame(
            top_section,
            fg_color="transparent",
            width=140,
            height=50
        )

        right_slot.grid(
            row=0,
            column=2,
            sticky="e"
        )

        right_slot.grid_propagate(False)

        nuevo_button = ctk.CTkButton(
            right_slot,
            text="+",
            width=CIRCULAR_BUTTON_SIZE,
            height=CIRCULAR_BUTTON_SIZE,
            corner_radius=CIRCULAR_BUTTON_RADIUS,
            font=(
                "Arial",
                24,
                "bold"
            ),
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            text_color=BACKGROUND,
            command=self.ir_nuevo_crq
        )

        nuevo_button.pack(
            side="right"
        )


        titulo = ctk.CTkLabel(
            hero,
            text="Test Planning",
            font=get_font(TITLE),
            text_color=PRIMARY
        )


        titulo.pack(
            pady=0
        )

        subtitulo = ctk.CTkLabel(
            hero,
            text="Consulta tus CRQ registrados y entra al planning cuando lo necesites.",
            font=get_font(BODY),
            text_color=TEXT_SECONDARY
        )

        subtitulo.pack(
            pady=(8, 0)
        )

        self.crq_container = ctk.CTkScrollableFrame(
            self,
            fg_color=SURFACE,
            height=470,
            corner_radius=22,
            border_width=1,
            border_color=BORDER
        )


        self.crq_container.pack(
            fill="both",
            expand=True,
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(8, 14)
        )

        self.crear_grid_crqs()
        self.cargar_crqs()


    def crear_grid_crqs(self):

        self.cards_grid = ctk.CTkFrame(
            self.crq_container,
            fg_color="transparent"
        )

        self.cards_grid.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=16
        )

        for columna in range(3):

            self.cards_grid.grid_columnconfigure(
                columna,
                weight=1,
                uniform="crq_cards"
            )




    def cargar_crqs(self):


        crqs = listar_crqs()


        if not crqs:

            self.mostrar_mensaje(
                "No existen CRQ registrados"
            )

            return



        for indice, (crq_id, data) in enumerate(crqs.items()):


            crq_data = {

                "crq": crq_id,

                **data

            }


            card = CRQCard(
                self.cards_grid,
                crq_data,
                self.abrir_crq,
                self.eliminar_crq,
                self.agregar_pruebas,
                self.probar_resultados
            )


            fila = indice // 3
            columna = indice % 3

            card.grid(
                row=fila,
                column=columna,
                padx=12,
                pady=12,
                sticky="nsew"
            )



    def ir_nuevo_crq(self):

        self.navigate(
            "new_crq"
        )



    def abrir_crq(
        self,
        crq
    ):

        self.navigate(
            "crq_detail",
            crq=crq
        )



    def eliminar_crq(
        self,
        crq
    ):


        ConfirmDialog(
            self,
            "Eliminar CRQ",
            f"¿Desea eliminar {crq['crq']}?",
            lambda:
                self.confirmar_eliminacion(crq)
        )


    def agregar_pruebas(
        self,
        crq
    ):

        self.navigate(
            "add_tests",
            crq=crq
        )


    def probar_resultados(
        self,
        crq
    ):

        self.navigate(
            "test_execution",
            crq=crq
        )



    def confirmar_eliminacion(
        self,
        crq
    ):


        eliminado = eliminar_crq_service(
            crq["crq"]
        )


        if eliminado:

            self.recargar_crqs()



    def recargar_crqs(self):


        for widget in self.cards_grid.winfo_children():

            widget.destroy()


        self.cargar_crqs()



    def mostrar_mensaje(
        self,
        texto
    ):


        label = ctk.CTkLabel(
            self.cards_grid,
            text=texto,
            font=get_font(SUBTITLE),
            text_color=TEXT_PRIMARY
        )


        label.grid(
            row=0,
            column=0,
            columnspan=3,
            pady=(70, 12)
        )


        ayuda = ctk.CTkLabel(
            self.cards_grid,
            text="Utilice “Nuevo CRQ” para iniciar una certificación.",
            font=get_font(BODY),
            text_color=TEXT_SECONDARY
        )


        ayuda.grid(
            row=1,
            column=0,
            columnspan=3
        )