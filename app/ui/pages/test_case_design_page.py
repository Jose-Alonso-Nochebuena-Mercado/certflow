import json
from pathlib import Path

import customtkinter as ctk

from app.services.bruno_runner_service import parsear_archivo_bru
from app.services.planning_service import cargar_planning_crq, guardar_planning_crq
from app.ui.components.message_box import MessageBox
from app.ui.pages.base_page import BasePage
from app.ui.theme.colors import BACKGROUND, BORDER, PRIMARY, PRIMARY_LIGHT, PRIMARY_SOFT, SURFACE, SURFACE_ALT, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING_SOFT, ACCENT_SOFT
from app.ui.theme.dimensions import PAGE_HORIZONTAL_PADDING
from app.ui.theme.styles import SECONDARY_BUTTON, SOFT_CARD_STYLE
from app.ui.theme.typography import BODY, SMALL, SUBTITLE, TITLE, get_font


CASE_TYPES = ["Happy path", "Negative", "Boundary", "Null or empty", "Custom"]


class TestCaseDesignPage(BasePage):


    def __init__(self, parent, app, crq=None, planning_data=None, request_info=None, response_data=None, current_plan_id=None):
        self.crq = crq or {}
        self.planning_data = planning_data
        self.request_info = request_info or {}
        self.response_data = response_data or {}
        self.current_plan_id = current_plan_id
        self.repository_path_default = ""
        self.base_body_template = "{\n\n}"
        self.test_entries = []
        self.selected_test_index = None
        self.selected_case_index = 0
        self.case_type_var = ctk.StringVar(value=CASE_TYPES[0])
        self.case_name_var = ctk.StringVar(value="")
        self.request_value_var = ctk.StringVar(value="")
        self.expected_value_var = ctk.StringVar(value="")
        super().__init__(parent, app)


    def build(self):
        self.configure(fg_color=BACKGROUND)
        self.cargar_contexto()
        self.crear_ui()
        self.render_navigation()
        self.seleccionar_test(0, persist_current=False)


    def cargar_contexto(self):
        if not self.planning_data:
            self.planning_data = cargar_planning_crq(self.crq.get("crq", "")) or {"crq": self.crq.get("crq", ""), "plans": []}

        self.repository_path_default = str(self.request_info.get("repository_folder", "")).strip()
        self.base_body_template = self.obtener_body_bruno_base()
        self.test_entries = self.construir_test_entries()


    def crear_ui(self):
        hero = ctk.CTkFrame(self, fg_color="transparent")
        hero.pack(fill="x", padx=PAGE_HORIZONTAL_PADDING, pady=(24, 14))
        ctk.CTkLabel(hero, text="Diseño de Tests", font=get_font(TITLE), text_color=PRIMARY).pack()
        ctk.CTkLabel(hero, text=f"CRQ activo: {self.crq.get('crq', 'Sin seleccionar')} · Plan: {self.obtener_nombre_plan_actual()} · Ahora sí defines los Tests uno por uno.", font=get_font(BODY), text_color=TEXT_SECONDARY, wraplength=1040, justify="center").pack(pady=(8, 0))

        layout = ctk.CTkFrame(self, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=PAGE_HORIZONTAL_PADDING, pady=(0, 18))

        self.navigation_panel = ctk.CTkScrollableFrame(layout, fg_color=SURFACE, corner_radius=20, border_width=1, border_color=BORDER, width=320)
        self.navigation_panel.pack(side="left", fill="y", padx=(0, 14))

        self.workspace = ctk.CTkScrollableFrame(layout, fg_color="transparent")
        self.workspace.pack(side="left", fill="both", expand=True)

        self.summary_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        self.summary_card.pack(fill="x", pady=(0, 12))
        self.summary_title = ctk.CTkLabel(self.summary_card, text="Selecciona un test", font=get_font(SUBTITLE), text_color=PRIMARY)
        self.summary_title.pack(anchor="w", padx=22, pady=(18, 6))
        self.summary_hint = ctk.CTkLabel(self.summary_card, text="La ruta del campo se infiere automáticamente. Aquí defines escenario, valor en request y valor esperado en response.", font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=760)
        self.summary_hint.pack(anchor="w", padx=22, pady=(0, 18))

        self.payload_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        self.payload_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(self.payload_card, text="Payload base del Test", font=get_font(SUBTITLE), text_color=PRIMARY).pack(anchor="w", padx=22, pady=(18, 6))
        payload_form = ctk.CTkFrame(self.payload_card, fg_color="transparent")
        payload_form.pack(fill="x", padx=22, pady=(0, 18))
        self.test_summary_entry = self.crear_entry(payload_form, "Summary")
        self.test_repository_entry = self.crear_entry(payload_form, "Repository path")
        self.test_description_text = self.crear_textbox(payload_form, "Description", 100)

        self.case_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        self.case_card.pack(fill="x", pady=(0, 12))
        head = ctk.CTkFrame(self.case_card, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(18, 10))
        ctk.CTkLabel(head, text="Casos del test", font=get_font(SUBTITLE), text_color=PRIMARY).pack(side="left")
        ctk.CTkButton(head, text="Nuevo caso", width=120, height=34, corner_radius=17, fg_color=PRIMARY_SOFT, hover_color=PRIMARY_LIGHT, text_color=PRIMARY, border_width=1, border_color=BORDER, command=self.agregar_caso).pack(side="right")
        self.case_buttons = ctk.CTkFrame(self.case_card, fg_color="transparent")
        self.case_buttons.pack(fill="x", padx=18, pady=(0, 18))

        form_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        form_card.pack(fill="x", pady=(0, 12))
        form = ctk.CTkFrame(form_card, fg_color="transparent")
        form.pack(fill="x", padx=22, pady=22)
        form.grid_columnconfigure(0, weight=1, uniform="test_form")
        form.grid_columnconfigure(1, weight=1, uniform="test_form")
        self.case_type_menu = self.crear_option_menu(form, 0, 0, "Tipo de prueba", self.case_type_var)
        self.case_name_entry = self.crear_field_entry(form, 0, 1, "Nombre del escenario", self.case_name_var)

        self.inferred_path_label = ctk.CTkLabel(form, text="Ruta inferida del campo: -", font=get_font(BODY), text_color=PRIMARY, justify="left", wraplength=760)
        self.inferred_path_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 10))

        self.request_value_entry = self.crear_field_entry(form, 2, 0, "Valor del campo en request", self.request_value_var)
        self.expected_value_entry = self.crear_field_entry(form, 2, 1, "Valor esperado en response", self.expected_value_var)

        live_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        live_card.pack(fill="both", expand=True, pady=(0, 12))
        live = ctk.CTkFrame(live_card, fg_color="transparent")
        live.pack(fill="both", expand=True, padx=18, pady=18)
        live.grid_columnconfigure(0, weight=1, uniform="live")
        live.grid_columnconfigure(1, weight=1, uniform="live")
        self.body_template_text = self.crear_text_panel(live, 0, "Body Bruno base editable", "Este machote se toma de la request Bruno actual y se actualiza con el valor del caso.", WARNING_SOFT, 280, True)
        self.body_preview_text = self.crear_text_panel(live, 1, "Preview del body para este caso", "Se recalcula automáticamente usando el path inferido del campo.", ACCENT_SOFT, 280, False)

        response_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        response_card.pack(fill="both", expand=True, pady=(0, 12))
        response = ctk.CTkFrame(response_card, fg_color="transparent")
        response.pack(fill="both", expand=True, padx=18, pady=18)
        response.grid_columnconfigure(0, weight=1, uniform="resp")
        response.grid_columnconfigure(1, weight=1, uniform="resp")
        self.response_value_text = self.crear_text_panel(response, 0, "Valor actual observado en response", "Te ayuda a contrastar el caso con la respuesta base.", SURFACE_ALT, 170, False)
        self.action_text = self.crear_text_panel(response, 1, "Action del test", "Aquí se documenta el escenario y la expectativa funcional del test.", SURFACE_ALT, 170, True)

        footer = ctk.CTkFrame(self.workspace, fg_color="transparent")
        footer.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(footer, text="Volver a Test Sets", width=160, height=40, corner_radius=20, command=lambda: self.navigate("test_set_design", crq=self.crq, planning_data=self.planning_data, request_info=self.request_info, response_data=self.response_data, current_plan_id=self.current_plan_id), **SECONDARY_BUTTON).pack(side="right")
        ctk.CTkButton(footer, text="Guardar Test", width=150, height=40, corner_radius=20, fg_color=PRIMARY, hover_color=PRIMARY_LIGHT, command=self.guardar_borrador).pack(side="right", padx=(0, 10))
        ctk.CTkButton(footer, text="Volver al planning", width=160, height=40, corner_radius=20, fg_color=PRIMARY_SOFT, hover_color=PRIMARY_LIGHT, text_color=PRIMARY, border_width=1, border_color=BORDER, command=self.finalizar).pack(side="right", padx=(0, 10))

        self.enlazar_eventos()


    def crear_entry(self, parent, label):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(wrapper, text=label, font=get_font(SMALL), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))
        entry = ctk.CTkEntry(wrapper, height=38, corner_radius=12, border_color=BORDER, fg_color=SURFACE_ALT, text_color=TEXT_PRIMARY)
        entry.pack(fill="x")
        entry.bind("<KeyRelease>", lambda _event: self.persistir_test_actual())
        return entry


    def crear_textbox(self, parent, label, height):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(wrapper, text=label, font=get_font(SMALL), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))
        textbox = ctk.CTkTextbox(wrapper, height=height, corner_radius=12, border_width=1, border_color=BORDER, fg_color=SURFACE_ALT, text_color=TEXT_PRIMARY)
        textbox.pack(fill="x")
        textbox.bind("<KeyRelease>", lambda _event: self.persistir_test_actual())
        return textbox


    def crear_field_entry(self, parent, row, column, label, variable):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(wrapper, text=label, font=get_font(SMALL), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))
        entry = ctk.CTkEntry(wrapper, textvariable=variable, height=38, corner_radius=12, border_color=BORDER, fg_color=SURFACE, text_color=TEXT_PRIMARY)
        entry.pack(fill="x")
        return entry


    def crear_option_menu(self, parent, row, column, label, variable):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(wrapper, text=label, font=get_font(SMALL), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))
        menu = ctk.CTkOptionMenu(wrapper, values=CASE_TYPES, variable=variable, height=38, corner_radius=12, fg_color=PRIMARY, button_color=PRIMARY, button_hover_color=PRIMARY_LIGHT, command=lambda _value: self.on_editor_changed())
        menu.pack(fill="x")
        return menu


    def crear_text_panel(self, parent, column, title, hint, tint, height, editable):
        card = ctk.CTkFrame(parent, fg_color=tint, corner_radius=16, border_width=1, border_color=BORDER)
        card.grid(row=0, column=column, sticky="nsew", padx=8)
        card.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(card, text=title, font=get_font(BODY), text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
        ctk.CTkLabel(card, text=hint, font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=400).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))
        textbox = ctk.CTkTextbox(card, height=height, corner_radius=12, border_width=1, border_color=BORDER, fg_color=SURFACE, text_color=TEXT_PRIMARY, wrap="none")
        textbox.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        if not editable:
            textbox.configure(state="disabled")
        return textbox


    def enlazar_eventos(self):
        for entry in [self.case_name_entry, self.request_value_entry, self.expected_value_entry]:
            entry.bind("<KeyRelease>", lambda _event: self.on_editor_changed())
        self.body_template_text.bind("<KeyRelease>", lambda _event: self.on_editor_changed())
        self.action_text.bind("<KeyRelease>", lambda _event: self.persistir_test_actual(False))


    def construir_test_entries(self):
        resultado = []
        for plan in self.planning_data.get("plans", []):
            if self.current_plan_id and plan.get("tipo_id") != self.current_plan_id:
                continue
            for test_set in plan.get("test_sets", []):
                if not test_set.get("enabled", True):
                    continue
                for test in test_set.get("tests", []):
                    field = str(test.get("field", "")).strip()
                    if not field:
                        continue
                    resultado.append({
                        "plan": plan,
                        "test_set": test_set,
                        "test": test,
                        "response_field_path": self.construir_response_path(test_set.get("path", ""), field)
                    })
        return resultado


    def render_navigation(self):
        for widget in self.navigation_panel.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.navigation_panel, text="Tests del plan", font=get_font(SUBTITLE), text_color=PRIMARY).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(self.navigation_panel, text="Cada fila representa un campo que terminó dentro de un Test Set activo para este plan.", font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=260).pack(anchor="w", padx=16, pady=(0, 12))

        if not self.test_entries:
            ctk.CTkLabel(self.navigation_panel, text="No hay tests disponibles para este plan. Regresa a Test Sets y activa al menos un set con campos.", font=get_font(BODY), text_color=TEXT_MUTED, wraplength=260, justify="left").pack(anchor="w", padx=16, pady=(0, 16))
            return

        for index, entry in enumerate(self.test_entries):
            card = ctk.CTkFrame(self.navigation_panel, fg_color=PRIMARY_SOFT if index == self.selected_test_index else SURFACE_ALT, corner_radius=14, border_width=1, border_color=BORDER)
            card.pack(fill="x", padx=12, pady=(0, 10))
            ctk.CTkButton(card, text=entry["test"].get("field", "Campo"), anchor="w", height=34, fg_color="transparent", hover_color=PRIMARY_SOFT, text_color=PRIMARY, command=lambda current=index: self.seleccionar_test(current)).pack(fill="x", padx=8, pady=(8, 4))
            ctk.CTkLabel(card, text=entry["test_set"].get("path", "General"), font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=240).pack(anchor="w", padx=12, pady=(0, 8))


    def seleccionar_test(self, index, persist_current=True):
        if persist_current and self.selected_test_index is not None:
            self.persistir_test_actual()
        self.selected_test_index = index
        self.selected_case_index = 0
        self.render_navigation()
        self.render_test_actual()


    def render_test_actual(self):
        entry = self.obtener_test_actual()
        if not entry:
            return
        test = entry["test"]
        payload = self.asegurar_payload_test(entry)
        cases = self.asegurar_casos(entry)
        case = cases[self.selected_case_index]
        inferred_path = case.get("response_field_path", entry["response_field_path"])

        self.summary_title.configure(text=f"{entry['test_set'].get('nombre', 'Test Set')} · {test.get('field', 'Campo')}")
        self.inferred_path_label.configure(text=f"Ruta inferida del campo: {inferred_path}")
        self.reemplazar_entry(self.test_summary_entry, payload.get("summary", ""))
        self.reemplazar_entry(self.test_repository_entry, payload.get("repository_path", ""))
        self.reemplazar_texto(self.test_description_text, payload.get("description", ""), True)
        self.render_case_buttons(cases)
        self.case_type_var.set(case.get("case_type", CASE_TYPES[0]))
        self.case_name_var.set(case.get("case_name", ""))
        self.request_value_var.set(case.get("request_value", ""))
        self.expected_value_var.set(case.get("expected_value", ""))
        self.reemplazar_texto(self.body_template_text, case.get("body_template", self.base_body_template), True)
        self.reemplazar_texto(self.action_text, case.get("action", ""), True)
        self.actualizar_previews()


    def render_case_buttons(self, cases):
        for widget in self.case_buttons.winfo_children():
            widget.destroy()
        for index, case in enumerate(cases):
            ctk.CTkButton(self.case_buttons, text=case.get("case_name", f"Caso {index + 1}"), height=32, corner_radius=16, fg_color=PRIMARY if index == self.selected_case_index else PRIMARY_SOFT, hover_color=PRIMARY_LIGHT, text_color="#FFFFFF" if index == self.selected_case_index else PRIMARY, command=lambda current=index: self.seleccionar_caso(current)).pack(side="left", padx=(0, 8))


    def seleccionar_caso(self, index):
        self.persistir_test_actual()
        self.selected_case_index = index
        self.render_test_actual()


    def agregar_caso(self):
        entry = self.obtener_test_actual()
        if not entry:
            return
        self.persistir_test_actual()
        cases = self.asegurar_casos(entry)
        base = self.crear_caso_base(entry)
        base["case_name"] = f"{entry['test'].get('field', 'Campo')} | Caso {len(cases) + 1}"
        cases.append(base)
        entry["test"]["draft_cases"] = cases
        self.selected_case_index = len(cases) - 1
        self.render_test_actual()


    def crear_caso_base(self, entry):
        response_path = entry["response_field_path"]
        observed = self.obtener_valor_desde_path(self.response_data, response_path)
        observed_text = self.valor_a_texto(observed)
        return {
            "case_type": CASE_TYPES[0],
            "case_name": f"{entry['test'].get('field', 'Campo')} | {CASE_TYPES[0]}",
            "request_field_path": response_path,
            "request_value": observed_text,
            "response_field_path": response_path,
            "expected_value": observed_text,
            "action": self.construir_action(response_path, observed_text, observed_text, self.base_body_template),
            "body_template": self.base_body_template
        }


    def asegurar_casos(self, entry):
        cases = list(entry["test"].get("draft_cases", []))
        if not cases:
            cases = [self.crear_caso_base(entry)]
            entry["test"]["draft_cases"] = cases
        return cases


    def persistir_test_actual(self, actualizar_preview=True):
        entry = self.obtener_test_actual()
        if not entry:
            return
        payload = self.asegurar_payload_test(entry)
        payload["summary"] = self.test_summary_entry.get().strip()
        payload["repository_path"] = self.test_repository_entry.get().strip()
        payload["description"] = self.test_description_text.get("1.0", "end").strip()
        payload["actions"] = self.action_text.get("1.0", "end").strip()

        cases = self.asegurar_casos(entry)
        response_path = entry["response_field_path"]
        body_template = self.body_template_text.get("1.0", "end").strip() or self.base_body_template
        action = self.action_text.get("1.0", "end").strip() or self.construir_action(response_path, self.request_value_var.get().strip(), self.expected_value_var.get().strip(), body_template)
        cases[self.selected_case_index] = {
            "case_type": self.case_type_var.get().strip() or CASE_TYPES[0],
            "case_name": self.case_name_var.get().strip() or f"{entry['test'].get('field', 'Campo')} | Caso {self.selected_case_index + 1}",
            "request_field_path": response_path,
            "request_value": self.request_value_var.get().strip(),
            "response_field_path": response_path,
            "expected_value": self.expected_value_var.get().strip(),
            "action": action,
            "body_template": body_template
        }
        entry["test"]["draft_cases"] = cases
        if actualizar_preview:
            self.actualizar_previews()
            self.render_case_buttons(cases)


    def on_editor_changed(self):
        self.persistir_test_actual(True)


    def actualizar_previews(self):
        entry = self.obtener_test_actual()
        if not entry:
            return
        response_path = entry["response_field_path"]
        body_template = self.body_template_text.get("1.0", "end").strip() or self.base_body_template
        request_value = self.request_value_var.get().strip()
        expected_value = self.expected_value_var.get().strip()
        preview = self.construir_body_preview(body_template, response_path, request_value)
        self.reemplazar_texto(self.body_preview_text, preview, False)
        observed = self.obtener_valor_desde_path(self.response_data, response_path)
        observed_text = self.valor_a_texto(observed)
        self.reemplazar_texto(self.response_value_text, f"Path: {response_path}\n\nValor actual: {observed_text or 'Sin dato'}\n\nValor esperado: {expected_value or 'Sin definir'}", False)


    def construir_body_preview(self, body_template, request_path, request_value):
        if not body_template:
            return "Sin body base disponible para este request."
        try:
            data = json.loads(body_template)
        except json.JSONDecodeError:
            return body_template
        if request_path:
            self.asignar_valor_en_path(data, request_path, self.coercer_valor(request_value))
        return json.dumps(data, indent=4, ensure_ascii=False)


    def asegurar_payload_test(self, entry):
        plan = entry["plan"]
        test_set = entry["test_set"]
        test = entry["test"]
        channel = str(self.request_info.get("transaction_channel", "GENERAL")).strip().upper() or "GENERAL"
        service = str(self.request_info.get("service_name", "Servicio")).strip() or "Servicio"
        version = str(self.request_info.get("version_label", "Sin versión")).strip() or "Sin versión"
        object_path = self.formatear_path(test_set.get("path", "General"))
        field_name = test.get("field", "Campo")
        case_type = self.case_type_var.get().strip() or CASE_TYPES[0]
        test.setdefault(
            "issue_payload",
            {
                "summary": f"[{channel}-Global] {service} | {version} | {object_path} | {field_name} | {case_type} | Global/Esperado",
                "description": (
                    f"Validación del campo {field_name} en {object_path} para el plan {plan.get('tipo_nombre', 'Plan')}. "
                    f"El escenario base corresponde a una prueba {case_type.lower()} y usa el body Bruno de la request seleccionada como machote funcional."
                ),
                "actions": test.get("actions", ""),
                "repository_path": self.repository_path_default
            }
        )
        return test["issue_payload"]


    def guardar_borrador(self):
        entry = self.obtener_test_actual()
        if not entry:
            MessageBox(self, "No hay ningún test seleccionado para guardar.", "warning")
            return
        self.persistir_test_actual(True)
        payload = self.asegurar_payload_test(entry)
        entry["test"]["estado"] = "Diseñado"
        entry["test"]["actions"] = payload.get("actions", "") or self.action_text.get("1.0", "end").strip()
        guardar_planning_crq(self.crq.get("crq", ""), self.planning_data)
        MessageBox(self, f"Se guardó el borrador del test {entry['test'].get('field', 'seleccionado')}.", "success")


    def finalizar(self):
        self.persistir_test_actual(True)
        guardar_planning_crq(self.crq.get("crq", ""), self.planning_data)
        self.navigate("crq_detail", crq=self.crq)


    def obtener_test_actual(self):
        if not self.test_entries or self.selected_test_index >= len(self.test_entries):
            return None
        return self.test_entries[self.selected_test_index]


    def obtener_nombre_plan_actual(self):
        for plan in self.planning_data.get("plans", []):
            if plan.get("tipo_id") == self.current_plan_id:
                return plan.get("tipo_nombre", "Plan")
        return "Plan"


    def obtener_body_bruno_base(self):
        bruno_request = dict(self.request_info.get("bruno_request", {}))
        file_path = str(bruno_request.get("file", "")).strip()
        if not file_path:
            return "{\n\n}"
        path = Path(file_path)
        if not path.exists():
            return "{\n\n}"
        try:
            definition = parsear_archivo_bru(path)
        except Exception:
            return "{\n\n}"
        content = str(definition.get("body", {}).get("content", "")).strip()
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
        for raw_segment in [segmento.strip() for segmento in str(path or "").split(".") if segmento.strip()]:
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
        segments = [segmento.strip() for segmento in str(path or "").split(".") if segmento.strip()]
        if not segments or not isinstance(data, dict):
            return
        current = data
        for index, raw_segment in enumerate(segments):
            is_last = index == len(segments) - 1
            is_array = raw_segment.endswith("[]")
            segment = raw_segment[:-2] if is_array else raw_segment
            if is_last:
                current[segment] = [value] if is_array else value
                return
            next_is_array = segments[index + 1].endswith("[]")
            if is_array:
                container = current.setdefault(segment, [])
                if not container:
                    container.append({})
                if not isinstance(container[0], dict):
                    container[0] = {}
                current = container[0]
                continue
            default = [] if next_is_array else {}
            if not isinstance(current.get(segment), (dict, list)):
                current[segment] = [] if isinstance(default, list) else {}
            current = current[segment]
            if isinstance(current, list):
                if not current:
                    current.append({})
                if not isinstance(current[0], dict):
                    current[0] = {}
                current = current[0]


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
            return json.dumps(value, ensure_ascii=False)
        return str(value)


    def construir_action(self, response_path, request_value, expected_value, body_template):
        return (
            f"Campo validado: {response_path}\n"
            f"Valor enviado en request: {request_value or '-'}\n"
            f"Valor esperado en response: {expected_value or '-'}\n\n"
            "Body base utilizado:\n"
            f"{body_template or '{ }'}"
        )


    def reemplazar_entry(self, entry, value):
        entry.delete(0, "end")
        entry.insert(0, value or "")


    def reemplazar_texto(self, textbox, value, editable):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", value or "")
        if not editable:
            textbox.configure(state="disabled")


    def formatear_path(self, path):
        segmentos = []
        for segmento in str(path or "General").split("."):
            limpio = segmento.replace("[]", "").replace("_", " ").strip()
            if limpio:
                segmentos.append(limpio[:1].upper() + limpio[1:])
        return " > ".join(segmentos) if segmentos else "General"