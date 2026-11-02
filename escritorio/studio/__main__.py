"""`python3 -m escritorio.studio [archivos…]`: abre Raphi Studio (o le manda los archivos si ya está abierto).

Sin lógica: la aplicación se arma en `escritorio/studio/aplicacion.py`. Corre con el Python del sistema
(/usr/bin/python3), cuyo Qt es el que trae Kirigami; el motor corre como proceso con el `.venv` del repo
(`RAPHI_MOTOR_PYTHON`, o `<repo>/.venv/bin/python` si existe). `raphi` (run.sh) y `python -m escritorio` llegan aquí.

    /usr/bin/python3 -m escritorio.studio                      # desde raphi/ (o con PYTHONPATH=raphi/)
    /usr/bin/python3 -m escritorio.studio --smoke              # construye la interfaz y sale (prueba de humo)
    /usr/bin/python3 -m escritorio.studio --instalar-lanzador  # el acceso directo del menú (-n simula)
"""
import sys

from escritorio.studio.aplicacion import main

sys.exit(main(sys.argv[1:]))
