class Router:

    def __init__(
        self,
        app,
        container
    ):

        self.app = app
        self.container = container
        self.current_page = None
        self.current_route = None
        self.current_kwargs = {}
        self.history = []


    def navigate(
        self,
        route,
        add_to_history=True,
        **page_kwargs
    ):

        from app.ui.pages.home_page import HomePage
        from app.ui.pages.new_crq_page import NewCRQPage
        from app.ui.pages.metadata_page import MetadataPage
        from app.ui.pages.discovery_page import DiscoveryPage
        from app.ui.pages.crq_detail_page import CRQDetailPage
        from app.ui.pages.add_tests_page import AddTestsPage
        from app.ui.pages.test_plan_design_page import TestPlanDesignPage
        from app.ui.pages.test_set_design_page import TestSetDesignPage
        from app.ui.pages.test_case_design_page import TestCaseDesignPage
        from app.ui.pages.test_design_page import TestDesignPage
        from app.ui.pages.settings_page import SettingsPage


        if self.current_page:

            self.current_page.destroy()


        pages = {

            "home":
                HomePage,

            "new_crq":
                NewCRQPage,

            "metadata":
                MetadataPage,

            "discovery":
                DiscoveryPage,

            "crq_detail":
                CRQDetailPage,

            "add_tests":
                AddTestsPage,

            "test_plan_design":
                TestPlanDesignPage,

            "test_set_design":
                TestSetDesignPage,

            "test_case_design":
                TestCaseDesignPage,

            "test_design":
                TestDesignPage,

            "settings":
                SettingsPage

        }


        page_class = pages.get(
            route
        )


        if not page_class:

            print(
                f"Ruta no encontrada: {route}"
            )

            return


        if self.current_route and add_to_history:

            self.history.append(
                (
                    self.current_route,
                    self.current_kwargs
                )
            )


        self.current_page = page_class(
            self.container,
            self.app,
            **page_kwargs
        )

        self.current_route = route
        self.current_kwargs = dict(
            page_kwargs
        )


        self.current_page.pack(
            fill="both",
            expand=True
        )


        if hasattr(
            self.app,
            "header"
        ):

            self.app.header.refresh_navigation()


    def go_back(self):

        if not self.history:

            self.navigate(
                "home",
                add_to_history=False
            )

            return


        route, kwargs = self.history.pop()

        self.navigate(
            route,
            add_to_history=False,
            **kwargs
        )
