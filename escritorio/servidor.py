"""El servidor local de la ventana: `python -m raphi.escritorio` en un puerto libre, con su ficha de un solo uso."""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


class Servidor:
    def __init__(self) -> None:
        self.ficha = secrets.token_urlsafe(32)
        self.puerto: int | None = None
        self.proceso: subprocess.Popen | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.puerto}"

    def arrancar(self, tope: float = 30) -> None:
        entorno = {**os.environ, "RAPHI_FICHA": self.ficha, "RAPHI_MODO": "escritorio",
                   "PYTHONPATH": f"{RAIZ}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"}
        self.proceso = subprocess.Popen([sys.executable, "-m", "raphi.escritorio", "--puerto", "0"], cwd=RAIZ, env=entorno,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        inicio = time.monotonic()
        for linea in self.proceso.stdout:
            if linea.startswith("RAPHI_PUERTO="):
                self.puerto = int(linea.split("=", 1)[1])
                break
            if time.monotonic() - inicio > tope:
                break
        if not self.puerto:
            self.detener()
            raise RuntimeError("El servidor de Raphi no arrancó.")
        while time.monotonic() - inicio < tope:
            try:
                with urllib.request.urlopen(f"{self.url}/api/health", timeout=1) as r:
                    if r.status == 200:
                        return
            except OSError:
                time.sleep(0.15)
        self.detener()
        raise RuntimeError("El servidor de Raphi arrancó pero no responde.")

    def pedir(self, ruta: str, cuerpo: dict | None = None, metodo: str | None = None) -> dict | list:
        """Una petición a la API con la ficha (para lo que el escritorio hace por su cuenta: carpetas vigiladas)."""
        datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
        peticion = urllib.request.Request(f"{self.url}{ruta}", data=datos, method=metodo or ("POST" if datos else "GET"),
                                          headers={"Authorization": f"Bearer {self.ficha}", "Content-Type": "application/json"})
        with urllib.request.urlopen(peticion, timeout=30) as r:
            return json.loads(r.read() or b"null")

    def detener(self) -> None:
        if self.proceso and self.proceso.poll() is None:
            self.proceso.terminate()
            try:
                self.proceso.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.proceso.kill()
        self.proceso = None
