from datetime import datetime

import customtkinter as ctk

from app.services.planning_service import cargar_planning_crq, guardar_planning_crq
from app.ui.pages.base_page import BasePage
from app.ui.theme.colors import BACKGROUND, BORDER, PRIMARY, PRIMARY_LIGHT, PRIMARY_SOFT, SURFACE, SURFACE_ALT, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY
from app.ui.theme.dimensions import PAGE_HORIZONTAL_PADDING
from app.ui.theme.styles import SECONDARY_BUTTON, SOFT_CARD_STYLE
from app.ui.theme.typography import BODY, SMALL, SUBTITLE, TITLE, get_font


TYPOLOGY_NAME_BY_PLAN_ID = {
    "integrado": "Integration",
    "accepted": "Acceptance",
    "regresion": "Regression"
}


class TestPlanDesignPage(BasePage):


    def __init__(self, parent, app, crq=None, planning_data=None, request_info=None, response_data=None):
        self.crq = crq or {}
        self.planning_data = planning_data
        self.request_info = request_info or {}
        self.response_data = response_data or {}
        self.selected_plan_index = None
        self.initial_plan_index = 0
        super().__init__(parent, app)


    def build(self):
        self.configure(fg_color=BACKGROUND)
        self.cargar_contexto()
        self.crear_ui()
        self.render_navigation()
        self.seleccionar_plan(self.initial_plan_index, persist_current=False)


    def cargar_contexto(self):
        if not self.planning_data:
            self.planning_data = cargar_planning_crq(self.crq.get("crq", "")) or {"crq": self.crq.get("crq", ""), "plans": []}

        planes = self.planning_data.get("plans", [])
        prioritario = self.obtener_indice_plan("integrado")
        self.initial_plan_index = prioritario if prioritario is not None else 0

        for plan in planes:
            self.asegurar_payload_plan(plan)


    def crear_ui(self):
        hero = ctk.CTkFrame(self, fg_color="transparent")
        hero.pack(fill="x", padx=PAGE_HORIZONTAL_PADDING, pady=(24, 14))

        ctk.CTkLabel(hero, text="Configurar Test Plan", font=get_font(TITLE), text_color=PRIMARY).pack()
        ctk.CTkLabel(
            hero,
            text=(
                f"CRQ activo: {self.crq.get('crq', 'Sin seleccionar')} · "
                "Aquí defines la información del Test Plan y la etiqueta de ambiente que verás en la vista Bruno de este plan."
            ),
            font=get_font(BODY),
            text_color=TEXT_SECONDARY,
            wraplength=1040,
            justify="center"
        ).pack(pady=(8, 0))

        layout = ctk.CTkFrame(self, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=PAGE_HORIZONTAL_PADDING, pady=(0, 18))

        self.navigation_panel = ctk.CTkScrollableFrame(layout, fg_color=SURFACE, corner_radius=20, border_width=1, border_color=BORDER, width=320)
        self.navigation_panel.pack(side="left", fill="y", padx=(0, 14))

        self.workspace = ctk.CTkScrollableFrame(layout, fg_color="transparent")
        self.workspace.pack(side="left", fill="both", expand=True)

        self.detail_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        self.detail_card.pack(fill="x", pady=(0, 12))

        self.plan_title = ctk.CTkLabel(self.detail_card, text="Selecciona un plan", font=get_font(SUBTITLE), text_color=PRIMARY)
        self.plan_title.pack(anchor="w", padx=22, pady=(18, 6))

        self.plan_hint = ctk.CTkLabel(self.detail_card, text="Aquí se captura el summary, la descripción, la tipología y las fechas del Test Plan.", font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=760)
        self.plan_hint.pack(anchor="w", padx=22, pady=(0, 18))

        self.form_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        self.form_card.pack(fill="x", pady=(0, 12))

        form = ctk.CTkFrame(self.form_card, fg_color="transparent")
        form.pack(fill="x", padx=22, pady=22)
        form.grid_columnconfigure(0, weight=1, uniform="plan_form")
        form.grid_columnconfigure(1, weight=1, uniform="plan_form")

        self.summary_entry = self.crear_field_entry(form, 0, 0, "Summary")
        self.typology_entry = self.crear_field_entry(form, 0, 1, "Typology")
        self.begin_entry = self.crear_field_entry(form, 1, 0, "Begin date")
        self.end_entry = self.crear_field_entry(form, 1, 1, "End date")
        self.environment_entry = self.crear_field_entry(form, 2, 0, "Bruno environment label")
        self.description_text = self.crear_textbox(form, 3, "Description", height=140)

        self.info_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        self.info_card.pack(fill="x", pady=(0, 12))
        self.info_title = ctk.CTkLabel(self.info_card, text="Test Sets del plan", font=get_font(SUBTITLE), text_color=PRIMARY)
        self.info_title.pack(anchor="w", padx=22, pady=(18, 6))
        self.info_text = ctk.CTkLabel(self.info_card, text="-", font=get_font(BODY), text_color=TEXT_PRIMARY, justify="left", wraplength=860)
        self.info_text.pack(anchor="w", padx=22, pady=(0, 18))

        footer = ctk.CTkFrame(self.workspace, fg_color="transparent")
        footer.pack(fill="x", pady=(0, 8))

        ctk.CTkButton(footer, text="Volver a añadir tests", width=180, height=40, corner_radius=20, command=lambda: self.navigate("add_tests", crq=self.crq), **SECONDARY_BUTTON).pack(side="right")
        ctk.CTkButton(footer, text="Continuar a Test Sets", width=190, height=40, corner_radius=20, fg_color=PRIMARY_SOFT, hover_color=PRIMARY_LIGHT, text_color=PRIMARY, border_width=1, border_color=BORDER, command=self.continuar_a_test_sets).pack(side="right", padx=(0, 10))


    def crear_field_entry(self, parent, row, column, label):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(wrapper, text=label, font=get_font(SMALL), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))
        entry = ctk.CTkEntry(wrapper, height=38, corner_radius=12, border_color=BORDER, fg_color=SURFACE_ALT, text_color=TEXT_PRIMARY)
        entry.pack(fill="x")
        entry.bind("<KeyRelease>", lambda _event: self.persistir_plan_actual())
        return entry


    def crear_textbox(self, parent, row, label, height=100):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(wrapper, text=label, font=get_font(SMALL), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))
        textbox = ctk.CTkTextbox(wrapper, height=height, corner_radius=12, border_width=1, border_color=BORDER, fg_color=SURFACE_ALT, text_color=TEXT_PRIMARY)
        textbox.pack(fill="x")
        textbox.bind("<KeyRelease>", lambda _event: self.persistir_plan_actual())
        return textbox


    def render_navigation(self):
        for widget in self.navigation_panel.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.navigation_panel, text="Planes del CRQ", font=get_font(SUBTITLE), text_color=PRIMARY).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(self.navigation_panel, text="Integrado va primero. Aquí capturas datos del plan y su ambiente; los Test Sets y Tests se ajustan en los siguientes pasos.", font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=260).pack(anchor="w", padx=16, pady=(0, 12))

        for index, plan in enumerate(self.planning_data.get("plans", [])):
            card = ctk.CTkFrame(self.navigation_panel, fg_color=PRIMARY_SOFT if index == self.selected_plan_index else SURFACE_ALT, corner_radius=14, border_width=1, border_color=BORDER)
            card.pack(fill="x", padx=12, pady=(0, 10))

            ctk.CTkButton(card, text=plan.get("tipo_nombre", "Plan"), anchor="w", height=34, fg_color="transparent", hover_color=PRIMARY_SOFT, text_color=PRIMARY, command=lambda current=index: self.seleccionar_plan(current)).pack(fill="x", padx=8, pady=(8, 4))

            detalle = f"{len(plan.get('test_sets', []))} test sets seleccionados"
            ctk.CTkLabel(card, text=detalle, font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left").pack(anchor="w", padx=12, pady=(0, 8))


    def seleccionar_plan(self, index, persist_current=True):
        if not self.planning_data.get("plans"):
            return
        if persist_current and self.selected_plan_index is not None:
            self.persistir_plan_actual()
        self.selected_plan_index = index
        self.render_navigation()
        self.render_plan_actual()


    def render_plan_actual(self):
        plan = self.obtener_plan_actual()
        if not plan:
            return

        payload = self.asegurar_payload_plan(plan)
        self.plan_title.configure(text=f"{plan.get('tipo_nombre', 'Plan')} · Test Plan")
        self.plan_hint.configure(text=f"Objetivo del cambio: {self.obtener_objetivo_cambio()}\nEstrategia base: {plan.get('estrategia', '-')}")
        self.reemplazar_entry(self.summary_entry, payload.get("summary", ""))
        self.reemplazar_entry(self.typology_entry, payload.get("typology_name", ""))
        self.reemplazar_entry(self.begin_entry, payload.get("begin_date", ""))
        self.reemplazar_entry(self.end_entry, payload.get("end_date", ""))
        self.reemplazar_entry(self.environment_entry, payload.get("environment_label", ""))
        self.reemplazar_texto(self.description_text, payload.get("description", ""))

        test_sets = self.obtener_nombres_test_sets_comunes()
        detalle = "\n".join(f"- {nombre}" for nombre in test_sets[:10]) or "No hay Test Sets activos todavía."
        if len(test_sets) > 10:
            detalle += f"\n... y {len(test_sets) - 10} más"
        self.info_text.configure(text=detalle)


    def persistir_plan_actual(self):
        plan = self.obtener_plan_actual()
        if not plan:
            return
        payload = self.asegurar_payload_plan(plan)
        payload["summary"] = self.summary_entry.get().strip()
        payload["typology_name"] = self.typology_entry.get().strip()
        payload["begin_date"] = self.begin_entry.get().strip()
        payload["end_date"] = self.end_entry.get().strip()
        payload["environment_label"] = self.environment_entry.get().strip()
        payload["description"] = self.description_text.get("1.0", "end").strip()


    def asegurar_payload_plan(self, plan):
        service_name = str(self.request_info.get("service_name", "Servicio")).strip() or "Servicio"
        version_label = str(self.request_info.get("version_label", "Sin versión")).strip() or "Sin versión"
        objetivo = self.obtener_objetivo_cambio()
        today = self.crq.get("fecha_instalacion", "") or datetime.now().strftime("%Y-%m-%d")

        plan.setdefault(
            "issue_payload",
            {
                "summary": f"[{self.crq.get('crq', '-')}] {service_name} | {version_label} | {plan.get('tipo_nombre', 'Plan')}",
                "description": (
                    f"Test Plan de tipo {plan.get('tipo_nombre', 'Plan')} para el servicio {service_name} {version_label}. "
                    f"Objetivo del cambio: {objetivo}. Estrategia inicial: {plan.get('estrategia', '-') }"
                ),
                "typology_name": TYPOLOGY_NAME_BY_PLAN_ID.get(plan.get("tipo_id", ""), plan.get("tipo_nombre", "")),
                "environment_label": "Production",
                "begin_date": today,
                "end_date": today
            }
        )
        return plan["issue_payload"]


    def obtener_objetivo_cambio(self):
        return str(self.crq.get("objetivo_cambio", "") or self.crq.get("descripcion", "Sin objetivo detallado")).strip()


    def obtener_indice_plan(self, tipo_id):
        for index, plan in enumerate(self.planning_data.get("plans", [])):
            if plan.get("tipo_id") == tipo_id:
                return index
        return None


    def obtener_plan_actual(self):
        planes = self.planning_data.get("plans", [])
        if not planes or self.selected_plan_index >= len(planes):
            return None
        return planes[self.selected_plan_index]


    def continuar_a_test_sets(self):
        self.persistir_plan_actual()
        guardar_planning_crq(self.crq.get("crq", ""), self.planning_data)
        plan = self.obtener_plan_actual()
        if not plan:
            MessageBox(self, "No hay planes configurados para continuar.", "warning")
            return
        self.navigate("test_set_design", crq=self.crq, planning_data=self.planning_data, request_info=self.request_info, response_data=self.response_data, current_plan_id=plan.get("tipo_id"))


    def reemplazar_entry(self, entry, value):
        entry.delete(0, "end")
        entry.insert(0, value or "")


    def reemplazar_texto(self, textbox, value):
        textbox.delete("1.0", "end")
        textbox.insert("1.0", value or "")


    def obtener_nombres_test_sets_comunes(self):
        for plan_id in ["integrado", "accepted"]:
            indice = self.obtener_indice_plan(plan_id)
            if indice is None:
                continue
            plan = self.planning_data.get("plans", [])[indice]
            return [
                test_set.get("nombre", test_set.get("path", "General"))
                for test_set in plan.get("test_sets", [])
                if test_set.get("enabled", True)
            ]
        plan = self.obtener_plan_actual() or {}
        return [
            test_set.get("nombre", test_set.get("path", "General"))
            for test_set in plan.get("test_sets", [])
            if test_set.get("enabled", True)
        ]