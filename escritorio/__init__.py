"""Raphi escritorio: la ventana PySide6 que muestra la web de Raphi y le da un puente nativo.

No tiene pantallas propias (regla del 2026-10-27: escritorio y web son la misma aplicación). Lo que hace:

- `servidor.py`: arranca `raphi.escritorio` en 127.0.0.1 con una ficha de un solo uso y lo detiene al salir;
- `ventana.py`: la ventana con QtWebEngine, la ficha puesta donde la cáscara web guarda la sesión, las rutas soltadas
  desde Dolphin entregadas a la web, la bandeja del sistema y su zona flotante para soltar, y una sola instancia
  (abrir archivos desde Dolphin los manda a la ventana que ya está);
- `puente.py`: lo que la web pide por QWebChannel (`window.raphiEscritorio`, ver `web/src/lib/escritorio.ts`);
- `vigilancia.py`: carpetas vigiladas que pasan por una receta;
- `dolphin.py`: los menús del clic derecho en Dolphin.
"""
