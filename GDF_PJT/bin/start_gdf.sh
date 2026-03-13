#!/bin/bash
echo Inicializando o GDF - SPED REINF
cd /app/gdf_v2/GDF_PJT
# SAP RFC SDK (PyRFC)
if [ -d /app/gdf_v2/nwrfcsdk/lib ]; then
  export LD_LIBRARY_PATH="/app/gdf_v2/nwrfcsdk/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
source venv/bin/activate

gunicorn --bind 0.0.0.0:8500 GDF_PJT.wsgi:application

#python3 manage.py runserver_plus --cert-file cert.crt 0.0.0.0:8500
#streamlit run streamlit/main.py   --server.port 8600   --server.sslCertFile cert.crt   --server.sslKeyFile cert.key

