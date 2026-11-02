// PaginaCatalogo — el catálogo de herramientas como cuadrícula de tarjetas (reingeniería X2): icono, nombre, qué hace,
// área, formatos que acepta y si está lista en esta máquina (o qué le falta). Filtrado por área y por la búsqueda de la
// barra; con entradas, arriba dice cuáles son y puede quedarse con las herramientas que las aceptan. Un clic abre el
// espacio de trabajo de la herramienta.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: pagina
    readonly property var h: studio.herramientas
    readonly property var e: studio.espacio
    readonly property var a: studio.archivos
    spacing: 0

    Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        visible: pagina.a.total > 0
        type: Kirigami.MessageType.Information
        text: "Entradas: " + pagina.a.resumen + (pagina.e.soloAceptan ? ". Se muestran las " + pagina.h.visibles + " herramientas que las aceptan." : ".")
        actions: [
            Kirigami.Action { text: pagina.e.soloAceptan ? "Ver todas" : "Solo las que las aceptan"; icon.name: "view-filter"; onTriggered: pagina.e.fijarSoloAceptan(!pagina.e.soloAceptan) },
            Kirigami.Action { text: "Quitar las entradas"; icon.name: "edit-clear-list"; onTriggered: { pagina.a.vaciar(); pagina.e.fijarSoloAceptan(false) } }
        ]
    }

    GridView {
        id: cuadricula
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        model: pagina.h.modelo
        readonly property int columnas: Math.max(1, Math.floor((width - Kirigami.Units.largeSpacing) / (Kirigami.Units.gridUnit * 17)))
        cellWidth: Math.floor((width - Kirigami.Units.largeSpacing) / columnas)
        cellHeight: Kirigami.Units.gridUnit * 7.5
        leftMargin: Kirigami.Units.largeSpacing / 2
        topMargin: Kirigami.Units.largeSpacing
        bottomMargin: Kirigami.Units.largeSpacing
        keyNavigationEnabled: true
        currentIndex: -1
        Accessible.name: "Catálogo de herramientas"
        QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
        Keys.onReturnPressed: if (currentItem) currentItem.abrir()

        delegate: Item {
            id: celda
            required property var model
            required property int index
            width: cuadricula.cellWidth
            height: cuadricula.cellHeight
            function abrir() { pagina.h.irA(model.ref) }

            Kirigami.AbstractCard {
                anchors.fill: parent
                anchors.margins: Kirigami.Units.smallSpacing
                showClickFeedback: true
                highlighted: cuadricula.currentIndex === celda.index
                onClicked: { cuadricula.currentIndex = celda.index; celda.abrir() }
                Accessible.name: celda.model.titulo + ". " + celda.model.descripcion + ". " + celda.model.estado
                Accessible.role: Accessible.Button
                contentItem: ColumnLayout {
                    spacing: Kirigami.Units.smallSpacing
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Kirigami.Units.largeSpacing
                        Kirigami.Icon {
                            source: celda.model.icono
                            implicitWidth: Kirigami.Units.iconSizes.medium
                            implicitHeight: implicitWidth
                            opacity: celda.model.disponible ? 1 : 0.5
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            Kirigami.Heading { level: 4; text: celda.model.titulo; elide: Text.ElideRight; Layout.fillWidth: true }
                            QQC2.Label { text: celda.model.areaTexto; elide: Text.ElideRight; Layout.fillWidth: true; font: Kirigami.Theme.smallFont; color: Kirigami.Theme.disabledTextColor }
                        }
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: celda.model.descripcion
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                        verticalAlignment: Text.AlignTop
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Kirigami.Units.smallSpacing
                        QQC2.Label {
                            Layout.fillWidth: true
                            text: celda.model.formatos
                            elide: Text.ElideRight
                            font.family: Kirigami.Theme.fixedWidthFont.family
                            font.pointSize: Kirigami.Theme.smallFont.pointSize
                            color: Kirigami.Theme.disabledTextColor
                        }
                        Kirigami.Icon {
                            source: celda.model.disponible ? "data-success" : "data-warning"
                            implicitWidth: Kirigami.Units.iconSizes.small
                            implicitHeight: implicitWidth
                        }
                        QQC2.Label {
                            text: celda.model.disponible ? (celda.model.larga ? "lista · tarda" : "lista") : celda.model.estado
                            font: Kirigami.Theme.smallFont
                            color: celda.model.disponible ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.negativeTextColor
                            elide: Text.ElideRight
                            Layout.maximumWidth: celda.width * 0.45
                        }
                    }
                }
            }
        }

        Kirigami.PlaceholderMessage {
            anchors.centerIn: parent
            width: parent.width - Kirigami.Units.gridUnit * 8
            visible: cuadricula.count === 0
            icon.name: pagina.h.total === 0 ? "view-refresh" : "edit-find"
            text: pagina.h.total === 0 ? (pagina.h.motivoSinFichas ? "El motor no respondió" : "Leyendo las fichas del motor…") : "Ninguna herramienta"
            explanation: pagina.h.total === 0 ? (pagina.h.motivoSinFichas || "F6 las vuelve a leer.") : "Nada cumple «" + pagina.e.textoFiltro + "»."
        }
    }
}
