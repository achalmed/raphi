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
    readonly property int anchoPieza: Kirigami.Units.gridUnit * 15
    contentWidth: availableWidth
    QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff
    Accessible.name: "Paleta de herramientas"

    ColumnLayout {
        width: pagina.availableWidth
        spacing: 0

        Repeater {
            model: pagina.h.paleta
            delegate: ColumnLayout {
                id: grupo
                required property var modelData
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.largeSpacing
                Layout.rightMargin: Kirigami.Units.largeSpacing
                Layout.topMargin: Kirigami.Units.largeSpacing
                spacing: Kirigami.Units.smallSpacing

                // la familia: icono, nombre, cuántas y para qué
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing
                    Kirigami.Icon { source: grupo.modelData.icono; implicitWidth: Kirigami.Units.iconSizes.smallMedium; implicitHeight: implicitWidth }
                    Kirigami.Heading { level: 3; text: grupo.modelData.texto }
                    QQC2.Label { text: grupo.modelData.herramientas.length; color: Kirigami.Theme.disabledTextColor }
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: grupo.modelData.descripcion
                        color: Kirigami.Theme.disabledTextColor
                        font: Kirigami.Theme.smallFont
                        elide: Text.ElideRight
                        leftPadding: Kirigami.Units.largeSpacing
                    }
                }
                Kirigami.Separator { Layout.fillWidth: true }

                // sus herramientas
                GridLayout {
                    Layout.fillWidth: true
                    columns: Math.max(1, Math.floor((pagina.availableWidth - Kirigami.Units.largeSpacing * 2) / pagina.anchoPieza))
                    columnSpacing: 0
                    rowSpacing: 0
                    Repeater {
                        model: grupo.modelData.herramientas
                        delegate: QQC2.ItemDelegate {
                            id: pieza
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredWidth: pagina.anchoPieza
                            // con entradas, la que no sirve para ellas queda tenue (sigue abriéndose)
                            readonly property bool atenuada: pagina.a.total > 0 && !modelData.sirve
                            onClicked: pagina.h.irA(modelData.ref)
                            Accessible.name: modelData.titulo + ". " + modelData.descripcion + ". " + modelData.estado + (modelData.sirve ? ". Sirve para las entradas" : "")
                            Accessible.role: Accessible.Button
                            QQC2.ToolTip.text: modelData.descripcion + "\n" + modelData.areaTexto
                            QQC2.ToolTip.visible: hovered
                            QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                            contentItem: RowLayout {
                                spacing: Kirigami.Units.largeSpacing
                                opacity: pieza.atenuada ? 0.55 : 1
                                Kirigami.Icon {
                                    source: pieza.modelData.icono
                                    implicitWidth: Kirigami.Units.iconSizes.medium
                                    implicitHeight: implicitWidth
                                    opacity: pieza.modelData.disponible ? 1 : 0.5
                                    Layout.alignment: Qt.AlignTop
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 0
                                    QQC2.Label { text: pieza.modelData.titulo; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                                    QQC2.Label {
                                        text: pieza.modelData.descripcion
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                        font: Kirigami.Theme.smallFont
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: Kirigami.Units.smallSpacing
                                        QQC2.Label {
                                            Layout.fillWidth: true
                                            text: pieza.modelData.formatos
                                            elide: Text.ElideRight
                                            font.family: Kirigami.Theme.fixedWidthFont.family
                                            font.pointSize: Kirigami.Theme.smallFont.pointSize
                                            color: Kirigami.Theme.disabledTextColor
                                        }
                                        QQC2.Label {
                                            text: !pieza.modelData.disponible ? pieza.modelData.estado : pieza.modelData.larga ? "tarda" : ""
                                            visible: text !== ""
                                            font: Kirigami.Theme.smallFont
                                            color: !pieza.modelData.disponible ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.disabledTextColor
                                            elide: Text.ElideRight
                                            Layout.maximumWidth: pieza.width * 0.5
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
        Item { Layout.preferredHeight: Kirigami.Units.largeSpacing }
    }
}
