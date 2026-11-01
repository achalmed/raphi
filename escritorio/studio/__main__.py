"""`python -m escritorio.studio [archivos…]`: abre Raphi Studio (o le manda los archivos si ya está abierto)."""
import sys

from escritorio.studio.app import main

sys.exit(main())
