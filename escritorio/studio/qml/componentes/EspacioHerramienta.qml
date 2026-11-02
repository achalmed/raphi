// EspacioHerramienta — el espacio de trabajo de la herramienta elegida (reingeniería X3), al estilo de HandBrake:
// arriba, qué es (icono, nombre, áreas, formatos, qué le falta, su ficha); a la izquierda las entradas (miniaturas,
// añadir con el diálogo de KDE, soltar desde Dolphin, quitar); en el centro el monitor con la vista previa de la entrada
// elegida o del resultado; a la derecha las opciones generadas de su ficha y dónde dejar la salida; abajo, el último
// trabajo de esta herramienta con su progreso. Simular (F5) y Procesar (Ctrl+Intro) están en la barra de arriba.
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

    // ------------------------------------------------------------------ entradas · monitor · opciones
    QQC2.SplitView {
        visible: raiz.h.hayActual
        Layout.fillWidth: true
        Layout.fillHeight: true
        orientation: Qt.Horizontal

        ColumnLayout {                                                     // entradas
            QQC2.SplitView.preferredWidth: Kirigami.Units.gridUnit * 15
            QQC2.SplitView.minimumWidth: Kirigami.Units.gridUnit * 10
            spacing: 0
            RowLayout {
                Layout.fillWidth: true
                Layout.margins: Kirigami.Units.smallSpacing
                Kirigami.Heading { level: 4; text: raiz.h.sinArchivos ? "Sin entradas" : "Entradas · " + raiz.a.total; Layout.fillWidth: true }
                BotonAccion { accion: studio.acciones.accion("archivo.anadir"); conTexto: false; visible: !raiz.h.sinArchivos }
                BotonAccion { accion: studio.acciones.accion("archivo.anadir_carpeta"); conTexto: false; visible: !raiz.h.sinArchivos }
                BotonAccion { accion: studio.acciones.accion("archivo.vaciar"); conTexto: false; visible: !raiz.h.sinArchivos }
            }
            ListView {
                id: entradas
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                visible: !raiz.h.sinArchivos
                model: raiz.a.rutas
                currentIndex: raiz.a.fila
                Accessible.name: "Entradas"
                QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
                delegate: QQC2.ItemDelegate {
                    id: entrada
                    required property var modelData
                    required property int index
                    readonly property var f: raiz.a.modelo.fila(index)
                    readonly property bool esImagen: /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(String(modelData))
                    width: entradas.width
                    highlighted: ListView.isCurrentItem
                    onClicked: raiz.verEntrada(index)
                    Accessible.name: f.nombre || ""
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.smallSpacing
                        Item {
                            implicitWidth: Kirigami.Units.iconSizes.large
                            implicitHeight: implicitWidth
                            Image {
                                anchors.fill: parent
                                visible: entrada.esImagen
                                source: entrada.esImagen ? "file://" + entrada.modelData : ""
                                sourceSize.width: width * 2
                                fillMode: Image.PreserveAspectFit
                                asynchronous: true
                            }
                            Kirigami.Icon { anchors.fill: parent; visible: !entrada.esImagen; source: entrada.f.icono ? entrada.f.icono.nombre : "text-x-generic" }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            QQC2.Label { text: entrada.f.nombre || ""; elide: Text.ElideMiddle; Layout.fillWidth: true }
                            QQC2.Label { text: (entrada.f.tipo || "") + " · " + (entrada.f.tamano || ""); font: Kirigami.Theme.smallFont; color: Kirigami.Theme.disabledTextColor; elide: Text.ElideRight; Layout.fillWidth: true }
                        }
                        QQC2.ToolButton { icon.name: "list-remove"; text: "Quitar"; display: QQC2.AbstractButton.IconOnly; onClicked: raiz.a.quitar(entrada.index); Accessible.name: "Quitar " + (entrada.f.nombre || "") }
                    }
                }
                Kirigami.PlaceholderMessage {
                    anchors.centerIn: parent
                    width: parent.width - Kirigami.Units.gridUnit * 2
                    visible: entradas.count === 0
                    icon.name: "document-open"
                    text: "Suelta aquí archivos"
                    explanation: "Desde Dolphin, o con «Añadir archivos» (Ctrl+O). Acepta " + raiz.h.textoAcepta + "."
                    helpfulAction: Kirigami.Action { text: "Añadir archivos…"; icon.name: "document-open"; onTriggered: studio.acciones.accion("archivo.anadir").disparar() }
                }
            }
            Kirigami.PlaceholderMessage {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: raiz.h.sinArchivos
                icon.name: raiz.h.icono
                text: "Trabaja sin archivos"
                explanation: "Lo que necesita (una dirección, una carpeta) está en sus opciones."
            }
        }

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
                vacio: raiz.monitor === "entrada" ? "Elige una entrada a la izquierda para verla aquí" : "Procesa (Ctrl+Intro) para ver el resultado"
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

    // ------------------------------------------------------------------ el último trabajo de esta herramienta
    Kirigami.Separator { Layout.fillWidth: true; visible: raiz.h.hayActual && raiz.t.hayActual && raiz.t.ref === raiz.h.ref }
    RowLayout {
        visible: raiz.h.hayActual && raiz.t.hayActual && raiz.t.ref === raiz.h.ref
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.largeSpacing
        Kirigami.Icon { source: raiz.t.estado === "en_curso" ? "media-playback-start" : raiz.t.estado === "hecho" ? "data-success" : raiz.t.estado === "en_cola" ? "chronometer" : "data-error"; implicitWidth: Kirigami.Units.iconSizes.small; implicitHeight: implicitWidth }
        QQC2.Label { text: raiz.t.textoEstado + (raiz.t.simulado ? " (simulación)" : "") + (raiz.t.mensaje ? " · " + raiz.t.mensaje : ""); elide: Text.ElideRight; Layout.fillWidth: true }
        QQC2.ProgressBar { visible: raiz.t.estado === "en_curso"; from: 0; to: 100; value: raiz.t.progreso; Layout.preferredWidth: Kirigami.Units.gridUnit * 10 }
        QQC2.Label { text: raiz.t.duracion; color: Kirigami.Theme.disabledTextColor }
        BotonAccion { accion: studio.acciones.accion("op.cancelar"); conTexto: false; visible: raiz.t.estado === "en_curso" }
        QQC2.Button { text: "En la cola"; icon.name: "view-task"; flat: true; onClicked: raiz.t.irA(raiz.t.id) }
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
