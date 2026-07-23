import calendar
from datetime import datetime

import customtkinter as ctk

from app.ui.theme.colors import (
    PRIMARY,
    PRIMARY_LIGHT,
    PRIMARY_SOFT,
    SURFACE,
    SURFACE_ALT,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    SECONDARY_HOVER
)

from app.ui.theme.typography import (
    BODY,
    SMALL,
    get_font
)


class DatePicker(ctk.CTkFrame):


    def __init__(
        self,
        parent,
        initial_date=None,
        width=420,
        height=42
    ):

        super().__init__(
            parent,
            fg_color="transparent"
        )

        self.width = width
        self.height = height
        self.selected_date = self.parse_date(initial_date) or datetime.now()
        self.visible_year = self.selected_date.year
        self.visible_month = self.selected_date.month

        self.crear_ui()
        self.set(self.selected_date.strftime("%Y-%m-%d"))


    def crear_ui(self):

        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self,
            width=self.width,
            height=self.height,
            corner_radius=14,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            font=get_font(BODY)
        )
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Button-1>", self.abrir_calendario)

        self.button = ctk.CTkButton(
            self,
            text="▾",
            width=42,
            height=self.height,
            corner_radius=14,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            text_color=SURFACE,
            command=self.abrir_calendario
        )
        self.button.grid(row=0, column=1, padx=(8, 0))


    def get(self):

        return self.entry.get().strip()


    def set(self, value):

        self.entry.delete(0, "end")
        self.entry.insert(0, value)

        fecha = self.parse_date(value)
        if fecha:
            self.selected_date = fecha
            self.visible_year = fecha.year
            self.visible_month = fecha.month


    def parse_date(self, value):

        if not value:
            return None

        if isinstance(value, datetime):
            return value

        try:
            return datetime.strptime(str(value), "%Y-%m-%d")
        except ValueError:
            return None


    def abrir_calendario(self, event=None):

        if hasattr(self, "popup") and self.popup.winfo_exists():
            self.popup.focus()
            return

        self.popup = CalendarPopup(
            self,
            self.selected_date,
            self.seleccionar_fecha,
            self.visible_year,
            self.visible_month
        )


    def seleccionar_fecha(self, selected_date):

        self.selected_date = selected_date
        self.visible_year = selected_date.year
        self.visible_month = selected_date.month
        self.set(selected_date.strftime("%Y-%m-%d"))


