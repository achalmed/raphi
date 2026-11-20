// ZonaSoltar — arriba del taller (rediseño aprobado del 2026-11-18): la zona para soltar archivos y carpetas desde
// Dolphin, con lo que ya entró en fila (miniatura o icono, nombre, tipo y tamaño, quitar). Elegir una entrada la muestra
// en el monitor de la herramienta; «Solo las que sirven» deja en la paleta las herramientas que la aceptan. Soltar se
// atiende en toda la ventana (Main.qml); aquí solo se señala. Los colores, del tema: la zona se marca con el resaltado
// mientras se arrastra encima.
import QtQuick
import QtQuick.Shapes
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
    readonly property bool oscuro: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark

    padding: Kirigami.Units.smallSpacing * 2
    leftPadding: Kirigami.Units.largeSpacing * 2
    rightPadding: Kirigami.Units.largeSpacing * 2
    Accessible.name: "Zona para soltar archivos y carpetas"
    Accessible.description: a.total > 0 ? a.resumen : "Vacía"

    // el pozo para soltar: un recuadro redondeado de borde punteado, del tema; mientras se arrastra encima, teñido del
    // acento y con el borde lleno
    background: Item {
        Rectangle {
            id: pozo
            anchors.fill: parent
            anchors.leftMargin: Kirigami.Units.largeSpacing
            anchors.rightMargin: Kirigami.Units.largeSpacing
            anchors.topMargin: Kirigami.Units.smallSpacing
            anchors.bottomMargin: Kirigami.Units.smallSpacing
            radius: Kirigami.Units.cornerRadius * 2
            color: zona.arrastrando ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, 0.16)
                 : Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, zona.oscuro ? 0.05 : 0.035)
            Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
        }
        Shape {
            anchors.fill: pozo
            anchors.leftMargin: pozo.anchors.leftMargin
            anchors.rightMargin: pozo.anchors.rightMargin
            anchors.topMargin: pozo.anchors.topMargin
            anchors.bottomMargin: pozo.anchors.bottomMargin
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeWidth: zona.arrastrando ? 2 : 1
                strokeColor: zona.arrastrando ? Kirigami.Theme.highlightColor
                           : Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.32)
                strokeStyle: zona.arrastrando ? ShapePath.SolidLine : ShapePath.DashLine
                dashPattern: [4, 3]
                fillColor: "transparent"
                PathRectangle { x: 0.5; y: 0.5; width: pozo.width - 1; height: pozo.height - 1; radius: pozo.radius }
            }
        }
    }

    contentItem: RowLayout {
        spacing: Kirigami.Units.largeSpacing

        // la invitación: qué se suelta aquí y para qué herramienta
        RowLayout {
            Layout.maximumWidth: zona.a.total > 0 ? Kirigami.Units.gridUnit * 15 : -1
            Layout.fillWidth: zona.a.total === 0
            Layout.leftMargin: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.largeSpacing
            Rectangle {
                implicitWidth: Kirigami.Units.gridUnit * 2
                implicitHeight: implicitWidth
                radius: width / 2
                color: Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, zona.arrastrando ? 0.35 : 0.16)
                Kirigami.Icon {
                    anchors.centerIn: parent
                    source: "document-import"
                    isMask: true
                    color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.highlightColor, Kirigami.Theme.textColor, 0.3)
                    implicitWidth: Kirigami.Units.iconSizes.smallMedium
                    implicitHeight: implicitWidth
                }
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
                    font.pointSize: Kirigami.Theme.smallFont.pointSize
                    color: Kirigami.Theme.disabledTextColor
                    elide: Text.ElideRight
                }
            }
        }

        // lo que ya entró: cada entrada como una ficha con su miniatura o icono, nombre, tipo y tamaño, y su X
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
                readonly property bool elegida: ListView.isCurrentItem
                width: Kirigami.Units.gridUnit * 12
                height: fila.height
                hoverEnabled: true
                onClicked: zona.elegida(index)
                Accessible.name: (f.nombre || "") + ", " + (f.tipo || "") + ", " + (f.tamano || "") + (elegida ? ", elegida" : "")
                QQC2.ToolTip.text: String(modelData)
                QQC2.ToolTip.visible: hovered
                QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                // sin los márgenes que el estilo de KDE deja alrededor del fondo: el fondo es la fila entera y
                // el contenido respeta su relleno (con ellos, la marca de lo elegido caía encima del texto)
                leftInset: 0; rightInset: 0; topInset: 0; bottomInset: 0
                topPadding: Kirigami.Units.smallSpacing * 2; bottomPadding: Kirigami.Units.smallSpacing * 2
                background: Rectangle {
                    radius: Kirigami.Units.cornerRadius * 2
                    color: entrada.elegida ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, entrada.hovered ? 0.30 : 0.22)
                         : entrada.hovered ? Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.08)
                         : Kirigami.Theme.backgroundColor
                    border.width: 1
                    border.color: entrada.elegida ? Kirigami.Theme.highlightColor
                                : Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.14)
                }
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
                        QQC2.Label { text: entrada.f.nombre || ""; elide: Text.ElideMiddle; Layout.fillWidth: true; font.weight: entrada.elegida ? Font.DemiBold : Font.Normal }
                        QQC2.Label {
                            text: (entrada.f.tipo || "") + " · " + (entrada.f.tamano || "")
                            font.pointSize: Kirigami.Theme.smallFont.pointSize
                            color: Kirigami.Theme.disabledTextColor
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                    BotonCierre {
                        text: "Quitar " + (entrada.f.nombre || "") + " de las entradas"
                        onClicked: zona.a.quitar(entrada.index)
                    }
                }
            }
        }

        // añadir, filtrar y vaciar (las acciones de siempre, del registro)
        RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Layout.rightMargin: Kirigami.Units.largeSpacing
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
