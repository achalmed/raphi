"""`python -m escritorio [--web] [archivos…]`: abre Raphi Studio, el escritorio nativo de la familia de los studios
(o le manda los archivos si ya está abierto). Con `--web`, o si `gui_comun` no está (Raphi instalado fuera del espacio de
trabajo), la ventana que muestra la web."""
import sys

from escritorio.studio import hay_gui_comun

if "--web" in sys.argv[1:] or not hay_gui_comun():
    from escritorio.ventana import main
    sys.exit(main([a for a in sys.argv[1:] if a != "--web"]))

from escritorio.studio.app import main

sys.exit(main())
