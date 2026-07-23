import json
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from app.services.bruno_runner_service import parsear_archivo_bru
from app.services.config_service import obtener_configuracion_jira_automatizacion
from app.services.planning_service import (
    cargar_planning_crq,
    guardar_planning_crq
)
from app.ui.components.message_box import MessageBox
from app.ui.pages.base_page import BasePage
from app.ui.theme.colors import (
    BACKGROUND,
    BORDER,
    PRIMARY,
    PRIMARY_LIGHT,
    PRIMARY_SOFT,
    SURFACE,
    SURFACE_ALT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_SOFT,
    ACCENT_SOFT
)
from app.ui.theme.dimensions import PAGE_HORIZONTAL_PADDING
from app.ui.theme.styles import SECONDARY_BUTTON, SOFT_CARD_STYLE
from app.ui.theme.typography import BODY, SMALL, SUBTITLE, TITLE, get_font


CASE_TYPES = [
    "Happy path",
    "Negative",
    "Boundary",
    "Null or empty",
    "Custom"
]

TYPOLOGY_NAME_BY_PLAN_ID = {
    "integrado": "Integration",
    "accepted": "Acceptance",
    "regresion": "Regression"
}


class TestDesignPage(BasePage):


    def __init__(
        self,
        parent,
        app,
        crq=None,
        planning_data=None,
        request_info=None,
        response_data=None
    ):

        self.crq = crq or {}
        self.planning_data = planning_data
        self.request_info = request_info or {}
        self.response_data = response_data or {}
        self.test_entries = []
        self.selected_test_index = None
        self.selected_case_index = 0
        self.base_body_template = "{\n\n}"
        self.repository_path_default = ""
        self.case_type_var = ctk.StringVar(value=CASE_TYPES[0])
        self.case_name_var = ctk.StringVar(value="")
        self.request_path_var = ctk.StringVar(value="")
        self.request_value_var = ctk.StringVar(value="")
        self.response_path_var = ctk.StringVar(value="")
        self.expected_value_var = ctk.StringVar(value="")

        super().__init__(
            parent,
            app
        )


    def build(self):

        self.configure(
            fg_color=BACKGROUND
        )

        self.cargar_contexto()
        self.crear_ui()
        self.render_navigation()
        self.seleccionar_primer_test()


    def cargar_contexto(self):

        if not self.planning_data:

            self.planning_data = cargar_planning_crq(
                self.crq.get(
                    "crq",
                    ""
                )
            ) or {
                "crq": self.crq.get(
                    "crq",
                    ""
                ),
                "plans": []
            }

        if not self.request_info:

            self.request_info = dict(
                self.planning_data.get(
                    "last_request",
                    {}
                )
            )

        self.repository_path_default = obtener_configuracion_jira_automatizacion().get(
            "jira_test_repository_path",
            ""
        )
        self.base_body_template = self.obtener_body_bruno_base()
        self.test_entries = self.construir_test_entries()


    def crear_ui(self):

        self.crear_hero()

        layout = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        layout.pack(
            fill="both",
            expand=True,
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(0, 18)
        )

        self.navigation_panel = ctk.CTkScrollableFrame(
            layout,
            fg_color=SURFACE,
            corner_radius=20,
            border_width=1,
            border_color=BORDER,
            width=320
        )

        self.navigation_panel.pack(
            side="left",
            fill="y",
            padx=(0, 14)
        )

        self.workspace = ctk.CTkScrollableFrame(
            layout,
            fg_color="transparent"
        )

        self.workspace.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.crear_workspace()


    def crear_hero(self):

        hero = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        hero.pack(
            fill="x",
            padx=PAGE_HORIZONTAL_PADDING,
            pady=(24, 14)
        )

        titulo = ctk.CTkLabel(
            hero,
            text="Diseño de tests",
            font=get_font(TITLE),
            text_color=PRIMARY
        )

        titulo.pack()

        subtitulo = ctk.CTkLabel(
            hero,
            text=(
                f"CRQ activo: {self.crq.get('crq', 'Sin seleccionar')} · "
                "Paso 2: define escenarios, request body y expectativa por campo antes de construir Tests, Test Sets y Planning finales."
            ),
            font=get_font(BODY),
            text_color=TEXT_SECONDARY,
            wraplength=1080,
            justify="center"
        )

        subtitulo.pack(
            pady=(8, 0)
        )


    def crear_workspace(self):

        self.summary_card = ctk.CTkFrame(
            self.workspace,
            **SOFT_CARD_STYLE
        )

        self.summary_card.pack(
            fill="x",
            pady=(0, 12)
        )

        self.summary_title = ctk.CTkLabel(
            self.summary_card,
            text="Selecciona un campo",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        self.summary_title.pack(
            anchor="w",
            padx=22,
            pady=(18, 6)
        )

        self.summary_detail = ctk.CTkLabel(
            self.summary_card,
            text="La columna izquierda te muestra los tests diseñados por plan, test set y campo.",
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=760
        )

        self.summary_detail.pack(
            anchor="w",
            padx=22,
            pady=(0, 18)
        )

        self.requirements_card = ctk.CTkFrame(
            self.workspace,
            **SOFT_CARD_STYLE
        )

        self.requirements_card.pack(
            fill="x",
            pady=(0, 12)
        )

        self.crear_bloque_requerimientos()

        self.case_card = ctk.CTkFrame(
            self.workspace,
            **SOFT_CARD_STYLE
        )

        self.case_card.pack(
            fill="x",
            pady=(0, 12)
        )

        case_header = ctk.CTkFrame(
            self.case_card,
            fg_color="transparent"
        )

        case_header.pack(
            fill="x",
            padx=18,
            pady=(18, 10)
        )

        case_title = ctk.CTkLabel(
            case_header,
            text="Casos del test",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        case_title.pack(
            side="left"
        )

        add_case = ctk.CTkButton(
            case_header,
            text="Nuevo caso",
            width=120,
            height=34,
            corner_radius=17,
            fg_color=PRIMARY_SOFT,
            hover_color=PRIMARY_LIGHT,
            text_color=PRIMARY,
            border_width=1,
            border_color=BORDER,
            command=self.agregar_caso
        )

        add_case.pack(
            side="right"
        )

        self.case_buttons = ctk.CTkFrame(
            self.case_card,
            fg_color="transparent"
        )

        self.case_buttons.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        self.form_card = ctk.CTkFrame(
            self.workspace,
            **SOFT_CARD_STYLE
        )

        self.form_card.pack(
            fill="x",
            pady=(0, 12)
        )

        form_grid = ctk.CTkFrame(
            self.form_card,
            fg_color="transparent"
        )

        form_grid.pack(
            fill="x",
            padx=22,
            pady=22
        )

        for column in range(2):

            form_grid.grid_columnconfigure(
                column,
                weight=1,
                uniform="design_form"
            )

        self.case_type_menu = self.crear_field_option_menu(
            form_grid,
            0,
            0,
            "Tipo de caso",
            self.case_type_var,
            CASE_TYPES,
            self.on_editor_changed
        )

        self.case_name_entry = self.crear_field_entry(
            form_grid,
            0,
            1,
            "Nombre del escenario",
            self.case_name_var
        )

        self.inferred_path_card = ctk.CTkFrame(
            form_grid,
            fg_color=PRIMARY_SOFT,
            corner_radius=14,
            border_width=1,
            border_color=BORDER
        )

        self.inferred_path_card.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=8,
            pady=8
        )

        self.inferred_path_label = ctk.CTkLabel(
            self.inferred_path_card,
            text="Ruta inferida del campo: -",
            font=get_font(BODY),
            text_color=PRIMARY,
            justify="left",
            wraplength=760
        )

        self.inferred_path_label.pack(
            anchor="w",
            padx=14,
            pady=(12, 4)
        )

        self.inferred_path_hint = ctk.CTkLabel(
            self.inferred_path_card,
            text="El path del body y de la response se infiere automáticamente desde el campo seleccionado. Aquí solo capturas el valor a enviar y el valor esperado.",
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=760
        )

        self.inferred_path_hint.pack(
            anchor="w",
            padx=14,
            pady=(0, 12)
        )

        self.request_path_entry = self.crear_field_entry(
            form_grid,
            2,
            0,
            "Valor del campo en request",
            self.request_path_var
        )

        self.request_value_entry = self.crear_field_entry(
            form_grid,
            2,
            1,
            "Valor esperado en response",
            self.request_value_var
        )

        self.live_card = ctk.CTkFrame(
            self.workspace,
            **SOFT_CARD_STYLE
        )

        self.live_card.pack(
            fill="both",
            expand=True,
            pady=(0, 12)
        )

        live_grid = ctk.CTkFrame(
            self.live_card,
            fg_color="transparent"
        )

        live_grid.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        for column in range(2):

            live_grid.grid_columnconfigure(
                column,
                weight=1,
                uniform="live_columns"
            )

        self.body_template_text = self.crear_text_panel(
            live_grid,
            0,
            "Body Bruno base editable",
            "Este machote se toma de la request Bruno actual. Puedes ajustarlo y el preview se actualiza en vivo.",
            WARNING_SOFT,
            height=300
        )

        self.body_preview_text = self.crear_text_panel(
            live_grid,
            1,
            "Preview del body para este caso",
            "Se calcula aplicando el path y el valor del caso seleccionado.",
            ACCENT_SOFT,
            height=300,
            editable=False
        )

        self.response_card = ctk.CTkFrame(
            self.workspace,
            **SOFT_CARD_STYLE
        )

        self.response_card.pack(
            fill="both",
            expand=True,
            pady=(0, 12)
        )

        response_grid = ctk.CTkFrame(
            self.response_card,
            fg_color="transparent"
        )

        response_grid.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        for column in range(2):

            response_grid.grid_columnconfigure(
                column,
                weight=1,
                uniform="response_columns"
            )

        self.response_value_text = self.crear_text_panel(
            response_grid,
            0,
            "Valor actual observado en response",
            "Te ayuda a decidir si el path y la expectativa del test tienen sentido con la respuesta base.",
            SURFACE_ALT,
            height=180,
            editable=False
        )

        self.action_text = self.crear_text_panel(
            response_grid,
            1,
            "Action del test",
            "Aquí documentas el body usado, el campo validado y la expectativa funcional del caso.",
            SURFACE_ALT,
            height=180
        )

        footer = ctk.CTkFrame(
            self.workspace,
            fg_color="transparent"
        )

        footer.pack(
            fill="x",
            pady=(0, 8)
        )

        volver = ctk.CTkButton(
            footer,
            text="Volver a añadir tests",
            width=180,
            height=40,
            corner_radius=20,
            command=lambda: self.navigate(
                "add_tests",
                crq=self.crq
            ),
            **SECONDARY_BUTTON
        )

        volver.pack(
            side="right"
        )

        guardar = ctk.CTkButton(
            footer,
            text="Guardar borrador",
            width=160,
            height=40,
            corner_radius=20,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            command=self.guardar_borrador
        )

        guardar.pack(
            side="right",
            padx=(0, 10)
        )

        finalizar = ctk.CTkButton(
            footer,
            text="Volver al planning",
            width=160,
            height=40,
            corner_radius=20,
            command=self.finalizar_diseno,
            **SECONDARY_BUTTON
        )

        finalizar.pack(
            side="right",
            padx=(0, 10)
        )

        self.footer_hint = ctk.CTkLabel(
            footer,
            text="Lo que guardes aquí queda dentro del planning como borrador por campo para seguir refinando luego la automatización Jira/Xray.",
            font=get_font(SMALL),
            text_color=TEXT_MUTED,
            justify="left",
            wraplength=580
        )

        self.footer_hint.pack(
            side="left",
            anchor="w"
        )

        self.enlazar_eventos_editor()


    def crear_bloque_requerimientos(self):

        title = ctk.CTkLabel(
            self.requirements_card,
            text="Campos requeridos para Jira/Xray",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        title.pack(
            anchor="w",
            padx=22,
            pady=(18, 6)
        )

        hint = ctk.CTkLabel(
            self.requirements_card,
            text=(
                "Test: summary, description, actions, repository path. "
                "Test Set: summary, description, repository path, tests asociados. "
                "Test Plan: summary, description, typology, begin date, end date y test sets asociados."
            ),
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=980
        )

        hint.pack(
            anchor="w",
            padx=22,
            pady=(0, 14)
        )

        content = ctk.CTkFrame(
            self.requirements_card,
            fg_color="transparent"
        )

        content.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        for row in range(3):

            content.grid_rowconfigure(
                row,
                weight=1
            )

        content.grid_columnconfigure(
            0,
            weight=1
        )

        test_card = self.crear_payload_card(
            content,
            0,
            "Payload base del Test",
            "Se construirá por campo y caso usando el action redactado abajo."
        )

        self.test_summary_entry = self.crear_payload_entry(
            test_card,
            "Summary"
        )
        self.test_description_text = self.crear_payload_textbox(
            test_card,
            "Description"
        )
        self.test_repository_entry = self.crear_payload_entry(
            test_card,
            "Repository path"
        )

        test_set_card = self.crear_payload_card(
            content,
            1,
            "Payload base del Test Set",
            "Los test keys se asociarán automáticamente a partir de los tests que terminen dentro de este set."
        )

        self.test_set_summary_entry = self.crear_payload_entry(
            test_set_card,
            "Summary"
        )
        self.test_set_description_text = self.crear_payload_textbox(
            test_set_card,
            "Description"
        )
        self.test_set_repository_entry = self.crear_payload_entry(
            test_set_card,
            "Repository path"
        )

        plan_card = self.crear_payload_card(
            content,
            2,
            "Payload base del Test Plan",
            "Los Test Set asociados se derivarán del planning guardado para este plan."
        )

        self.plan_summary_entry = self.crear_payload_entry(
            plan_card,
            "Summary"
        )
        self.plan_description_text = self.crear_payload_textbox(
            plan_card,
            "Description"
        )

        plan_row = ctk.CTkFrame(
            plan_card,
            fg_color="transparent"
        )

        plan_row.pack(
            fill="x",
            padx=14,
            pady=(0, 14)
        )

        self.plan_typology_entry = self.crear_payload_entry(
            plan_row,
            "Typology",
            pack=False
        )
        self.plan_typology_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        self.plan_begin_entry = self.crear_payload_entry(
            plan_row,
            "Begin date",
            pack=False
        )
        self.plan_begin_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=4
        )

        self.plan_end_entry = self.crear_payload_entry(
            plan_row,
            "End date",
            pack=False
        )
        self.plan_end_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 0)
        )


    def crear_payload_card(self, parent, row, title, hint):

        card = ctk.CTkFrame(
            parent,
            fg_color=SURFACE_ALT,
            corner_radius=16,
            border_width=1,
            border_color=BORDER
        )

        card.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 10)
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        title_label.pack(
            anchor="w",
            padx=14,
            pady=(14, 4)
        )

        hint_label = ctk.CTkLabel(
            card,
            text=hint,
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=900
        )

        hint_label.pack(
            anchor="w",
            padx=14,
            pady=(0, 12)
        )

        return card


    def crear_payload_entry(self, parent, label, pack=True):

        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        if pack:

            wrapper.pack(
                fill="x",
                padx=14,
                pady=(0, 10)
            )

        title = ctk.CTkLabel(
            wrapper,
            text=label,
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY
        )

        title.pack(
            anchor="w",
            pady=(0, 6)
        )

        entry = ctk.CTkEntry(
            wrapper,
            height=36,
            corner_radius=12,
            border_color=BORDER,
            fg_color=SURFACE,
            text_color=TEXT_PRIMARY
        )

        entry.pack(
            fill="x"
        )

        entry.bind(
            "<KeyRelease>",
            lambda _event: self.persistir_payloads_actuales()
        )

        return wrapper


    def crear_payload_textbox(self, parent, label):

        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        wrapper.pack(
            fill="x",
            padx=14,
            pady=(0, 10)
        )

        title = ctk.CTkLabel(
            wrapper,
            text=label,
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY
        )

        title.pack(
            anchor="w",
            pady=(0, 6)
        )

        textbox = ctk.CTkTextbox(
            wrapper,
            height=82,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE,
            text_color=TEXT_PRIMARY
        )

        textbox.pack(
            fill="x"
        )

        textbox.bind(
            "<KeyRelease>",
            lambda _event: self.persistir_payloads_actuales()
        )

        return textbox


    def crear_field_entry(
        self,
        parent,
        row,
        column,
        label,
        variable
    ):

        container = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        container.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=8,
            pady=8
        )

        title = ctk.CTkLabel(
            container,
            text=label,
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY
        )

        title.pack(
            anchor="w",
            pady=(0, 6)
        )

        entry = ctk.CTkEntry(
            container,
            textvariable=variable,
            height=38,
            corner_radius=12,
            border_color=BORDER,
            fg_color=SURFACE,
            text_color=TEXT_PRIMARY
        )

        entry.pack(
            fill="x"
        )

        return entry


    def crear_field_option_menu(
        self,
        parent,
        row,
        column,
        label,
        variable,
        values,
        command
    ):

        container = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        container.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=8,
            pady=8
        )

        title = ctk.CTkLabel(
            container,
            text=label,
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY
        )

        title.pack(
            anchor="w",
            pady=(0, 6)
        )

        menu = ctk.CTkOptionMenu(
            container,
            values=values,
            variable=variable,
            height=38,
            corner_radius=12,
            fg_color=PRIMARY,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_LIGHT,
            command=lambda _value: command()
        )

        menu.pack(
            fill="x"
        )

        return menu


    def crear_text_panel(
        self,
        parent,
        column,
        title,
        hint,
        tint,
        height=220,
        editable=True
    ):

        card = ctk.CTkFrame(
            parent,
            fg_color=tint,
            corner_radius=16,
            border_width=1,
            border_color=BORDER
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=8,
            pady=0
        )

        card.grid_rowconfigure(
            2,
            weight=1
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )

        title_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=14,
            pady=(14, 6)
        )

        hint_label = ctk.CTkLabel(
            card,
            text=hint,
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=400
        )

        hint_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=14,
            pady=(0, 10)
        )

        textbox = ctk.CTkTextbox(
            card,
            height=height,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
            fg_color=SURFACE,
            text_color=TEXT_PRIMARY,
            wrap="none"
        )

        textbox.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=14,
            pady=(0, 14)
        )

        if not editable:

            textbox.configure(
                state="disabled"
            )

        return textbox


    def enlazar_eventos_editor(self):

        for entry in [
            self.case_name_entry,
            self.request_path_entry,
            self.request_value_entry
        ]:

            entry.bind(
                "<KeyRelease>",
                lambda _event: self.on_editor_changed()
            )

        self.body_template_text.bind(
            "<KeyRelease>",
            lambda _event: self.on_editor_changed()
        )

        self.action_text.bind(
            "<KeyRelease>",
            lambda _event: self.on_editor_changed(save_action_only=True)
        )


    def construir_test_entries(self):

        resultado = []

        for plan_index, plan in enumerate(
            self.planning_data.get(
                "plans",
                []
            )
        ):

            for test_set_index, test_set in enumerate(
                plan.get(
                    "test_sets",
                    []
                )
            ):

                for test_index, test in enumerate(
                    test_set.get(
                        "tests",
                        []
                    )
                ):

                    field = str(
                        test.get(
                            "field",
                            ""
                        )
                    ).strip()

                    if not field:

                        continue

                    response_path = self.construir_response_path(
                        test_set.get(
                            "path",
                            ""
                        ),
                        field
                    )

                    resultado.append(
                        {
                            "plan_index": plan_index,
                            "test_set_index": test_set_index,
                            "test_index": test_index,
                            "plan": plan,
                            "test_set": test_set,
                            "test": test,
                            "response_field_path": response_path
                        }
                    )

        return resultado


    def render_navigation(self):

        for widget in self.navigation_panel.winfo_children():

            widget.destroy()

        title = ctk.CTkLabel(
            self.navigation_panel,
            text="Campos a diseñar",
            font=get_font(SUBTITLE),
            text_color=PRIMARY
        )

        title.pack(
            anchor="w",
            padx=16,
            pady=(16, 4)
        )

        hint = ctk.CTkLabel(
            self.navigation_panel,
            text="Cada fila representa un campo que ya quedó seleccionado para generar tests dentro del planning.",
            font=get_font(SMALL),
            text_color=TEXT_SECONDARY,
            wraplength=260,
            justify="left"
        )

        hint.pack(
            anchor="w",
            padx=16,
            pady=(0, 12)
        )

        if not self.test_entries:

            empty = ctk.CTkLabel(
                self.navigation_panel,
                text="Todavía no hay campos disponibles. Regresa a Añadir tests y selecciona al menos un nodo con campos.",
                font=get_font(BODY),
                text_color=TEXT_MUTED,
                wraplength=260,
                justify="left"
            )

            empty.pack(
                anchor="w",
                padx=16,
                pady=(0, 16)
            )
            return

        for index, entry in enumerate(self.test_entries):

            card = ctk.CTkFrame(
                self.navigation_panel,
                fg_color=PRIMARY_SOFT if index == self.selected_test_index else SURFACE_ALT,
                corner_radius=14,
                border_width=1,
                border_color=BORDER
            )

            card.pack(
                fill="x",
                padx=12,
                pady=(0, 10)
            )

            button = ctk.CTkButton(
                card,
                text=entry["test"]["field"],
                anchor="w",
                height=34,
                fg_color="transparent",
                hover_color=PRIMARY_SOFT,
                text_color=PRIMARY,
                command=lambda current=index: self.seleccionar_test(current)
            )

            button.pack(
                fill="x",
                padx=8,
                pady=(8, 4)
            )

            detail = ctk.CTkLabel(
                card,
                text=(
                    f"{entry['plan'].get('tipo_nombre', 'Plan')} · "
                    f"{entry['test_set'].get('path', 'General')}"
                ),
                font=get_font(SMALL),
                text_color=TEXT_SECONDARY,
                wraplength=240,
                justify="left"
            )

            detail.pack(
                anchor="w",
                padx=12,
                pady=(0, 8)
            )


    def seleccionar_primer_test(self):

        if self.test_entries:

            self.seleccionar_test(0)


    def seleccionar_test(self, index):

        self.persistir_caso_actual_en_memoria()
        self.selected_test_index = index
        self.selected_case_index = 0
        self.asegurar_casos_borrador()
        self.render_navigation()
        self.render_editor()


    def asegurar_casos_borrador(self):

        entry = self.obtener_test_actual()

        if not entry:

            return []

        test = entry["test"]
        cases = list(
            test.get(
                "draft_cases",
                []
            )
        )

        if not cases:

            cases = [
                self.crear_caso_base(entry)
            ]
            test["draft_cases"] = cases

        return cases


    def crear_caso_base(self, entry):

        response_path = entry["response_field_path"]
        valor_actual = self.obtener_valor_desde_path(
            self.response_data,
            response_path
        )
        valor_texto = self.valor_a_texto(
            valor_actual
        )

        return {
            "case_type": CASE_TYPES[0],
            "case_name": f"{entry['test']['field']} | {CASE_TYPES[0]}",
            "request_field_path": response_path,
            "request_value": valor_texto,
            "response_field_path": response_path,
            "expected_value": valor_texto,
            "action": self.construir_action_texto(
                response_path,
                valor_texto,
                valor_texto,
                self.base_body_template
            ),
            "body_template": self.base_body_template
        }


    def render_editor(self):

        entry = self.obtener_test_actual()

        if not entry:

            self.summary_title.configure(
                text="Selecciona un campo"
            )
            self.summary_detail.configure(
                text="No hay casos disponibles todavía."
            )
            self.render_case_buttons([])
            self.limpiar_editor()
            return

        cases = self.asegurar_casos_borrador()
        current_case = cases[self.selected_case_index]
        inferred_path = current_case.get(
            "response_field_path",
            entry["response_field_path"]
        )

        self.summary_title.configure(
            text=f"{entry['test_set'].get('nombre', 'Test Set')} · {entry['test']['field']}"
        )
        self.summary_detail.configure(
            text=(
                f"Plan: {entry['plan'].get('tipo_nombre', 'Plan')} · "
                f"Path inferido: {inferred_path} · "
                f"Jira test actual: {entry['test'].get('jira_key', 'Sin ligar')}"
            )
        )

        self.inferred_path_label.configure(
            text=f"Ruta inferida del campo: {inferred_path}"
        )

        self.render_case_buttons(cases)
        self.render_payloads_requeridos(entry)

        self.case_type_var.set(
            current_case.get(
                "case_type",
                CASE_TYPES[0]
            )
        )
        self.case_name_var.set(
            current_case.get(
                "case_name",
                ""
            )
        )
        self.request_path_var.set(
            current_case.get(
                "request_value",
                ""
            )
        )
        self.request_value_var.set(
            current_case.get(
                "expected_value",
                ""
            )
        )
        self.request_path_var.set(
            current_case.get(
                "request_value",
                ""
            )
        )
        self.response_path_var.set(inferred_path)
        self.expected_value_var.set(
            current_case.get(
                "expected_value",
                ""
            )
        )

        self.reemplazar_texto(
            self.body_template_text,
            current_case.get(
                "body_template",
                self.base_body_template
            ),
            editable=True
        )

        self.reemplazar_texto(
            self.action_text,
            current_case.get(
                "action",
                ""
            ),
            editable=True
        )

        self.actualizar_previews()


    def render_case_buttons(self, cases):

        for widget in self.case_buttons.winfo_children():

            widget.destroy()

        if not cases:

            return

        for index, case in enumerate(cases):

            button = ctk.CTkButton(
                self.case_buttons,
                text=case.get(
                    "case_name",
                    f"Caso {index + 1}"
                ),
                height=32,
                corner_radius=16,
                fg_color=PRIMARY if index == self.selected_case_index else PRIMARY_SOFT,
                hover_color=PRIMARY_LIGHT,
                text_color="#FFFFFF" if index == self.selected_case_index else PRIMARY,
                command=lambda current=index: self.seleccionar_caso(current)
            )

            button.pack(
                side="left",
                padx=(0, 8)
            )


    def seleccionar_caso(self, index):

        self.persistir_caso_actual_en_memoria()
        self.selected_case_index = index
        self.render_editor()


    def agregar_caso(self):

        entry = self.obtener_test_actual()

        if not entry:

            return

        self.persistir_caso_actual_en_memoria()
        cases = self.asegurar_casos_borrador()
        nuevo = self.crear_caso_base(entry)
        nuevo["case_type"] = CASE_TYPES[0]
        nuevo["case_name"] = f"{entry['test']['field']} | Caso {len(cases) + 1}"
        cases.append(nuevo)
        entry["test"]["draft_cases"] = cases
        self.selected_case_index = len(cases) - 1
        self.render_editor()


    def limpiar_editor(self):

        self.case_type_var.set(CASE_TYPES[0])
        self.case_name_var.set("")
        self.request_value_var.set("")
        self.expected_value_var.set("")
        self.request_path_var.set("")
        self.response_path_var.set("")
        self.inferred_path_label.configure(
            text="Ruta inferida del campo: -"
        )
        self.reemplazar_texto(
            self.body_template_text,
            self.base_body_template,
            editable=True
        )
        self.reemplazar_texto(
            self.body_preview_text,
            "",
            editable=False
        )
        self.reemplazar_texto(
            self.response_value_text,
            "",
            editable=False
        )
        self.reemplazar_texto(
            self.action_text,
            "",
            editable=True
        )
        self.limpiar_payloads_requeridos()


    def on_editor_changed(self, save_action_only=False):

        if save_action_only:

            self.persistir_caso_actual_en_memoria(actualizar_preview=False)
            return

        self.persistir_caso_actual_en_memoria(actualizar_preview=True)


    def persistir_caso_actual_en_memoria(self, actualizar_preview=False):

        entry = self.obtener_test_actual()

        if not entry:

            return

        cases = self.asegurar_casos_borrador()

        if not cases or self.selected_case_index >= len(cases):

            return

        case_name = self.case_name_var.get().strip()
        response_path = self.response_path_var.get().strip()
        request_value = self.request_path_var.get().strip()
        expected_value = self.request_value_var.get().strip()
        body_template = self.body_template_text.get(
            "1.0",
            "end"
        ).strip()
        action = self.action_text.get(
            "1.0",
            "end"
        ).strip()

        if not action:

            action = self.construir_action_texto(
                response_path,
                request_value,
                expected_value,
                body_template
            )

        cases[self.selected_case_index] = {
            "case_type": self.case_type_var.get().strip() or CASE_TYPES[0],
            "case_name": case_name or f"{entry['test']['field']} | Caso {self.selected_case_index + 1}",
            "request_field_path": response_path,
            "request_value": request_value,
            "response_field_path": response_path,
            "expected_value": expected_value,
            "action": action,
            "body_template": body_template or self.base_body_template
        }

        entry["test"]["draft_cases"] = cases
        self.persistir_payloads_actuales()

        if actualizar_preview:

            self.actualizar_previews()
            self.render_case_buttons(cases)


    def actualizar_previews(self):

        entry = self.obtener_test_actual()

        if not entry:

            return

        body_template = self.body_template_text.get(
            "1.0",
            "end"
        ).strip() or self.base_body_template
        request_path = self.request_path_var.get().strip()
        request_value = self.request_path_var.get().strip()
        response_path = self.response_path_var.get().strip()
        expected_value = self.request_value_var.get().strip()

        preview_text = self.construir_body_preview(
            body_template,
            request_path,
            request_value
        )
        self.reemplazar_texto(
            self.body_preview_text,
            preview_text,
            editable=False
        )

        observed = self.obtener_valor_desde_path(
            self.response_data,
            response_path
        )
        observed_text = self.valor_a_texto(observed)

        self.reemplazar_texto(
            self.response_value_text,
            (
                f"Path: {response_path or '-'}\n\n"
                f"Valor actual: {observed_text or 'Sin dato'}\n\n"
                f"Valor esperado: {expected_value or 'Sin definir'}"
            ),
            editable=False
        )

        if not self.action_text.get(
            "1.0",
            "end"
        ).strip():

            self.reemplazar_texto(
                self.action_text,
                self.construir_action_texto(
                    response_path,
                    request_value,
                    expected_value,
                    body_template
                ),
                editable=True
            )


    def construir_body_preview(
        self,
        body_template,
        request_path,
        request_value
    ):

        if not body_template:

            return "Sin body base disponible para este request."

        try:

            data = json.loads(body_template)

        except json.JSONDecodeError:

            return body_template

        if request_path:

            self.asignar_valor_en_path(
                data,
                request_path,
                self.coercer_valor(request_value)
            )

        return json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )


    def guardar_borrador(self):

        entry = self.obtener_test_actual()

        if not entry:

            MessageBox(
                self,
                "No hay ningún campo seleccionado para guardar.",
                "warning"
            )
            return

        self.persistir_caso_actual_en_memoria(actualizar_preview=True)
        self.persistir_payloads_actuales()

        test = entry["test"]
        draft_cases = test.get(
            "draft_cases",
            []
        )

        test["estado"] = "Diseñado"
        test["actions"] = self.construir_actions_desde_casos(
            draft_cases
        )

        guardar_planning_crq(
            self.crq.get(
                "crq",
                ""
            ),
            self.planning_data
        )

        MessageBox(
            self,
            (
                f"Se guardó el borrador de {test.get('field', 'este campo')}\n\n"
                f"Casos almacenados: {len(draft_cases)}"
            ),
            "success"
        )


    def finalizar_diseno(self):

        self.guardar_borrador_silencioso()
        self.navigate(
            "crq_detail",
            crq=self.crq
        )


    def guardar_borrador_silencioso(self):

        entry = self.obtener_test_actual()

        if not entry:

            return

        self.persistir_caso_actual_en_memoria(actualizar_preview=True)
        self.persistir_payloads_actuales()
        test = entry["test"]
        test["actions"] = self.construir_actions_desde_casos(
            test.get(
                "draft_cases",
                []
            )
        )

        guardar_planning_crq(
            self.crq.get(
                "crq",
                ""
            ),
            self.planning_data
        )


    def obtener_test_actual(self):

        if self.selected_test_index is None:

            return None

        if self.selected_test_index >= len(self.test_entries):

            return None

        return self.test_entries[self.selected_test_index]


    def render_payloads_requeridos(self, entry):

        payloads = self.asegurar_issue_payloads(entry)

        self.reemplazar_entry(
            self.test_summary_entry,
            payloads["test"].get("summary", "")
        )
        self.reemplazar_texto(
            self.test_description_text,
            payloads["test"].get("description", ""),
            editable=True
        )
        self.reemplazar_entry(
            self.test_repository_entry,
            payloads["test"].get("repository_path", "")
        )

        self.reemplazar_entry(
            self.test_set_summary_entry,
            payloads["test_set"].get("summary", "")
        )
        self.reemplazar_texto(
            self.test_set_description_text,
            payloads["test_set"].get("description", ""),
            editable=True
        )
        self.reemplazar_entry(
            self.test_set_repository_entry,
            payloads["test_set"].get("repository_path", "")
        )

        self.reemplazar_entry(
            self.plan_summary_entry,
            payloads["plan"].get("summary", "")
        )
        self.reemplazar_texto(
            self.plan_description_text,
            payloads["plan"].get("description", ""),
            editable=True
        )
        self.reemplazar_entry(
            self.plan_typology_entry,
            payloads["plan"].get("typology_name", "")
        )
        self.reemplazar_entry(
            self.plan_begin_entry,
            payloads["plan"].get("begin_date", "")
        )
        self.reemplazar_entry(
            self.plan_end_entry,
            payloads["plan"].get("end_date", "")
        )


    def limpiar_payloads_requeridos(self):

        for entry in [
            self.test_summary_entry,
            self.test_repository_entry,
            self.test_set_summary_entry,
            self.test_set_repository_entry,
            self.plan_summary_entry,
            self.plan_typology_entry,
            self.plan_begin_entry,
            self.plan_end_entry
        ]:

            self.reemplazar_entry(entry, "")

        for textbox in [
            self.test_description_text,
            self.test_set_description_text,
            self.plan_description_text
        ]:

            self.reemplazar_texto(textbox, "", editable=True)


    def asegurar_issue_payloads(self, entry):

        plan = entry["plan"]
        test_set = entry["test_set"]
        test = entry["test"]
        channel = self.obtener_channel_display()
        service_name = self.obtener_service_display()
        version_label = self.obtener_version_display()
        object_path = self.formatear_path_para_summary(
            test_set.get("path", "General")
        )
        case_type = self.obtener_tipo_prueba_display(test)
        field_name = test.get("field", "Campo")
        objetivo = str(
            self.crq.get(
                "objetivo_cambio",
                ""
            ) or self.crq.get(
                "descripcion",
                ""
            )
        ).strip()

        today = self.crq.get("fecha_instalacion", "") or datetime.now().strftime("%Y-%m-%d")

        plan.setdefault(
            "issue_payload",
            {
                "summary": f"[CRQ-{self.crq.get('crq', '-')}] {service_name} | {version_label} | {plan.get('tipo_nombre', 'Plan')}",
                "description": self.construir_descripcion_test_plan(
                    plan.get("tipo_nombre", "Plan"),
                    service_name,
                    version_label,
                    objetivo,
                    plan.get("estrategia", "")
                ),
                "typology_name": TYPOLOGY_NAME_BY_PLAN_ID.get(
                    plan.get("tipo_id", ""),
                    plan.get("tipo_nombre", "")
                ),
                "begin_date": today,
                "end_date": today
            }
        )

        test_set.setdefault(
            "issue_payload",
            {
                "summary": f"[{channel}-Global] {service_name} | {version_label} | {object_path}",
                "description": self.construir_descripcion_test_set(
                    object_path,
                    service_name,
                    version_label
                ),
                "repository_path": self.repository_path_default
            }
        )

        test.setdefault(
            "issue_payload",
            {
                "summary": f"[{channel}-Global] {service_name} | {version_label} | {object_path} | {field_name} | {case_type} | Global/Esperado",
                "description": self.construir_descripcion_test(
                    field_name,
                    object_path,
                    case_type,
                    service_name,
                    version_label,
                    test
                ),
                "actions": test.get("actions", ""),
                "repository_path": self.repository_path_default
            }
        )

        return {
            "plan": plan["issue_payload"],
            "test_set": test_set["issue_payload"],
            "test": test["issue_payload"]
        }


    def persistir_payloads_actuales(self):

        entry = self.obtener_test_actual()

        if not entry:

            return

        payloads = self.asegurar_issue_payloads(entry)

        payloads["test"]["summary"] = self.obtener_valor_entry(self.test_summary_entry)
        payloads["test"]["description"] = self.obtener_valor_texto(self.test_description_text)
        payloads["test"]["actions"] = self.obtener_valor_texto(self.action_text)
        payloads["test"]["repository_path"] = self.obtener_valor_entry(self.test_repository_entry)

        payloads["test_set"]["summary"] = self.obtener_valor_entry(self.test_set_summary_entry)
        payloads["test_set"]["description"] = self.obtener_valor_texto(self.test_set_description_text)
        payloads["test_set"]["repository_path"] = self.obtener_valor_entry(self.test_set_repository_entry)

        payloads["plan"]["summary"] = self.obtener_valor_entry(self.plan_summary_entry)
        payloads["plan"]["description"] = self.obtener_valor_texto(self.plan_description_text)
        payloads["plan"]["typology_name"] = self.obtener_valor_entry(self.plan_typology_entry)
        payloads["plan"]["begin_date"] = self.obtener_valor_entry(self.plan_begin_entry)
        payloads["plan"]["end_date"] = self.obtener_valor_entry(self.plan_end_entry)

        self.repository_path_default = payloads["test"]["repository_path"]


    def obtener_valor_entry(self, wrapper):

        children = wrapper.winfo_children()
        entry = children[-1] if children else None
        return entry.get().strip() if entry else ""


    def reemplazar_entry(self, wrapper, value):

        children = wrapper.winfo_children()
        entry = children[-1] if children else None

        if not entry:

            return

        entry.delete(0, "end")
        entry.insert(0, value or "")


    def obtener_valor_texto(self, textbox):

        return textbox.get(
            "1.0",
            "end"
        ).strip()


    def obtener_channel_display(self):

        channel = str(
            self.request_info.get(
                "transaction_channel",
                ""
            )
        ).strip()

        return channel.upper() if channel else "GENERAL"


    def obtener_service_display(self):

        return str(
            self.request_info.get(
                "service_name",
                "Servicio"
            )
        ).strip() or "Servicio"


    def obtener_version_display(self):

        return str(
            self.request_info.get(
                "version_label",
                "Sin versión"
            )
        ).strip() or "Sin versión"


    def formatear_path_para_summary(self, path):

        segmentos = []

        for segmento in str(path or "General").split("."):

            limpio = segmento.replace("[]", "")
            limpio = limpio.replace("_", " ").strip()

            if not limpio:

                continue

            segmentos.append(
                limpio[:1].upper() + limpio[1:]
            )

        return " > ".join(segmentos) if segmentos else "General"


    def obtener_tipo_prueba_display(self, test):

        draft_cases = test.get("draft_cases", [])

        if draft_cases:

            return str(
                draft_cases[0].get(
                    "case_type",
                    CASE_TYPES[0]
                )
            ).strip() or CASE_TYPES[0]

        return CASE_TYPES[0]


    def construir_descripcion_test(self, field_name, object_path, case_type, service_name, version_label, test):

        draft_cases = test.get("draft_cases", [])
        case_detail = ""

        if draft_cases:

            primer_caso = draft_cases[0]
            esperado = str(
                primer_caso.get(
                    "expected_value",
                    ""
                )
            ).strip()

            if esperado:

                case_detail = f" Se espera observar el valor `{esperado}` en la respuesta para validar el resultado del escenario."

        return (
            f"Validación del campo {field_name} en {object_path} para el servicio {service_name} {version_label}. "
            f"El caso base corresponde a un escenario {case_type.lower()} y servirá como referencia para construir el test funcional y su evidencia.{case_detail}"
        )


    def construir_descripcion_test_set(self, object_path, service_name, version_label):

        return (
            f"Agrupa los tests funcionales asociados al objeto {object_path} del servicio {service_name} {version_label}. "
            "Este set sirve como contenedor de cobertura para revisar de forma conjunta los campos seleccionados y sus escenarios."
        )


    def construir_descripcion_test_plan(self, plan_name, service_name, version_label, objetivo, estrategia):

        objetivo_texto = objetivo or "Sin objetivo detallado"

        return (
            f"Test Plan de tipo {plan_name} para el servicio {service_name} {version_label}. "
            f"Objetivo del cambio: {objetivo_texto}. "
            f"Estrategia inicial: {estrategia}"
        )


    def obtener_body_bruno_base(self):

        bruno_request = dict(
            self.request_info.get(
                "bruno_request",
                {}
            )
        )

        if not bruno_request:

            for plan in self.planning_data.get(
                "plans",
                []
            ):

                for test_set in plan.get(
                    "test_sets",
                    []
                ):

                    source = test_set.get(
                        "source",
                        {}
                    )
                    bruno_request = dict(
                        source.get(
                            "bruno_request",
                            {}
                        )
                    )

                    if bruno_request:

                        break

                if bruno_request:

                    break

        file_path = str(
            bruno_request.get(
                "file",
                ""
            )
        ).strip()

        if not file_path:

            return "{\n\n}"

        path = Path(file_path)

        if not path.exists():

            return "{\n\n}"

        try:

            definition = parsear_archivo_bru(path)

        except Exception:

            return "{\n\n}"

        body = definition.get(
            "body",
            {}
        )

        content = str(
            body.get(
                "content",
                ""
            )
        ).strip()

        return content or "{\n\n}"


    def construir_response_path(self, object_path, field):

        object_path = str(object_path or "").strip()
        field = str(field or "").strip()

        if not object_path:

            return field

        if not field:

            return object_path

        return f"{object_path}.{field}"


    def obtener_valor_desde_path(self, data, path):

        current = data

        for raw_segment in self.segmentos_path(path):

            is_array = raw_segment.endswith("[]")
            segment = raw_segment[:-2] if is_array else raw_segment

            if isinstance(current, dict):

                current = current.get(segment)

            else:

                return None

            if is_array:

                if not isinstance(current, list) or not current:

                    return None

                current = current[0]

            if current is None:

                return None

        return current


    def asignar_valor_en_path(self, data, path, value):

        segments = self.segmentos_path(path)

        if not segments or not isinstance(data, dict):

            return

        current = data

        for index, raw_segment in enumerate(segments):

            is_last = index == len(segments) - 1
            is_array = raw_segment.endswith("[]")
            segment = raw_segment[:-2] if is_array else raw_segment

            if is_last:

                if is_array:

                    current[segment] = [value]

                else:

                    current[segment] = value

                return

            next_segment = segments[index + 1]
            next_is_array = next_segment.endswith("[]")

            if is_array:

                container = current.setdefault(segment, [])

                if not container:

                    container.append({})

                if not isinstance(container[0], dict):

                    container[0] = {}

                current = container[0]
                continue

            next_default = [] if next_is_array else {}
            value_at_key = current.get(segment)

            if not isinstance(value_at_key, (dict, list)):

                current[segment] = next_default.copy() if isinstance(next_default, dict) else []

            current = current[segment]

            if isinstance(current, list):

                if not current:

                    current.append({})

                if not isinstance(current[0], dict):

                    current[0] = {}

                current = current[0]


    def segmentos_path(self, path):

        return [
            segmento.strip()
            for segmento in str(path or "").split(".")
            if segmento.strip()
        ]


    def coercer_valor(self, value):

        texto = str(value or "").strip()

        if texto == "":

            return ""

        try:

            return json.loads(texto)

        except json.JSONDecodeError:

            lowered = texto.lower()

            if lowered == "true":

                return True

            if lowered == "false":

                return False

            if lowered == "null":

                return None

            return texto


    def valor_a_texto(self, value):

        if value is None:

            return ""

        if isinstance(value, (dict, list, bool, int, float)):

            return json.dumps(
                value,
                ensure_ascii=False
            )

        return str(value)


    def construir_action_texto(
        self,
        response_path,
        request_value,
        expected_value,
        body_template
    ):

        return (
            f"Campo validado: {response_path or '-'}\n"
            f"Valor enviado en request: {request_value or '-'}\n"
            f"Valor esperado en response: {expected_value or '-'}\n\n"
            "Body base utilizado:\n"
            f"{body_template or '{ }'}"
        )


    def construir_actions_desde_casos(self, draft_cases):

        bloques = []

        for index, case in enumerate(draft_cases, start=1):

            bloques.append(
                (
                    f"Caso {index}: {case.get('case_name', f'Caso {index}')}\n"
                    f"Tipo: {case.get('case_type', '-') }\n"
                    f"Path request: {case.get('request_field_path', '-') }\n"
                    f"Valor request: {case.get('request_value', '-') }\n"
                    f"Path response: {case.get('response_field_path', '-') }\n"
                    f"Valor esperado: {case.get('expected_value', '-') }\n\n"
                    f"{case.get('action', '').strip()}"
                ).strip()
            )

        return "\n\n---\n\n".join(bloques)


    def reemplazar_texto(self, textbox, value, editable):

        textbox.configure(
            state="normal"
        )
        textbox.delete(
            "1.0",
            "end"
        )
        textbox.insert(
            "1.0",
            value or ""
        )

        if not editable:

            textbox.configure(
                state="disabled"
            )

