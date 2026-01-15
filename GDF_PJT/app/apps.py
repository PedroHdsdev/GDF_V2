import os
import threading
import subprocess
from django.apps import AppConfig


class AppConfig(AppConfig):
    name = 'app'

    if os.environ.get('RUN_MAIN', None) == 'true':

        def run_streamlit():        
            # Caminho da raiz do projeto
            print("Iniciando Streamlit automaticamente...")
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            streamlit_file = os.path.join(
                project_root,
                "streamlit",
                "home.py"
            )
                
            subprocess.Popen(
                [
                    "streamlit", "run", streamlit_file,
                    "--server.address=0.0.0.0",
                    "--server.port=8901",
                    "--server.enableCORS=false"
                ],
                cwd=project_root
            )

        #threading.Thread(target=run_streamlit, daemon=True).start()