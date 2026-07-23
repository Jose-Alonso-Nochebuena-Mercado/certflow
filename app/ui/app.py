import customtkinter as ctk

from app.ui.components.header import Header

from app.ui.theme.dimensions import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT
)
from app.ui.theme.colors import BACKGROUND

from app.core.router import Router



class CertFlowApp(ctk.CTk):


    def __init__(self):

        super().__init__()


        self.title(
            "CertFlow"
        )


        self.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )


        self.configure(
            fg_color=BACKGROUND
        )


        self.resizable(
            False,
            False
        )


        self.crear_layout()


        self.load_home()



    def crear_layout(self):


        self.header = Header(
            self,
            self
        )


        self.header.pack(
            fill="x"
        )


        self.page_container = ctk.CTkFrame(
            self,
            fg_color=BACKGROUND
        )


        self.page_container.pack(
            fill="both",
            expand=True
        )


        self.router = Router(
            self,
            self.page_container
        )


        self.header.refresh_navigation()



    def load_home(self):

        self.router.navigate(
            "home"
        )



    def clear_container(self):


        for widget in self.page_container.winfo_children():

            widget.destroy()