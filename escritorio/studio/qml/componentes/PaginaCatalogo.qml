// PaginaCatalogo — la paleta de herramientas del taller (rediseño aprobado del 2026-11-18; antes, la cuadrícula de
// tarjetas de la reingeniería X2): las herramientas agrupadas por familia, en el orden del taller (PDF, imágenes, audio
// y video, documentos; después archivos y recetas), cada una con su icono, qué hace, los formatos que acepta y si está
// lista en esta máquina (o qué le falta). Con entradas, la que no sirve para ellas queda tenue. Los filtros de siempre (área,
// búsqueda, «solo las que sirven») deciden qué entra; el agrupado lo arma Python (`herramientas.paleta`). Un clic abre
// el espacio de trabajo de la herramienta.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.ScrollView {
    id: pagina
    readonly property var h: studio.herramientas
    readonly property var e: studio.espacio
    readonly property var a: studio.archivos
    readonly property int anchoPieza: Kirigami.Units.gridUnit * 16
    contentWidth: availableWidth
    QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff
    Accessible.name: "Paleta de herramientas"

    PaletaCategorica { id: paleta }

    // la pastilla de un icono: un círculo teñido del color de su familia con el icono de la acción, monocromo
    component Pastilla: Rectangle {
        property string icono: ""
        property color tono: Kirigami.Theme.highlightColor
        property real lado: Kirigami.Units.gridUnit * 2.2
        implicitWidth: lado
        implicitHeight: lado
        radius: lado / 2
        color: Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, tono, 0.16)
        border.width: 1
        border.color: Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, tono, 0.38)
        Kirigami.Icon {
            anchors.centerIn: parent
            source: parent.icono
            fallback: "system-run"
            isMask: true
            color: Kirigami.ColorUtils.linearInterpolation(parent.tono, Kirigami.Theme.textColor, 0.35)
            implicitWidth: Kirigami.Units.iconSizes.smallMedium
            implicitHeight: implicitWidth
        }
    }

    ColumnLayout {
        width: pagina.availableWidth
        spacing: 0

        Repeater {
            model: pagina.h.paleta
            delegate: ColumnLayout {
                id: grupo
                required property var modelData
                readonly property color tono: paleta.rol(modelData.rol || "gris")
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.largeSpacing * 2
                Layout.rightMargin: Kirigami.Units.largeSpacing * 2
                Layout.topMargin: Kirigami.Units.largeSpacing * 2
                spacing: Kirigami.Units.largeSpacing

                // la familia: su pastilla, su nombre, cuántas y para qué
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.largeSpacing
                    Pastilla { icono: grupo.modelData.icono; tono: grupo.tono; lado: Kirigami.Units.gridUnit * 1.6 }
                    Kirigami.Heading { level: 2; text: grupo.modelData.texto }
                    EtiquetaNivel { text: grupo.modelData.herramientas.length; Layout.alignment: Qt.AlignVCenter }
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: grupo.modelData.descripcion
                        color: Kirigami.Theme.disabledTextColor
                        elide: Text.ElideRight
                        leftPadding: Kirigami.Units.smallSpacing
                    }
                }

                // sus herramientas, en tarjetas que responden al ratón
                GridLayout {
                    Layout.fillWidth: true
                    columns: Math.max(1, Math.floor((pagina.availableWidth - Kirigami.Units.largeSpacing * 4) / pagina.anchoPieza))
                    columnSpacing: Kirigami.Units.smallSpacing
                    rowSpacing: Kirigami.Units.smallSpacing
                    Repeater {
                        model: grupo.modelData.herramientas
                        delegate: QQC2.ItemDelegate {
                            id: pieza
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredWidth: pagina.anchoPieza
                            Layout.fillHeight: true
                            // con entradas, la que no sirve para ellas queda tenue (sigue abriéndose)
                            readonly property bool atenuada: pagina.a.total > 0 && !modelData.sirve
                            hoverEnabled: true
                            padding: Kirigami.Units.largeSpacing
                            onClicked: pagina.h.irA(modelData.ref)
                            Accessible.name: modelData.titulo + ". " + modelData.descripcion + ". " + modelData.estado + (modelData.sirve ? ". Sirve para las entradas" : "")
                            Accessible.role: Accessible.Button
                            QQC2.ToolTip.text: modelData.descripcion + "\n" + modelData.areaTexto
                            QQC2.ToolTip.visible: hovered
                            QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                            // sin los márgenes que el estilo de KDE deja alrededor del fondo: el fondo es la fila entera y
                            // el contenido respeta su relleno (con ellos, la marca de lo elegido caía encima del texto)
                            leftInset: 0; rightInset: 0; topInset: 0; bottomInset: 0
                            topPadding: Kirigami.Units.smallSpacing * 2; bottomPadding: Kirigami.Units.smallSpacing * 2
                            background: Rectangle {
                                radius: Kirigami.Units.cornerRadius * 2
                                color: pieza.pressed ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, grupo.tono, 0.14)
                                     : pieza.hovered ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, grupo.tono, 0.08)
                                     : "transparent"
                                border.width: 1
                                border.color: pieza.visualFocus ? Kirigami.Theme.focusColor
                                            : pieza.hovered ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, grupo.tono, 0.40)
                                            : Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.08)
                                Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
                            }
                            contentItem: RowLayout {
                                spacing: Kirigami.Units.largeSpacing
                                opacity: pieza.atenuada ? 0.5 : 1
                                Pastilla {
                                    icono: pieza.modelData.icono
                                    tono: grupo.tono
                                    opacity: pieza.modelData.disponible ? 1 : 0.5
                                    Layout.alignment: Qt.AlignTop
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.alignment: Qt.AlignTop
                                    spacing: Kirigami.Units.smallSpacing / 2
                                    QQC2.Label { text: pieza.modelData.titulo; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                                    QQC2.Label {
                                        text: pieza.modelData.descripcion
                                        wrapMode: Text.WordWrap
                                        maximumLineCount: 2
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                        font.pointSize: Kirigami.Theme.smallFont.pointSize
                                        opacity: 0.8
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Layout.topMargin: Kirigami.Units.smallSpacing / 2
                                        spacing: Kirigami.Units.smallSpacing
                                        QQC2.Label {
                                            Layout.fillWidth: true
                                            text: pieza.modelData.formatos
                                            elide: Text.ElideRight
                                            font.pointSize: Kirigami.Theme.smallFont.pointSize
                                            color: Kirigami.Theme.disabledTextColor
                                        }
                                        // lo que le falta a la máquina, o que tarda: etiquetas del color de su nivel
                                        EtiquetaNivel {
                                            visible: !pieza.modelData.disponible || pieza.modelData.larga
                                            text: !pieza.modelData.disponible ? pieza.modelData.estado : "tarda"
                                            nivel: !pieza.modelData.disponible ? "negativo" : "neutro"
                                            icono: !pieza.modelData.disponible ? "dialog-warning" : "chronometer"
                                            elide: Text.ElideRight
                                            Layout.maximumWidth: pieza.width * 0.55
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        Kirigami.PlaceholderMessage {
            Layout.fillWidth: true
            Layout.preferredHeight: pagina.availableHeight
            Layout.leftMargin: Kirigami.Units.gridUnit * 4
            Layout.rightMargin: Kirigami.Units.gridUnit * 4
            visible: pagina.h.paleta.length === 0
            icon.name: pagina.h.total === 0 ? "view-refresh" : "edit-find"
            text: pagina.h.total === 0 ? (pagina.h.motivoSinFichas ? "El motor no respondió" : "Leyendo las fichas del motor…") : "Ninguna herramienta"
            explanation: pagina.h.total === 0 ? (pagina.h.motivoSinFichas || "F6 las vuelve a leer.") : "Nada cumple «" + pagina.e.textoFiltro + "»."
        }
        Item { Layout.preferredHeight: Kirigami.Units.largeSpacing * 2 }
    }
}
