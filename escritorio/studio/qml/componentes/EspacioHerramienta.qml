// EspacioHerramienta — el espacio de trabajo de la herramienta elegida (reingeniería X3; en el taller del 2026-11-18,
// sin columna de entradas: lo que entró está en la zona para soltar de arriba, y el avance, en la cola de la derecha):
// arriba, qué es (icono, nombre, áreas, formatos, qué le falta, su ficha); en el centro el monitor con la vista previa
// de la entrada elegida o del resultado; a la derecha las opciones generadas de su ficha y dónde dejar la salida.
// Simular (F5) y Procesar (Ctrl+Intro) están en la barra de arriba y al pie de las opciones.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: raiz
    readonly property var h: studio.herramientas
    readonly property var a: studio.archivos
    readonly property var t: studio.trabajos
    readonly property var v: studio.vista
    property string monitor: "entrada"                   // entrada · resultado
    spacing: 0

    function quitarSeleccion() { if (a.fila >= 0) a.quitar(a.fila) }
    function verEntrada(i) {
        a.fijarFila(i)
        monitor = "entrada"
        v.mostrar(a.rutaActual)
    }
    function verSalida(ruta) {
        monitor = "resultado"
        v.mostrar(ruta)
    }

    Connections {
        target: raiz.t
        function onTerminado(id, simulado, estado) {
            if (raiz.h.hayActual && raiz.t.ref === raiz.h.ref && raiz.t.nSalidas > 0) raiz.verSalida(raiz.t.salidas[0])
            else if (raiz.h.hayActual && raiz.t.ref === raiz.h.ref) raiz.monitor = "resultado"
        }
    }
    Connections {
        target: raiz.a
        function onCambiado() { if (raiz.monitor === "entrada" && raiz.v.ruta !== raiz.a.rutaActual && raiz.a.total > 0 && raiz.a.rutaActual === "") raiz.verEntrada(0) }
    }
    Connections { target: raiz.h; function onActualCambiado() { raiz.monitor = "entrada"; raiz.v.mostrar(raiz.a.rutaActual || (raiz.a.total ? raiz.a.rutas[0] : "")) } }

    Kirigami.PlaceholderMessage {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: !raiz.h.hayActual
        icon.name: "view-grid"
        text: "Ninguna herramienta abierta"
        explanation: "Elige una en el catálogo (Ctrl+1)."
    }

    // ------------------------------------------------------------------ qué es
    RowLayout {
        visible: raiz.h.hayActual
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing
        Kirigami.Icon { source: raiz.h.icono; implicitWidth: Kirigami.Units.iconSizes.large; implicitHeight: implicitWidth }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            Kirigami.Heading { level: 2; text: raiz.h.titulo; elide: Text.ElideRight; Layout.fillWidth: true }
            QQC2.Label { text: raiz.h.descripcion; wrapMode: Text.WordWrap; Layout.fillWidth: true; maximumLineCount: 2; elide: Text.ElideRight }
            QQC2.Label {
                text: raiz.h.textoAreas + " · acepta " + raiz.h.textoAcepta + (raiz.h.larga ? " · tarda: verás su progreso" : "")
                color: Kirigami.Theme.disabledTextColor
                font: Kirigami.Theme.smallFont
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
        }
        QQC2.Button { text: "Ficha"; icon.name: "help-about"; flat: true; onClicked: ficha.open() }
    }
    Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.leftMargin: Kirigami.Units.largeSpacing
        Layout.rightMargin: Kirigami.Units.largeSpacing
        visible: raiz.h.hayActual && raiz.h.faltan.length > 0
        type: Kirigami.MessageType.Warning
        text: "Falta en esta máquina: " + raiz.h.faltan.join(", ") + ". Sin eso la herramienta no puede correr (Herramientas › Lo que falta…)."
    }
    Kirigami.Separator { Layout.fillWidth: true; visible: raiz.h.hayActual }

    // ------------------------------------------------------------------ monitor · opciones
    QQC2.SplitView {
        visible: raiz.h.hayActual
        Layout.fillWidth: true
        Layout.fillHeight: true
        orientation: Qt.Horizontal

        ColumnLayout {                                                     // monitor
            QQC2.SplitView.fillWidth: true
            QQC2.SplitView.minimumWidth: Kirigami.Units.gridUnit * 16
            spacing: 0
            QQC2.TabBar {
                Layout.fillWidth: true
                currentIndex: raiz.monitor === "entrada" ? 0 : 1
                QQC2.TabButton { text: "Entrada"; onClicked: { raiz.monitor = "entrada"; raiz.v.mostrar(raiz.a.rutaActual || (raiz.a.total ? raiz.a.rutas[0] : "")) } }
                QQC2.TabButton {
                    text: "Resultado" + (raiz.t.hayActual && raiz.t.ref === raiz.h.ref && raiz.t.nSalidas > 0 ? " · " + raiz.t.nSalidas : "")
                    onClicked: { raiz.monitor = "resultado"; raiz.v.mostrar(raiz.t.ref === raiz.h.ref ? raiz.t.salidaActual : "") }
                }
            }
            // las salidas del último trabajo de esta herramienta (o su plan, si fue simulado)
            Flow {
                Layout.fillWidth: true
                Layout.margins: Kirigami.Units.smallSpacing
                visible: raiz.monitor === "resultado" && raiz.t.hayActual && raiz.t.ref === raiz.h.ref && raiz.t.nSalidas > 0
                spacing: Kirigami.Units.smallSpacing
                Repeater {
                    model: raiz.monitor === "resultado" && raiz.t.ref === raiz.h.ref ? raiz.t.salidas : []
                    delegate: QQC2.Button {
                        required property var modelData
                        required property int index
                        text: String(modelData).split("/").pop()
                        icon.name: "document-preview"
                        checkable: true
                        checked: raiz.v.ruta === String(modelData)
                        onClicked: { raiz.t.fijarSalida(index); raiz.verSalida(String(modelData)) }
                    }
                }
            }
            VistaPrevia {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: raiz.monitor === "entrada" || (raiz.t.ref === raiz.h.ref && raiz.t.nSalidas > 0)
                vacio: raiz.monitor === "entrada" ? "Elige una entrada arriba para verla aquí, o suelta archivos desde Dolphin" : "Procesa (Ctrl+Intro) para ver el resultado"
            }
            VistaTexto {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: !(raiz.monitor === "entrada" || (raiz.t.ref === raiz.h.ref && raiz.t.nSalidas > 0))
                markdown: true
                texto: raiz.t.hayActual && raiz.t.ref === raiz.h.ref ? raiz.t.resultado : ""
                mensajeVacio: "Sin resultado todavía: simula (F5) para ver el plan, o procesa (Ctrl+Intro)"
                iconoVacio: "view-task"
                nombreAccesible: "Resultado"
            }
        }

        Opciones {                                                         // opciones
            QQC2.SplitView.preferredWidth: Kirigami.Units.gridUnit * 22
            QQC2.SplitView.minimumWidth: Kirigami.Units.gridUnit * 16
        }
    }

    Kirigami.Dialog {
        id: ficha
        title: raiz.h.titulo
        standardButtons: Kirigami.Dialog.Close
        preferredWidth: Kirigami.Units.gridUnit * 34
        preferredHeight: Kirigami.Units.gridUnit * 26
        VistaTexto { texto: raiz.h.resumenMarkdown; markdown: true; nombreAccesible: "Ficha de " + raiz.h.titulo }
    }
}
