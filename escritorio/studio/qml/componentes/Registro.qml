// Registro — lo que el corredor del motor escribió durante el trabajo actual (cada archivo con su resultado o su error).
import QtQuick
import GuiComun

VistaTexto {
    readonly property var t: studio.trabajos
    texto: t.registro
    mensajeVacio: !t.hayActual ? "Ningún trabajo" : (t.estado === "en_curso" ? "En curso: la salida íntegra está en el panel inferior (F4)" : "Sin registro")
    iconoVacio: "text-x-log"
    nombreAccesible: "Registro de " + (t.titulo || "ningún trabajo")
}
