import os
import threading
import subprocess
from django.apps import AppConfig


class AppConfig(AppConfig):
    name = 'app'

    def ready(self):
        # import the dynamically placed models so Django's migration
        # autodetector will see CTe and NFSe when running ``makemigrations``.
        # without this import the modules live in a nonstandard package
        # (app/db_GDF/CTe and app/db_GDF/NFSe) and are not imported by
        # default during app registry initialization.
        try:
            import app.db_GDF.CTe.models  # noqa: F401
            import app.db_GDF.NFSe.models  # noqa: F401
            import app.db_GDF.sped_fiscal.models  # noqa: F401
            import app.db_GDF.sped_contribuicao.models  # noqa: F401
            import app.db_GDF.reprocessamento.models  # noqa: F401
        except ImportError:
            # during early development the modules may not exist yet
            pass

    # if os.environ.get('RUN_MAIN', None) == 'true':
    #     def run_streamlit():        
    #         # Caminho da raiz do projeto
    #         print("Iniciando Streamlit automaticamente...")
    #         project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #         streamlit_file = os.path.join(
    #             project_root,
    #             "streamlit",
    #             "home.py"
    #         )
    #         subprocess.Popen(
    #             [
    #                 "streamlit", "run", streamlit_file,
    #                 "--server.address=0.0.0.0",
    #                 "--server.port=8601",
    #                 "--server.enableCORS=false"
    #             ],
    #             cwd=project_root
    #         )

    #     threading.Thread(target=run_streamlit, daemon=True).start()

