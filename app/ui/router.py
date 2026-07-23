from app.ui.pages.home_page import HomePage
from app.ui.pages.new_crq_page import NewCRQPage


class Router:
    def __init__(self, app, container):
        """
        app:
            instancia principal de CertFlowApp

        container:
            frame donde se cargarán las páginas
        """
        self.app = app
        self.container = container

        self.routes = {
            "home":
                HomePage,

            "new_crq":
                NewCRQPage
        }

        self.current_page = None



    def navigate(self, route):
        """
        Cambia la página actual.

        Ejemplo:

        router.navigate("home")

        router.navigate("new_crq")

        """


        if route not in self.routes:

            raise Exception(
                f"Ruta no encontrada: {route}"
            )



        page_class = self.routes[route]

        self.clear()

        self.current_page = page_class(
            self.container,
            self.app
        )


        self.current_page.pack(
            fill="both",
            expand=True
        )



    def clear(self):

        """
        Limpia la página actual.
        """

        if self.current_page:

            self.current_page.destroy()

