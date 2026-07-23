import customtkinter as ctk



class BasePage(ctk.CTkFrame):


    def __init__(
        self,
        parent,
        app
    ):


        super().__init__(
            parent
        )


        self.app = app


        self.router = app.router


        self.configure(
            fg_color="transparent"
        )


        self.build()



    def build(self):
        """
        Método que deben implementar
        las páginas hijas.
        """

        raise NotImplementedError(
            "La página debe implementar build()"
        )



    def clear_page(self):

        """
        Limpia todos los componentes
        de la página actual.
        """

        for widget in self.winfo_children():

            widget.destroy()



    def navigate(
        self,
        route,
        **kwargs
    ):

        """
        Atajo para navegación.

        Ejemplo:

        self.navigate("home")

        """

        self.router.navigate(
            route,
            **kwargs
        )


    def go_back(self):

        self.router.go_back()
