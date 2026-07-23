from copy import deepcopy

import customtkinter as ctk

from app.services.planning_service import cargar_planning_crq, guardar_planning_crq
from app.ui.pages.base_page import BasePage
from app.ui.theme.colors import BACKGROUND, BORDER, PRIMARY, PRIMARY_LIGHT, PRIMARY_SOFT, SURFACE, SURFACE_ALT, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY
from app.ui.theme.dimensions import PAGE_HORIZONTAL_PADDING
from app.ui.theme.styles import SECONDARY_BUTTON, SOFT_CARD_STYLE
from app.ui.theme.typography import BODY, SMALL, SUBTITLE, TITLE, get_font


class TestSetDesignPage(BasePage):


    def __init__(self, parent, app, crq=None, planning_data=None, request_info=None, response_data=None, current_plan_id=None):
        self.crq = crq or {}
        self.planning_data = planning_data
        self.request_info = request_info or {}
        self.response_data = response_data or {}
        self.current_plan_id = current_plan_id
        self.plan_sequence = []
        self.current_plan_index = 0
        self.selected_test_set_index = None
        self.test_set_vars = {}
        self.summary_entry = None
        self.description_text = None
        self.repository_entry = None
        super().__init__(parent, app)


    def build(self):
        self.configure(fg_color=BACKGROUND)
        self.cargar_contexto()
        self.crear_ui()
        self.render_navigation()
        self.seleccionar_test_set(0, persist_current=False)


    def cargar_contexto(self):
        if not self.planning_data:
            self.planning_data = cargar_planning_crq(self.crq.get("crq", "")) or {"crq": self.crq.get("crq", ""), "plans": []}

        self.plan_sequence = [plan.get("tipo_id") for plan in self.planning_data.get("plans", [])]

        if self.current_plan_id in self.plan_sequence:
            self.current_plan_index = self.plan_sequence.index(self.current_plan_id)
        elif "integrado" in self.plan_sequence:
            self.current_plan_index = self.plan_sequence.index("integrado")
            self.current_plan_id = "integrado"
        elif self.plan_sequence:
            self.current_plan_index = 0
            self.current_plan_id = self.plan_sequence[0]

        for plan in self.planning_data.get("plans", []):
            for test_set in plan.get("test_sets", []):
                test_set.setdefault("enabled", True)
                self.asegurar_payload_test_set(plan, test_set)


    def crear_ui(self):
        hero = ctk.CTkFrame(self, fg_color="transparent")
        hero.pack(fill="x", padx=PAGE_HORIZONTAL_PADDING, pady=(24, 14))

        ctk.CTkLabel(hero, text="Configurar Test Sets", font=get_font(TITLE), text_color=PRIMARY).pack()
        ctk.CTkLabel(hero, text="Ajusta los Test Sets del plan actual. Integrado y Aceptación comparten la base, pero Aceptación puede tener extras exclusivos cuando el flujo lo requiera.", font=get_font(BODY), text_color=TEXT_SECONDARY, wraplength=1040, justify="center").pack(pady=(8, 0))

        layout = ctk.CTkFrame(self, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=PAGE_HORIZONTAL_PADDING, pady=(0, 18))

        self.navigation_panel = ctk.CTkScrollableFrame(layout, fg_color=SURFACE, corner_radius=20, border_width=1, border_color=BORDER, width=340)
        self.navigation_panel.pack(side="left", fill="y", padx=(0, 14))

        self.workspace = ctk.CTkScrollableFrame(layout, fg_color="transparent")
        self.workspace.pack(side="left", fill="both", expand=True)

        self.plan_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        self.plan_card.pack(fill="x", pady=(0, 12))
        self.plan_title = ctk.CTkLabel(self.plan_card, text="Plan", font=get_font(SUBTITLE), text_color=PRIMARY)
        self.plan_title.pack(anchor="w", padx=22, pady=(18, 6))
        self.plan_hint = ctk.CTkLabel(self.plan_card, text="-", font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=760)
        self.plan_hint.pack(anchor="w", padx=22, pady=(0, 18))

        self.detail_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        self.detail_card.pack(fill="x", pady=(0, 12))
        self.detail_title = ctk.CTkLabel(self.detail_card, text="Selecciona un Test Set", font=get_font(SUBTITLE), text_color=PRIMARY)
        self.detail_title.pack(anchor="w", padx=22, pady=(18, 6))
        self.detail_hint = ctk.CTkLabel(self.detail_card, text="Los sets comunes se replican entre Integrado y Aceptación. Si este plan necesita uno extra, se crea aquí sin afectar la base común.", font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=760)
        self.detail_hint.pack(anchor="w", padx=22, pady=(0, 18))

        self.form_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        self.form_card.pack(fill="x", pady=(0, 12))
        form = ctk.CTkFrame(self.form_card, fg_color="transparent")
        form.pack(fill="x", padx=22, pady=22)
        self.summary_entry = self.crear_field(form, "Summary")
        self.repository_entry = self.crear_field(form, "Repository path")
        self.description_text = self.crear_textbox(form, "Description")

        footer = ctk.CTkFrame(self.workspace, fg_color="transparent")
        footer.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(footer, text="Volver a Test Plan", width=170, height=40, corner_radius=20, command=self.volver_a_test_plan, **SECONDARY_BUTTON).pack(side="right")
        if self.plan_actual_permite_extras():
            ctk.CTkButton(footer, text="Agregar extra del plan", width=180, height=40, corner_radius=20, fg_color=PRIMARY, hover_color=PRIMARY_LIGHT, command=self.agregar_test_set_extra).pack(side="right", padx=(0, 10))
        ctk.CTkButton(footer, text="Continuar a Tests", width=180, height=40, corner_radius=20, fg_color=PRIMARY_SOFT, hover_color=PRIMARY_LIGHT, text_color=PRIMARY, border_width=1, border_color=BORDER, command=self.continuar_a_tests).pack(side="right", padx=(0, 10))


    def crear_field(self, parent, label):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(wrapper, text=label, font=get_font(SMALL), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))
        entry = ctk.CTkEntry(wrapper, height=38, corner_radius=12, border_color=BORDER, fg_color=SURFACE_ALT, text_color=TEXT_PRIMARY)
        entry.pack(fill="x")
        entry.bind("<KeyRelease>", lambda _event: self.persistir_test_set_actual())
        return entry


    def crear_textbox(self, parent, label):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(wrapper, text=label, font=get_font(SMALL), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 6))
        textbox = ctk.CTkTextbox(wrapper, height=120, corner_radius=12, border_width=1, border_color=BORDER, fg_color=SURFACE_ALT, text_color=TEXT_PRIMARY)
        textbox.pack(fill="x")
        textbox.bind("<KeyRelease>", lambda _event: self.persistir_test_set_actual())
        return textbox


    def render_navigation(self):
        for widget in self.navigation_panel.winfo_children():
            widget.destroy()

        plan = self.obtener_plan_actual()
        if not plan:
            return

        comunes, extras = self.separar_test_sets(plan.get("test_sets", []))
        self.plan_title.configure(text=f"Plan actual: {plan.get('tipo_nombre', 'Plan')}")
        self.plan_hint.configure(text=f"{len(comunes)} test sets comunes y {len(extras)} extras exclusivos de este plan. Los comunes se sincronizan entre Integrado y Aceptación; los extras se quedan solo aquí.")

        ctk.CTkLabel(self.navigation_panel, text="Test Sets del plan", font=get_font(SUBTITLE), text_color=PRIMARY).pack(anchor="w", padx=16, pady=(16, 4))

        for index, test_set in enumerate(plan.get("test_sets", [])):
            path = self.construir_key_visual_test_set(test_set, index)
            variable = self.test_set_vars.get(path)

            if variable is None:
                variable = ctk.BooleanVar(value=test_set.get("enabled", True))
                self.test_set_vars[path] = variable

            card = ctk.CTkFrame(self.navigation_panel, fg_color=PRIMARY_SOFT if index == self.selected_test_set_index else SURFACE_ALT, corner_radius=14, border_width=1, border_color=BORDER)
            card.pack(fill="x", padx=12, pady=(0, 10))

            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(10, 4))

            check = ctk.CTkCheckBox(header, text="", width=20, variable=variable, fg_color=PRIMARY, hover_color=PRIMARY_LIGHT, border_color=PRIMARY, command=lambda current=index: self.toggle_test_set(current))
            check.pack(side="left")
            ctk.CTkButton(header, text=test_set.get("path", "General"), anchor="w", height=30, fg_color="transparent", hover_color=PRIMARY_SOFT, text_color=PRIMARY, command=lambda current=index: self.seleccionar_test_set(current)).pack(side="left", fill="x", expand=True, padx=(6, 0))

            prefijo = "Extra" if self.es_test_set_plan_specific(test_set) else "Común"
            estado = f"{prefijo} · {'Activo' if variable.get() else 'Excluido'}"
            ctk.CTkLabel(card, text=estado, font=get_font(SMALL), text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(0, 10))


    def toggle_test_set(self, index):
        plan = self.obtener_plan_actual()
        if not plan:
            return
        test_set = plan.get("test_sets", [])[index]
        path = self.construir_key_visual_test_set(test_set, index)
        test_set["enabled"] = bool(self.test_set_vars[path].get())
        self.render_navigation()
        self.render_test_set_actual()


    def seleccionar_test_set(self, index, persist_current=True):
        if persist_current and self.selected_test_set_index is not None:
            self.persistir_test_set_actual()
        self.selected_test_set_index = index
        self.render_navigation()
        self.render_test_set_actual()


    def render_test_set_actual(self):
        test_set = self.obtener_test_set_actual()
        if not test_set:
            return
        payload = self.asegurar_payload_test_set(self.obtener_plan_actual(), test_set)
        self.detail_title.configure(text=f"{test_set.get('path', 'General')} · Test Set")
        self.reemplazar_entry(self.summary_entry, payload.get("summary", ""))
        self.reemplazar_entry(self.repository_entry, payload.get("repository_path", self.request_info.get("repository_folder", "")))
        self.reemplazar_texto(self.description_text, payload.get("description", ""))


    def persistir_test_set_actual(self):
        test_set = self.obtener_test_set_actual()
        if not test_set:
            return
        payload = self.asegurar_payload_test_set(self.obtener_plan_actual(), test_set)
        payload["summary"] = self.summary_entry.get().strip()
        payload["repository_path"] = self.repository_entry.get().strip()
        payload["description"] = self.description_text.get("1.0", "end").strip()
        self.sincronizar_test_sets_comunes()


    def asegurar_payload_test_set(self, plan, test_set):
        channel = str(self.request_info.get("transaction_channel", "GENERAL")).strip().upper() or "GENERAL"
        service = str(self.request_info.get("service_name", "Servicio")).strip() or "Servicio"
        version = str(self.request_info.get("version_label", "Sin versión")).strip() or "Sin versión"
        object_path = self.formatear_path(test_set.get("path", "General"))
        repository_path = str(self.request_info.get("repository_folder", "")).strip()

        test_set.setdefault(
            "issue_payload",
            {
                "summary": f"[{channel}-Global] {service} | {version} | {object_path}",
                "description": (
                    f"Agrupa los tests funcionales asociados al objeto {object_path}. "
                    "Aquí se decide si el set se conserva tal cual, se amplía con más tests o se excluye del plan."
                ),
                "repository_path": repository_path
            }
        )
        return test_set["issue_payload"]


    def obtener_plan_actual(self):
        for plan in self.planning_data.get("plans", []):
            if plan.get("tipo_id") == self.current_plan_id:
                return plan
        return self.planning_data.get("plans", [None])[0]


    def obtener_plan_base_comun(self):
        for plan_id in ["integrado", "accepted"]:
            for plan in self.planning_data.get("plans", []):
                if plan.get("tipo_id") == plan_id:
                    return plan
        return self.obtener_plan_actual()


    def obtener_test_set_actual(self):
        plan = self.obtener_plan_actual()
        test_sets = plan.get("test_sets", []) if plan else []
        if not test_sets or self.selected_test_set_index >= len(test_sets):
            return None
        return test_sets[self.selected_test_set_index]


    def sincronizar_test_sets_comunes(self):
        base_plan = self.obtener_plan_base_comun()
        if not base_plan:
            return
        visibles = self.obtener_plan_actual() or base_plan
        common_sets, _ = self.separar_test_sets(visibles.get("test_sets", []))
        base_sets = deepcopy(common_sets)
        for plan in self.planning_data.get("plans", []):
            if plan.get("tipo_id") not in {"integrado", "accepted"}:
                continue
            _, extras = self.separar_test_sets(plan.get("test_sets", []))
            plan["test_sets"] = deepcopy(base_sets) + deepcopy(extras)


    def agregar_test_set_extra(self):
        plan = self.obtener_plan_actual()
        if not plan:
            return
        indice = 1 + len([test_set for test_set in plan.get("test_sets", []) if self.es_test_set_plan_specific(test_set)])
        tipo = plan.get("tipo_id", "plan")
        path = f"extra_{tipo}_{indice}"
        nuevo = {
            "path": path,
            "nombre": f"Extra {plan.get('tipo_nombre', 'Plan')} {indice}",
            "enabled": True,
            "tests": [],
            "source": {
                "plan_specific": True,
                "plan_id": tipo
            }
        }
        self.asegurar_payload_test_set(plan, nuevo)
        plan.setdefault("test_sets", []).append(nuevo)
        self.selected_test_set_index = len(plan.get("test_sets", [])) - 1
        self.render_navigation()
        self.render_test_set_actual()


    def plan_actual_permite_extras(self):
        plan = self.obtener_plan_actual() or {}
        return plan.get("tipo_id") in {"accepted", "regresion"}


    def es_test_set_plan_specific(self, test_set):
        source = dict(test_set.get("source", {}))
        return bool(source.get("plan_specific"))


    def separar_test_sets(self, test_sets):
        comunes = []
        extras = []
        for test_set in test_sets or []:
            if self.es_test_set_plan_specific(test_set):
                extras.append(test_set)
            else:
                comunes.append(test_set)
        return comunes, extras


    def construir_key_visual_test_set(self, test_set, index):
        prefijo = "extra" if self.es_test_set_plan_specific(test_set) else "common"
        return f"{prefijo}:{test_set.get('path', f'set_{index}')}:{index}"


    def volver_a_test_plan(self):
        self.persistir_test_set_actual()
        guardar_planning_crq(self.crq.get("crq", ""), self.planning_data)
        self.navigate("test_plan_design", crq=self.crq, planning_data=self.planning_data, request_info=self.request_info, response_data=self.response_data)


    def continuar_a_tests(self):
        self.persistir_test_set_actual()
        guardar_planning_crq(self.crq.get("crq", ""), self.planning_data)
        self.navigate("test_case_design", crq=self.crq, planning_data=self.planning_data, request_info=self.request_info, response_data=self.response_data, current_plan_id=self.current_plan_id)


    def reemplazar_entry(self, entry, value):
        entry.delete(0, "end")
        entry.insert(0, value or "")


    def reemplazar_texto(self, textbox, value):
        textbox.delete("1.0", "end")
        textbox.insert("1.0", value or "")


    def formatear_path(self, path):
        segmentos = []
        for segmento in str(path or "General").split("."):
            limpio = segmento.replace("[]", "").replace("_", " ").strip()
            if limpio:
                segmentos.append(limpio[:1].upper() + limpio[1:])
        return " > ".join(segmentos) if segmentos else "General"