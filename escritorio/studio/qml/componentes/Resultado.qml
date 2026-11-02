// Resultado — el último trabajo de la herramienta actual (o el trabajo actual en la vista Trabajos): el plan (si fue
// simulación) o las salidas con cada error por su archivo; la tabla de salidas (abrir, mostrar en la carpeta) y la
// vista previa de la elegida (imagen, o texto: una transcripción, un Markdown, unos subtítulos).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: pagina
    readonly property var t: studio.trabajos
    readonly property var o: studio.operaciones
    spacing: 0
    Kirigami.PlaceholderMessage {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: !pagina.t.hayActual && pagina.o.actual === "herramienta"
        text: studio.herramientas.hayActual ? "Sin trabajos de esta herramienta" : "Ningún trabajo"
        explanation: studio.herramientas.hayActual ? "Añade archivos, revisa las opciones y simula (F5): el plan aparece aquí; aplica con Ctrl+Intro." : "Elige una herramienta o un trabajo."
        icon.name: "system-run"
    }
    VistaTexto {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: !pagina.t.hayActual && pagina.o.actual !== "herramienta"
        texto: pagina.o.salida
        mensajeVacio: "Sin salida todavía: ejecuta «" + pagina.o.titulo + "» (F5)"
        iconoVacio: "utilities-terminal"
        nombreAccesible: "Salida de " + pagina.o.titulo
    }
    VistaTexto {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: Kirigami.Units.gridUnit * 6
        visible: pagina.t.hayActual
        texto: pagina.t.resultado
        markdown: true
        mensajeVacio: pagina.t.estado === "en_curso" ? "En curso: " + pagina.t.progreso + " % · " + pagina.t.mensaje : (pagina.t.estado === "en_cola" ? "En cola" : "Sin informe")
        iconoVacio: pagina.t.estado === "en_curso" ? "media-playback-start" : "view-task"
        nombreAccesible: "Resultado de " + (pagina.t.titulo || "ningún trabajo")
    }
    Kirigami.Separator { Layout.fillWidth: true; visible: pagina.t.nSalidas > 0 }
    TablaDatos {
        Layout.fillWidth: true
        Layout.preferredHeight: Kirigami.Units.gridUnit * 7
        visible: pagina.t.nSalidas > 0
        modelo: pagina.t.salidasModelo
        claveAjustes: "salidas"
        umbralEstrecho: 0
        columnas: [{ ancho: 0, minimo: 10, conIcono: true }, { ancho: 7, secundaria: true, estrecho: true }, { ancho: 5, alinear: "derecha", secundaria: true },
                   { ancho: 12, secundaria: true, estrecho: true }]
        onFilaActualCambiada: fila => pagina.t.fijarSalida(fila)
        onActivada: fila => { pagina.t.fijarSalida(fila); studio.acciones.accion("archivo.abrir").disparar() }
        menuContextual: MenuAcciones {
            acciones: studio.acciones
            conAtajos: false
            elementos: [{ tipo: "accion", nombre: "archivo.abrir" }, { tipo: "accion", nombre: "archivo.mostrar" }, { tipo: "accion", nombre: "archivo.copiar" }]
        }
    }
    Image {
        Layout.fillWidth: true
        Layout.preferredHeight: Kirigami.Units.gridUnit * 12
        visible: pagina.t.vistaPrevia === "imagen"
        source: pagina.t.imagenSalida
        fillMode: Image.PreserveAspectFit
        asynchronous: true
        Accessible.name: "Vista previa de " + pagina.t.salidaActual
    }
    VistaTexto {
        Layout.fillWidth: true
        Layout.preferredHeight: Kirigami.Units.gridUnit * 12
        visible: pagina.t.vistaPrevia === "texto"
        texto: pagina.t.textoSalida
        nombreAccesible: "Vista previa de " + pagina.t.salidaActual
    }
}