class CalendarPopup(ctk.CTkToplevel):


    def __init__(
        self,
        parent,
        selected_date,
        on_select,
        initial_year,
        initial_month
    ):

        super().__init__(parent)

        self.on_select = on_select
        self.selected_date = selected_date
        self.visible_year = initial_year
        self.visible_month = initial_month

        self.title("Seleccionar fecha")
        self.geometry("320x320")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self.crear_ui()
        self.dibujar_calendario()


    def crear_ui(self):

        card = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=18,
            border_width=1,
            border_color=BORDER
        )
        card.pack(fill="both", expand=True, padx=14, pady=14)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(14, 12))

        prev_btn = ctk.CTkButton(
            header,
            text="‹",
            width=28,
            height=28,
            corner_radius=14,
            fg_color=PRIMARY_SOFT,
            hover_color=SECONDARY_HOVER,
            text_color=PRIMARY,
            command=self.mes_anterior
        )
        prev_btn.pack(side="left")

        self.month_label = ctk.CTkLabel(
            header,
            text="",
            font=get_font(BODY),
            text_color=TEXT_PRIMARY
        )
        self.month_label.pack(side="left", expand=True)

        next_btn = ctk.CTkButton(
            header,
            text="›",
            width=28,
            height=28,
            corner_radius=14,
            fg_color=PRIMARY_SOFT,
            hover_color=SECONDARY_HOVER,
            text_color=PRIMARY,
            command=self.mes_siguiente
        )
        next_btn.pack(side="right")

        self.days_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.days_frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=14, pady=(6, 14))

        hoy_btn = ctk.CTkButton(
            footer,
            text="Hoy",
            width=72,
            height=32,
            corner_radius=16,
            fg_color=PRIMARY_SOFT,
            hover_color=SECONDARY_HOVER,
            text_color=PRIMARY,
            border_width=1,
            border_color=BORDER,
            command=self.ir_hoy
        )
        hoy_btn.pack(side="left")

        cerrar_btn = ctk.CTkButton(
            footer,
            text="Cerrar",
            width=82,
            height=32,
            corner_radius=16,
            fg_color=PRIMARY,
            hover_color=PRIMARY_LIGHT,
            text_color=SURFACE,
            command=self.destroy
        )
        cerrar_btn.pack(side="right")


    def dibujar_calendario(self):

        self.limpiar_calendario()
        self.configurar_titulo_mes()
        self.configurar_columnas()
        self.crear_encabezados_semana()

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.visible_year, self.visible_month)
        today = datetime.now()

        for week_index, week in enumerate(weeks, start=1):
            for day_index, day in enumerate(week):
                if day == 0:
                    self.crear_espaciador(week_index, day_index)
                    continue

                current = datetime(self.visible_year, self.visible_month, day)
                self.crear_boton_dia(current, today, week_index, day_index)


    def limpiar_calendario(self):

        for widget in self.days_frame.winfo_children():
            widget.destroy()


    def configurar_titulo_mes(self):

        self.month_label.configure(
            text=f"{calendar.month_name[self.visible_month]} {self.visible_year}"
        )


    def configurar_columnas(self):

        for column in range(7):
            self.days_frame.grid_columnconfigure(column, weight=1, uniform="calendar_cols")


    def crear_encabezados_semana(self):

        weekdays = ["L", "M", "M", "J", "V", "S", "D"]
        for idx, weekday in enumerate(weekdays):
            label = ctk.CTkLabel(
                self.days_frame,
                text=weekday,
                font=get_font(SMALL),
                text_color=TEXT_MUTED
            )
            label.grid(row=0, column=idx, pady=(0, 6))


    def crear_espaciador(self, row, column):

        spacer = ctk.CTkLabel(self.days_frame, text="")
        spacer.grid(row=row, column=column, padx=2, pady=2)


    def crear_boton_dia(self, current, today, row, column):

        estilos = self.obtener_estilos_dia(current, today)
        btn = ctk.CTkButton(
            self.days_frame,
            text=str(current.day),
            width=34,
            height=30,
            corner_radius=12,
            fg_color=estilos["fg_color"],
            hover_color=SECONDARY_HOVER,
            text_color=estilos["text_color"],
            border_width=estilos["border_width"],
            border_color=estilos["border_color"],
            font=get_font(SMALL),
            command=lambda value=current: self.confirmar(value)
        )
        btn.grid(row=row, column=column, padx=2, pady=2, sticky="ew")


    def obtener_estilos_dia(self, current, today):

        is_selected = current.date() == self.selected_date.date()
        is_today = current.date() == today.date()

        fg_color = "transparent"
        text_color = TEXT_PRIMARY
        border_width = 0
        border_color = BORDER

        if is_selected:
            fg_color = PRIMARY
            text_color = SURFACE
        elif is_today:
            fg_color = SURFACE_ALT
            text_color = PRIMARY
            border_width = 1
            border_color = PRIMARY_SOFT

        return {
            "fg_color": fg_color,
            "text_color": text_color,
            "border_width": border_width,
            "border_color": border_color
        }


    def mes_anterior(self):

        if self.visible_month == 1:
            self.visible_month = 12
            self.visible_year -= 1
        else:
            self.visible_month -= 1

        self.dibujar_calendario()


    def mes_siguiente(self):

        if self.visible_month == 12:
            self.visible_month = 1
            self.visible_year += 1
        else:
            self.visible_month += 1

        self.dibujar_calendario()


    def ir_hoy(self):

        hoy = datetime.now()
        self.visible_year = hoy.year
        self.visible_month = hoy.month
        self.confirmar(hoy)


    def confirmar(self, date_value):

        self.selected_date = date_value
        self.on_select(date_value)
        self.destroy()
        border_color = PRIMARY_SOFT

        return {
            "fg_color": fg_color,
            "text_color": text_color,
            "border_width": border_width,
            "border_color": border_color
        }


    def mes_anterior(self):

        if self.visible_month == 1:

            self.visible_month = 12
            self.visible_year -= 1

        else:

            self.visible_month -= 1

            self.dibujar_calendario()


    def mes_siguiente(self):

        if self.visible_month == 12:

            self.visible_month = 1
            self.visible_year += 1

        else:

            self.visible_month += 1

        self.dibujar_calendario()


    def ir_hoy(self):

        hoy = datetime.now()
        self.visible_year = hoy.year
        self.visible_month = hoy.month
        self.confirmar(hoy)


    def confirmar(self, date_value):

        self.selected_date = date_value
        self.on_select(date_value)
        self.destroy()



