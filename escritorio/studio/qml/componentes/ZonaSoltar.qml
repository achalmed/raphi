// ZonaSoltar — arriba del taller (rediseño aprobado del 2026-11-18): la zona para soltar archivos y carpetas desde
// Dolphin, con lo que ya entró en fila (miniatura o icono, nombre, tipo y tamaño, quitar). Elegir una entrada la muestra
// en el monitor de la herramienta; «Solo las que sirven» deja en la paleta las herramientas que la aceptan. Soltar se
// atiende en toda la ventana (Main.qml); aquí solo se señala. Los colores, del tema: la zona se marca con el resaltado
// mientras se arrastra encima.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.Control {
    id: zona
    readonly property var a: studio.archivos
    readonly property var h: studio.herramientas
    readonly property var e: studio.espacio
    property bool arrastrando: false                  // lo pone la ventana mientras algo se arrastra encima
    signal elegida(int indice)

    padding: Kirigami.Units.smallSpacing
    leftPadding: Kirigami.Units.largeSpacing
    rightPadding: Kirigami.Units.largeSpacing
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    Accessible.name: "Zona para soltar archivos y carpetas"
    Accessible.description: a.total > 0 ? a.resumen : "Vacía"

    background: Rectangle {
        color: zona.arrastrando ? Kirigami.Theme.highlightColor : Kirigami.Theme.alternateBackgroundColor
        opacity: zona.arrastrando ? 0.25 : 1
        border.width: zona.arrastrando ? 2 : 0
        border.color: Kirigami.Theme.highlightColor
    }

    contentItem: RowLayout {
        spacing: Kirigami.Units.largeSpacing

        // la invitación: qué se suelta aquí y para qué herramienta
        RowLayout {
            Layout.maximumWidth: zona.a.total > 0 ? Kirigami.Units.gridUnit * 15 : -1
            Layout.fillWidth: zona.a.total === 0
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon {
                source: zona.arrastrando ? "document-import" : "folder-download"
                implicitWidth: Kirigami.Units.iconSizes.medium
                implicitHeight: implicitWidth
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                QQC2.Label {
                    Layout.fillWidth: true
                    text: zona.arrastrando ? "Suéltalos aquí" : zona.a.total > 0 ? "Entradas · " + zona.a.total : "Suelta aquí archivos y carpetas"
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    text: zona.e.vista === "herramienta" && zona.h.hayActual
                          ? (zona.h.sinArchivos ? zona.h.titulo + " trabaja sin archivos" : zona.h.titulo + " acepta " + zona.h.textoAcepta)
                          : zona.a.total > 0 ? "Más desde Dolphin, o con Ctrl+O" : "Desde Dolphin, o con «Añadir» (Ctrl+O; una carpeta, Ctrl+Mayús+O)"
                    font: Kirigami.Theme.smallFont
                    color: Kirigami.Theme.disabledTextColor
                    elide: Text.ElideRight
                }
            }
        }

        // lo que ya entró
        ListView {
            id: fila
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium + Kirigami.Units.smallSpacing * 4
            visible: zona.a.total > 0
            orientation: ListView.Horizontal
            spacing: Kirigami.Units.smallSpacing
            clip: true
            model: zona.a.rutas
            currentIndex: zona.a.fila
            Accessible.name: "Entradas"
            QQC2.ScrollBar.horizontal: QQC2.ScrollBar { policy: QQC2.ScrollBar.AsNeeded }
            delegate: QQC2.ItemDelegate {
                id: entrada
                required property var modelData
                required property int index
                readonly property var f: zona.a.modelo.fila(index)
                readonly property bool esImagen: /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(String(modelData))
                width: Kirigami.Units.gridUnit * 12
                height: fila.height
                highlighted: ListView.isCurrentItem
                onClicked: zona.elegida(index)
                Accessible.name: (f.nombre || "") + ", " + (f.tipo || "") + ", " + (f.tamano || "")
                QQC2.ToolTip.text: String(modelData)
                QQC2.ToolTip.visible: hovered
                QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                contentItem: RowLayout {
                    spacing: Kirigami.Units.smallSpacing
                    Item {
                        implicitWidth: Kirigami.Units.iconSizes.medium
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
                        QQC2.Label { text: entrada.f.nombre || ""; elide: Text.ElideMiddle; Layout.fillWidth: true; color: entrada.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor }
                        QQC2.Label {
                            text: (entrada.f.tipo || "") + " · " + (entrada.f.tamano || "")
                            font: Kirigami.Theme.smallFont
                            color: entrada.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                    QQC2.ToolButton {
                        icon.name: "list-remove"
                        text: "Quitar"
                        display: QQC2.AbstractButton.IconOnly
                        onClicked: zona.a.quitar(entrada.index)
                        Accessible.name: "Quitar " + (entrada.f.nombre || "")
                        QQC2.ToolTip.text: "Quitar de las entradas"
                        QQC2.ToolTip.visible: hovered
                    }
                }
            }
        }

        // añadir, filtrar y vaciar (las acciones de siempre, del registro)
        RowLayout {
            spacing: 0
            BotonAccion { accion: studio.acciones.accion("archivo.anadir"); conTexto: zona.a.total === 0 }
            BotonAccion { accion: studio.acciones.accion("archivo.anadir_carpeta"); conTexto: false }
            QQC2.ToolSeparator { visible: zona.a.total > 0 }
            BotonAccion {
                accion: studio.acciones.accion("ver.aceptan")
                visible: zona.a.total > 0 && zona.e.vista === "catalogo"
                text: "Solo las que sirven"
            }
            BotonAccion { accion: studio.acciones.accion("archivo.vaciar"); conTexto: false; visible: zona.a.total > 0 }
        }
    }
}
