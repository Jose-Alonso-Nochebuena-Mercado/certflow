from datetime import datetime
import json
from pathlib import Path

import customtkinter as ctk

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None

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
        ctk.CTkLabel(hero, text=f"CRQ activo: {self.crq.get('crq', 'Sin seleccionar')} · Ejecuta cada caso con una vista tipo Bruno y guarda capturas PNG para revisión manual.", font=get_font(BODY), text_color=TEXT_SECONDARY, wraplength=1040, justify="center").pack(pady=(8, 0))

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

        panels = ctk.CTkFrame(self.workspace, **SOFT_CARD_STYLE)
        panels.pack(fill="both", expand=True, pady=(0, 12))
        content = ctk.CTkFrame(panels, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18, pady=18)
        content.grid_columnconfigure(0, weight=1, uniform="bruno")
        content.grid_columnconfigure(1, weight=1, uniform="bruno")
        self.request_text = self.crear_text_panel(content, 0, "Body", "Body ejecutable. Puedes ajustarlo y volver a lanzar el caso actual.", WARNING_SOFT, 360, True)
        self.response_text = self.crear_text_panel(content, 1, "Response", "Respuesta JSON real de la request. Se resalta la clave objetivo cuando aparece.", ACCENT_SOFT, 360, False)

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


    def construir_execution_entries(self):
        resultado = []
        plan = self.obtener_plan_base_comun()
        if not plan:
            return resultado
        for test_set in plan.get("test_sets", []):
            if not test_set.get("enabled", True):
                continue
            for test in test_set.get("tests", []):
                field = str(test.get("field", "")).strip()
                if not field:
                    continue
                draft_cases = list(test.get("draft_cases", [])) or [self.crear_caso_default(test_set, test)]
                for case_index, case in enumerate(draft_cases, start=1):
                    resultado.append({
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
            ctk.CTkLabel(card, text=f"{entry['test_set'].get('path', 'General')} · {entry['test'].get('field', 'Campo')}", font=get_font(SMALL), text_color=TEXT_SECONDARY, justify="left", wraplength=240).pack(anchor="w", padx=12, pady=(0, 8))


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
        body = self.aplicar_request_value(body, entry["response_field_path"], case.get("request_value", ""))
        self.summary_title.configure(text=case.get("case_name", "Caso"))
        self.summary_text.configure(text=f"Campo objetivo: {entry['response_field_path']}\nCondición: {case.get('comparison_operator', '-')}\nRequest value: {case.get('request_value', '-')}")
        self.reemplazar_texto(self.request_text, body, True)
        self.reemplazar_texto(self.response_text, "Esperando ejecución...", False)


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
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        width = self.winfo_width()
        height = self.winfo_height()
        image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
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
        content = json.dumps(response_json, indent=4, ensure_ascii=False)
        field_name = self.obtener_ultima_clave_path(response_path)
        self.reemplazar_texto(self.response_text, content, False)
        try:
            self.response_text.configure(state="normal")
            self.response_text.tag_delete("target_key")
            self.response_text.tag_config("target_key", background="#FFF0B3", foreground="#222222")
            pattern = f'"{field_name}"'
            start = "1.0"
            while True:
                match = self.response_text.search(pattern, start, stopindex="end")
                if not match:
                    break
                end = f"{match}+{len(pattern)}c"
                self.response_text.tag_add("target_key", match, end)
                start = end
            self.response_text.configure(state="disabled")
        except Exception:
            self.response_text.configure(state="disabled")


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