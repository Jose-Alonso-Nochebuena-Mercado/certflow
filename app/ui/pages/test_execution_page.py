from datetime import datetime
import json
from pathlib import Path

import customtkinter as ctk

try:
    from PIL import ImageGrab
    from PIL import Image
except Exception:
    ImageGrab = None
    Image = None

from app.services.bruno_runner_service import BrunoExecutionError, ejecutar_request_bruno_preview, parsear_archivo_bru
from app.services.crq_service import construir_nombre_archivo_crq
from app.services.planning_service import cargar_planning_crq
from app.services.test_catalog_service import CatalogoServiciosError, resolver_request
from app.ui.components.message_box import MessageBox
from app.ui.pages.base_page import BasePage
from app.ui.theme.colors import ACCENT_SOFT, BACKGROUND, BORDER, PRIMARY, PRIMARY_LIGHT, PRIMARY_SOFT, SURFACE, SURFACE_ALT, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WARNING_SOFT
from app.ui.theme.dimensions import PAGE_HORIZONTAL_PADDING
from app.ui.theme.styles import SECONDARY_BUTTON, SOFT_CARD_STYLE
from app.ui.theme.typography import BODY, SMALL, SUBTITLE, TITLE, get_font


class TestExecutionPage(BasePage):


    def __init__(self, parent, app, crq=None):
        self.crq = crq or {}
        self.planning_data = {}
        self.request_info = {}
        self.base_body_template = "{\n\n}"
        self.execution_entries = []
        self.selected_index = None
        self.current_result = None
        self.screenshot_dir = None
        self.bruno_logo = None
        self.collection_node_labels = []
        super().__init__(parent, app)


    def build(self):
        self.configure(fg_color=BACKGROUND)
        self.cargar_contexto()
        self.crear_ui()
        self.render_navigation()
        if self.execution_entries:
            self.seleccionar_entry(0)


    def cargar_contexto(self):
        crq_id = str(self.crq.get("crq", "")).strip()
        self.planning_data = cargar_planning_crq(crq_id) or {"crq": crq_id, "plans": []}
        last_request = dict(self.planning_data.get("last_request", {}))

        if not last_request.get("service_id") or not last_request.get("transaction_id"):
            return

        try:
            self.request_info = resolver_request(
                last_request.get("service_id"),
                last_request.get("transaction_id"),
                last_request.get("version_id")
            )
        except CatalogoServiciosError:
            self.request_info = {}
            return

        self.base_body_template = self.obtener_body_bruno_base()
        self.execution_entries = self.construir_execution_entries()


    def crear_ui(self):
        hero = ctk.CTkFrame(self, fg_color="transparent")
        hero.pack(fill="x", padx=PAGE_HORIZONTAL_PADDING, pady=(24, 14))
        ctk.CTkLabel(hero, text="Prueba y Capturas", font=get_font(TITLE), text_color=PRIMARY).pack()
        ctk.CTkLabel(hero, text=f"CRQ activo: {self.crq.get('crq', 'Sin seleccionar')} · Ejecuta cada caso con una vista tipo Bruno y guarda capturas PNG que simulen una sesión real de Bruno.", font=get_font(BODY), text_color=TEXT_SECONDARY, wraplength=1040, justify="center").pack(pady=(8, 0))

        layout = ctk.CTkFrame(self, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=PAGE_HORIZONTAL_PADDING, pady=(0, 18))

        self.navigation_panel = ctk.CTkScrollableFrame(layout, fg_color=SURFACE, corner_radius=20, border_width=1, border_color=BORDER, width=320)
        self.navigation_panel.pack(side="left", fill="y", padx=(0, 14))

        self.workspace = ctk.CTkScrollableFrame(layout, fg_color="transparent")
        self.workspace.pack(side="left", fill="both", expand=True)

        self.summary_card = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        self.summary_card.pack(fill="x", pady=(0, 12))
        self.summary_title = ctk.CTkLabel(self.summary_card, text="Selecciona un caso", font=get_font(SUBTITLE), text_color=PRIMARY)
        self.summary_title.pack(anchor="w", padx=22, pady=(18, 6))
        self.summary_text = ctk.CTkLabel(self.summary_card, text="-", font=get_font(BODY), text_color=TEXT_SECONDARY, justify="left", wraplength=860)
        self.summary_text.pack(anchor="w", padx=22, pady=(0, 18))

        self.capture_surface = ctk.CTkFrame(self.workspace, fg_color="#1E1E1E", corner_radius=14, border_width=1, border_color="#2C2C2C")
        self.capture_surface.pack(fill="both", expand=True, pady=(0, 12))
        self.capture_surface.grid_columnconfigure(0, weight=0)
        self.capture_surface.grid_columnconfigure(1, weight=1)
        self.capture_surface.grid_rowconfigure(0, weight=1)

        self.collection_sidebar = ctk.CTkFrame(self.capture_surface, fg_color="#171717", corner_radius=0, width=250)
        self.collection_sidebar.grid(row=0, column=0, sticky="nsw")
        self.collection_sidebar.grid_propagate(False)
        ctk.CTkLabel(self.collection_sidebar, text="Collections", font=("Arial", 14, "bold"), text_color="#ECECEC").pack(anchor="w", padx=16, pady=(16, 6))
        self.collection_hint = ctk.CTkLabel(self.collection_sidebar, text="Path Bruno activo", font=("Arial", 11), text_color="#9A9A9A")
        self.collection_hint.pack(anchor="w", padx=16, pady=(0, 10))
        self.collection_tree = ctk.CTkFrame(self.collection_sidebar, fg_color="transparent")
        self.collection_tree.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        self.bruno_stage = ctk.CTkFrame(self.capture_surface, fg_color="#1E1E1E", corner_radius=0)
        self.bruno_stage.grid(row=0, column=1, sticky="nsew")

        bruno_header = ctk.CTkFrame(self.bruno_stage, fg_color="#202020", corner_radius=0)
        bruno_header.pack(fill="x", padx=0, pady=0)
        brand = ctk.CTkFrame(bruno_header, fg_color="transparent")
        brand.pack(side="left", padx=14, pady=10)
        self.bruno_logo_label = ctk.CTkLabel(brand, text="")
        self.bruno_logo_label.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(brand, text="Bruno", font=("Arial", 18, "bold"), text_color="#F5F5F5").pack(side="left")
        self.environment_badge = ctk.CTkLabel(bruno_header, text="Production", font=("Arial", 12, "bold"), text_color="#F6B13D", fg_color="#2A241A", corner_radius=12, padx=12, pady=6)
        self.environment_badge.pack(side="right", padx=14)

        toolbar = ctk.CTkFrame(self.bruno_stage, fg_color="#262626", corner_radius=0)
        toolbar.pack(fill="x")
        self.transaction_title_label = ctk.CTkLabel(toolbar, text="Transacción", font=("Arial", 15, "bold"), text_color="#F5F5F5")
        self.transaction_title_label.pack(side="left", padx=14, pady=10)
        self.tab_label = ctk.CTkLabel(toolbar, text="POST Runner", font=("Arial", 12, "bold"), text_color="#E0E0E0", fg_color="#343434", corner_radius=8, padx=12, pady=6)
        self.tab_label.pack(side="left", padx=(6, 0))

        self.request_line = ctk.CTkFrame(self.bruno_stage, fg_color="#303030", corner_radius=0)
        self.request_line.pack(fill="x", padx=14, pady=(12, 10))
        self.method_label = ctk.CTkLabel(self.request_line, text="POST", font=("Arial", 12, "bold"), text_color="#F0F0F0", fg_color="#3A3A3A", corner_radius=10, padx=10, pady=6)
        self.method_label.pack(side="left", padx=(10, 8), pady=8)
        self.url_label = ctk.CTkLabel(self.request_line, text="-", font=("Consolas", 12), text_color="#8AE234", anchor="w")
        self.url_label.pack(side="left", fill="x", expand=True, padx=(0, 10))

        bruno_content = ctk.CTkFrame(self.bruno_stage, fg_color="transparent")
        bruno_content.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        bruno_content.grid_columnconfigure(0, weight=1, uniform="bruno")
        bruno_content.grid_columnconfigure(1, weight=1, uniform="bruno")
        self.request_text = self.crear_bruno_panel(bruno_content, 0, "Body", "JSON", WARNING_SOFT, 390, True)
        self.response_text = self.crear_bruno_panel(bruno_content, 1, "Response", "JSON", ACCENT_SOFT, 390, False)

        self.cargar_logo_bruno()
        self.render_collection_sidebar()

        bottom = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        bottom.pack(fill="both", expand=True, pady=(0, 12))
        meta = ctk.CTkFrame(bottom, fg_color="transparent")
        meta.pack(fill="both", expand=True, padx=18, pady=18)
        meta.grid_columnconfigure(0, weight=1, uniform="meta")
        meta.grid_columnconfigure(1, weight=1, uniform="meta")
        self.execution_text = self.crear_text_panel(meta, 0, "Detalle de ejecución", "Estado HTTP, tiempo y valor encontrado en el campo objetivo.", SURFACE_ALT, 180, False)
        self.capture_text = self.crear_text_panel(meta, 1, "Capturas", "Aquí se mostrará la carpeta de salida y el nombre del último PNG guardado.", SURFACE_ALT, 180, False)

        footer = ctk.CTkFrame(self.workspace, fg_color="transparent")
        footer.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(footer, text="Volver", width=120, height=40, corner_radius=20, command=self.go_back, **SECONDARY_BUTTON).pack(side="right")
        ctk.CTkButton(footer, text="Capturar actual", width=150, height=40, corner_radius=20, fg_color=PRIMARY_SOFT, hover_color=PRIMARY_LIGHT, text_color=PRIMARY, border_width=1, border_color=BORDER, command=self.capturar_actual).pack(side="right", padx=(0, 10))
        ctk.CTkButton(footer, text="Capturar todas", width=150, height=40, corner_radius=20, fg_color=PRIMARY, hover_color=PRIMARY_LIGHT, command=self.capturar_todas).pack(side="right", padx=(0, 10))
        ctk.CTkButton(footer, text="Ejecutar actual", width=150, height=40, corner_radius=20, fg_color=PRIMARY, hover_color=PRIMARY_LIGHT, command=self.ejecutar_actual).pack(side="right", padx=(0, 10))


    def crear_text_panel(self, parent, column, title, hint, tint, height, editable):
        card = ctk.CTkFrame(parent, fg_color=tint, corner_radius=16, border_width=1, border_color=BORDER)
        card.grid(row=0, column=column, sticky="nsew", padx=8)
        card.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(card, text=title, font=get_font(BODY), text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
        ctk.CTkLabel(card, text=hint, font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=400).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))
        textbox = ctk.CTkTextbox(card, height=height, corner_radius=12, border_width=1, border_color=BORDER, fg_color=SURFACE, text_color=TEXT_PRIMARY, wrap="word")
        textbox.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        if not editable:
            textbox.configure(state="disabled")
        return textbox


    def crear_bruno_panel(self, parent, column, title, badge, tint, height, editable):
        card = ctk.CTkFrame(parent, fg_color="#1F1F1F", corner_radius=12, border_width=1, border_color="#313131")
        card.grid(row=0, column=column, sticky="nsew", padx=8)
        card.grid_rowconfigure(2, weight=1)
        tabs = ctk.CTkFrame(card, fg_color="#1F1F1F")
        tabs.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        ctk.CTkLabel(tabs, text=title, font=("Arial", 13, "bold"), text_color="#F5F5F5").pack(side="left")
        ctk.CTkLabel(tabs, text=badge, font=("Arial", 11, "bold"), text_color="#F6B13D").pack(side="right")
        ctk.CTkLabel(card, text="Pretty", font=("Arial", 11), text_color="#BEBEBE").grid(row=1, column=0, sticky="e", padx=12, pady=(0, 8))
        textbox = ctk.CTkTextbox(card, height=height, corner_radius=0, border_width=0, fg_color="#161616", text_color="#E7E7E7", wrap="word", font=("Consolas", 12))
        textbox.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        if not editable:
            textbox.configure(state="disabled")
        return textbox


    def construir_execution_entries(self):
        resultado = []
        firmas = set()
        for plan in self.planning_data.get("plans", []):
            for test_set in plan.get("test_sets", []):
                if not test_set.get("enabled", True):
                    continue
                for test in test_set.get("tests", []):
                    field = str(test.get("field", "")).strip()
                    if not field:
                        continue
                    draft_cases = list(test.get("draft_cases", [])) or [self.crear_caso_default(test_set, test)]
                    for case_index, case in enumerate(draft_cases, start=1):
                        firma = self.construir_firma_ejecucion(plan, test_set, test, case)
                        if firma in firmas:
                            continue
                        firmas.add(firma)
                        resultado.append({
                            "plan": plan,
                            "test_set": test_set,
                            "test": test,
                            "case": case,
                            "case_index": case_index,
                            "response_field_path": case.get("response_field_path") or self.construir_response_path(test_set.get("path", ""), field)
                        })
        return resultado


    def render_navigation(self):
        for widget in self.navigation_panel.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.navigation_panel, text="Casos ejecutables", font=get_font(SUBTITLE), text_color=PRIMARY).pack(anchor="w", padx=16, pady=(16, 4))
        if not self.execution_entries:
            ctk.CTkLabel(self.navigation_panel, text="No hay casos diseñados o no se pudo reconstruir la request Bruno del CRQ.", font=get_font(BODY), text_color=TEXT_MUTED, wraplength=260, justify="left").pack(anchor="w", padx=16, pady=(0, 16))
            return
        for index, entry in enumerate(self.execution_entries):
            label = entry["case"].get("case_name", f"Caso {index + 1}")
            card = ctk.CTkFrame(self.navigation_panel, fg_color=PRIMARY_SOFT if index == self.selected_index else SURFACE_ALT, corner_radius=14, border_width=1, border_color=BORDER)
            card.pack(fill="x", padx=12, pady=(0, 10))
            ctk.CTkButton(card, text=label, anchor="w", height=34, fg_color="transparent", hover_color=PRIMARY_SOFT, text_color=PRIMARY, command=lambda current=index: self.seleccionar_entry(current)).pack(fill="x", padx=8, pady=(8, 4))
            prefijo = "Extra" if self.es_test_set_plan_specific(entry["test_set"]) else entry["plan"].get("tipo_nombre", "Plan")
            ctk.CTkLabel(card, text=f"{prefijo} · {entry['test_set'].get('path', 'General')} · {entry['test'].get('field', 'Campo')}", font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=240).pack(anchor="w", padx=12, pady=(0, 8))


    def seleccionar_entry(self, index):
        self.selected_index = index
        self.render_navigation()
        self.render_entry_actual()
        self.ejecutar_actual()


    def render_entry_actual(self):
        entry = self.obtener_entry_actual()
        if not entry:
            return
        case = entry["case"]
        body = case.get("body_template", self.base_body_template) or self.base_body_template
        self.summary_title.configure(text=case.get("case_name", "Caso"))
        self.summary_text.configure(text=f"Campo objetivo: {entry['response_field_path']}\nCondición: {case.get('comparison_operator', '-')}\nRequest value: {case.get('request_value', '-')}")
        self.tab_label.configure(text=f"{entry['plan'].get('tipo_nombre', 'Plan')} · {case.get('case_name', 'Runner')}")
        self.reemplazar_texto(self.request_text, body, True)
        self.reemplazar_texto(self.response_text, "Esperando ejecución...", False)
        self.actualizar_bruno_contexto_visual(entry)


    def ejecutar_actual(self):
        entry = self.obtener_entry_actual()
        if not entry or not self.request_info:
            return
        body_text = self.request_text.get("1.0", "end").strip() or self.base_body_template
        try:
            resultado = ejecutar_request_bruno_preview(self.request_info, body_override_text=body_text)
        except BrunoExecutionError as error:
            self.current_result = {"error": str(error)}
            self.reemplazar_texto(self.response_text, str(error), False)
            self.reemplazar_texto(self.execution_text, f"Error ejecutando caso\n\n{error}", False)
            return

        self.current_result = resultado
        response_json = resultado.get("response", {})
        response_path = entry["response_field_path"]
        target_value = self.obtener_valor_desde_path(response_json, response_path)
        self.render_response_json(response_json, response_path)
        self.reemplazar_texto(self.execution_text, f"HTTP: {resultado.get('status_code', '-')} {resultado.get('reason', '')}\nTiempo: {resultado.get('elapsed_ms', '-')} ms\n\nCampo objetivo: {self.obtener_ultima_clave_path(response_path)}\nValor encontrado: {self.valor_a_texto(target_value) or 'Sin dato'}", False)


    def capturar_actual(self):
        entry = self.obtener_entry_actual()
        if not entry:
            return
        path = self.guardar_captura_entry(entry)
        if not path:
            return
        self.reemplazar_texto(self.capture_text, f"Última captura guardada en:\n{path}\n\nCarpeta:\n{path.parent}", False)


    def capturar_todas(self):
        if not self.execution_entries:
            MessageBox(self, "No hay casos disponibles para capturar.", "warning")
            return
        saved = []
        for index in range(len(self.execution_entries)):
            self.seleccionar_entry(index)
            self.update_idletasks()
            self.update()
            path = self.guardar_captura_entry(self.execution_entries[index])
            if path:
                saved.append(path)
        if saved:
            self.reemplazar_texto(self.capture_text, f"Se guardaron {len(saved)} capturas.\n\nCarpeta:\n{saved[0].parent}", False)
            MessageBox(self, f"Se guardaron {len(saved)} capturas.", "success")


    def guardar_captura_entry(self, entry):
        if ImageGrab is None:
            MessageBox(self, "Pillow no está disponible para capturar pantallas. Instala dependencias con requirements.txt.", "warning")
            return None
        output_dir = self.obtener_directorio_capturas()
        nombre = self.construir_nombre_captura(entry)
        output_path = output_dir / f"{nombre}.png"
        self.update_idletasks()
        self.update()
        bbox = self.obtener_capture_bbox()
        image = ImageGrab.grab(bbox=bbox)
        image.save(output_path)
        return output_path


    def obtener_directorio_capturas(self):
        if self.screenshot_dir is None:
            base = Path(__file__).resolve().parents[3] / "metadata" / "test_runs"
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            crq_name = construir_nombre_archivo_crq(self.crq.get("crq", ""))
            self.screenshot_dir = base / crq_name / stamp
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        return self.screenshot_dir


    def construir_nombre_captura(self, entry):
        case = entry["case"]
        bruto = "_".join([
            str(entry["test_set"].get("path", "general")),
            str(entry["test"].get("field", "campo")),
            str(case.get("case_name", f"caso_{entry['case_index']}"))
        ])
        return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in bruto).strip("_") or f"caso_{entry['case_index']}"


    def obtener_plan_base_comun(self):
        for plan_id in ["integrado", "accepted"]:
            for plan in self.planning_data.get("plans", []):
                if plan.get("tipo_id") == plan_id:
                    return plan
        planes = self.planning_data.get("plans", [])
        return planes[0] if planes else None


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


    def crear_caso_default(self, test_set, test):
        response_path = self.construir_response_path(test_set.get("path", ""), test.get("field", ""))
        return {
            "case_name": f"{test.get('field', 'Campo')} | Base",
            "request_value": "",
            "comparison_operator": "Igual",
            "response_field_path": response_path,
            "body_template": self.base_body_template
        }


    def aplicar_request_value(self, body_template, request_path, request_value):
        if not request_path:
            return body_template
        try:
            data = json.loads(body_template)
        except json.JSONDecodeError:
            return body_template
        self.asignar_valor_en_path(data, request_path, self.coercer_valor(request_value))
        return json.dumps(data, indent=4, ensure_ascii=False)


    def render_response_json(self, response_json, response_path):
        content, target_line = self.serializar_json_con_linea_objetivo(response_json, response_path)
        self.reemplazar_texto(self.response_text, content, False)
        try:
            self.response_text.configure(state="normal")
            self.response_text.tag_delete("target_row")
            self.response_text.tag_config("target_row", background="#DDF5E4", foreground="#124B2E")
            if target_line is not None:
                self.response_text.tag_add("target_row", f"{target_line}.0", f"{target_line}.end")
                self.centrar_linea_texto(self.response_text, target_line)
            self.response_text.configure(state="disabled")
        except Exception:
            self.response_text.configure(state="disabled")


    def actualizar_bruno_contexto_visual(self, entry):
        bruno_request = dict(self.request_info.get("bruno_request", {}))
        try:
            definition = parsear_archivo_bru(Path(str(bruno_request.get("file", "")).strip()))
            self.method_label.configure(text=str(definition.get("method", "POST")).upper())
            self.url_label.configure(text=str(definition.get("url", "-")).strip() or "-")
        except Exception:
            self.method_label.configure(text="POST")
            self.url_label.configure(text="-")
        self.transaction_title_label.configure(text=str(self.request_info.get("transaction_name", "Transacción")).strip() or "Transacción")
        self.environment_badge.configure(text=self.obtener_environment_label(entry))
        self.render_collection_sidebar()


    def cargar_logo_bruno(self):
        if Image is None:
            return
        image_path = Path(__file__).resolve().parents[1] / "assets" / "bruno.png"
        if not image_path.exists():
            return
        try:
            image = Image.open(image_path)
            self.bruno_logo = ctk.CTkImage(light_image=image, dark_image=image, size=(24, 24))
            self.bruno_logo_label.configure(image=self.bruno_logo)
        except Exception:
            pass


    def render_collection_sidebar(self):
        for widget in self.collection_tree.winfo_children():
            widget.destroy()

        segments = self.obtener_collection_segments()
        if not segments:
            ctk.CTkLabel(self.collection_tree, text="Sin colección Bruno asociada", font=("Arial", 11), text_color="#8C8C8C").pack(anchor="w", padx=8, pady=(4, 0))
            return

        for index, segment in enumerate(segments):
            is_last = index == len(segments) - 1
            prefix = "▾" if index == 0 else ("└" if is_last else "├")
            text_color = "#F5F5F5" if is_last else "#B8B8B8"
            fg_color = "#2A2A2A" if is_last else "transparent"
            label = ctk.CTkLabel(
                self.collection_tree,
                text=f"{prefix} {segment}",
                font=("Consolas", 11, "bold" if is_last else "normal"),
                text_color=text_color,
                fg_color=fg_color,
                corner_radius=8,
                anchor="w",
                padx=8,
                pady=6
            )
            label.pack(fill="x", padx=6, pady=(0, 4))

        libraries = list(self.request_info.get("transaction_libraries", []))
        if libraries:
            ctk.CTkLabel(self.collection_tree, text="Libraries", font=("Arial", 11, "bold"), text_color="#9A9A9A").pack(anchor="w", padx=8, pady=(10, 4))
            for library in libraries:
                ctk.CTkLabel(self.collection_tree, text=f"• {library}", font=("Consolas", 10), text_color="#B8B8B8", anchor="w").pack(fill="x", padx=10, pady=(0, 2))


    def obtener_collection_segments(self):
        bruno_request = dict(self.request_info.get("bruno_request", {}))
        logical_path = str(bruno_request.get("logical_path", "")).strip()
        if logical_path:
            return [segment for segment in logical_path.split("/") if segment]

        segments = []
        collection = str(bruno_request.get("collection", "")).strip()
        folder = str(bruno_request.get("folder", "")).strip()
        request = str(bruno_request.get("request", "")).strip()
        if collection:
            segments.append(collection)
        if folder:
            segments.extend([segment for segment in folder.split("/") if segment])
        if request:
            segments.append(request)
        return segments


    def obtener_environment_label(self, entry):
        payload = dict(entry.get("plan", {}).get("issue_payload", {}))
        return str(payload.get("environment_label", "Production")).strip() or "Production"


    def obtener_capture_bbox(self):
        scale = self.obtener_escala_pantalla()
        x = self.capture_surface.winfo_rootx()
        y = self.capture_surface.winfo_rooty()
        width = self.capture_surface.winfo_width()
        height = self.capture_surface.winfo_height()
        return (
            int(x * scale),
            int(y * scale),
            int((x + width) * scale),
            int((y + height) * scale)
        )


    def obtener_escala_pantalla(self):
        try:
            return max(1.0, float(self.winfo_fpixels("1i")) / 72.0)
        except Exception:
            return 1.0


    def es_test_set_plan_specific(self, test_set):
        source = dict(test_set.get("source", {}))
        return bool(source.get("plan_specific"))


    def construir_firma_ejecucion(self, plan, test_set, test, case):
        if self.es_test_set_plan_specific(test_set):
            return "|".join([
                str(plan.get("tipo_id", "")),
                str(test_set.get("path", "")),
                str(test.get("field", "")),
                str(case.get("case_name", ""))
            ])
        return "|".join([
            "common",
            str(test_set.get("path", "")),
            str(test.get("field", "")),
            str(case.get("case_name", ""))
        ])


    def serializar_json_con_linea_objetivo(self, value, target_path):
        lines = []
        target_line = None

        def walk(node, indent=0, path=""):
            nonlocal target_line
            prefix = "    " * indent
            if isinstance(node, dict):
                lines.append(f"{prefix}{{")
                items = list(node.items())
                for index, (key, child) in enumerate(items):
                    child_path = f"{path}.{key}" if path else key
                    suffix = "," if index < len(items) - 1 else ""
                    child_prefix = "    " * (indent + 1)
                    if isinstance(child, dict):
                        lines.append(f'{child_prefix}"{key}": {{')
                        walk(child, indent + 2, child_path)
                        lines.append(f'{child_prefix}}}{suffix}')
                    elif isinstance(child, list):
                        lines.append(f'{child_prefix}"{key}": [')
                        walk_list(child, indent + 2, f"{child_path}[]")
                        lines.append(f'{child_prefix}]{suffix}')
                    else:
                        serialized = json.dumps(child, ensure_ascii=False)
                        lines.append(f'{child_prefix}"{key}": {serialized}{suffix}')
                        if child_path == target_path:
                            target_line = len(lines)
                lines.append(f"{prefix}}}")
                return
            lines.append(f"{prefix}{json.dumps(node, ensure_ascii=False)}")

        def walk_list(node, indent=0, path=""):
            nonlocal target_line
            prefix = "    " * indent
            for index, child in enumerate(node):
                suffix = "," if index < len(node) - 1 else ""
                if isinstance(child, dict):
                    lines.append(f"{prefix}{{")
                    items = list(child.items())
                    for child_index, (key, grandchild) in enumerate(items):
                        child_path = f"{path}.{key}" if path else key
                        child_suffix = "," if child_index < len(items) - 1 else ""
                        child_prefix = "    " * (indent + 1)
                        if isinstance(grandchild, dict):
                            lines.append(f'{child_prefix}"{key}": {{')
                            walk(grandchild, indent + 2, child_path)
                            lines.append(f'{child_prefix}}}{child_suffix}')
                        elif isinstance(grandchild, list):
                            lines.append(f'{child_prefix}"{key}": [')
                            walk_list(grandchild, indent + 2, f"{child_path}[]")
                            lines.append(f'{child_prefix}]{child_suffix}')
                        else:
                            serialized = json.dumps(grandchild, ensure_ascii=False)
                            lines.append(f'{child_prefix}"{key}": {serialized}{child_suffix}')
                            if child_path == target_path:
                                target_line = len(lines)
                    lines.append(f"{prefix}}}{suffix}")
                elif isinstance(child, list):
                    lines.append(f"{prefix}[")
                    walk_list(child, indent + 1, f"{path}[]")
                    lines.append(f"{prefix}]{suffix}")
                else:
                    lines.append(f"{prefix}{json.dumps(child, ensure_ascii=False)}{suffix}")
                    if path == target_path:
                        target_line = len(lines)

        if isinstance(value, list):
            lines.append("[")
            walk_list(value, 1, "[]")
            lines.append("]")
        elif isinstance(value, dict):
            walk(value, 0, "")
        else:
            lines.append(json.dumps(value, ensure_ascii=False))

        return "\n".join(lines), target_line


    def centrar_linea_texto(self, textbox, line_number):
        try:
            total_lines = max(1, int(textbox.index("end-1c").split(".")[0]))
            visible_lines = max(1, int(textbox.winfo_height() / 20))
            target = max(0, line_number - (visible_lines // 2))
            textbox.yview_moveto(min(1.0, target / total_lines))
            textbox.see(f"{line_number}.0")
        except Exception:
            try:
                textbox.see(f"{line_number}.0")
            except Exception:
                pass


    def obtener_entry_actual(self):
        if self.selected_index is None or self.selected_index >= len(self.execution_entries):
            return None
        return self.execution_entries[self.selected_index]


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
        for raw_segment in [segment.strip() for segment in str(path or "").split(".") if segment.strip()]:
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
        segments = [segment.strip() for segment in str(path or "").split(".") if segment.strip()]
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
            if not isinstance(current.get(segment), (dict, list)):
                current[segment] = [] if next_is_array else {}
            current = current[segment]
            if isinstance(current, list):
                if not current:
                    current.append({})
                if not isinstance(current[0], dict):
                    current[0] = {}
                current = current[0]


    def coercer_valor(self, value):
        text = str(value or "").strip()
        if text == "":
            return ""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            lowered = text.lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False
            if lowered == "null":
                return None
            return text


    def valor_a_texto(self, value):
        if value is None:
            return ""
        if isinstance(value, (dict, list, bool, int, float)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)


    def obtener_ultima_clave_path(self, path):
        segments = [segment.strip() for segment in str(path or "").split(".") if segment.strip()]
        if not segments:
            return ""
        return segments[-1].replace("[]", "")


    def reemplazar_texto(self, textbox, value, editable):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", value or "")
        if not editable:
            textbox.configure(state="disabled")