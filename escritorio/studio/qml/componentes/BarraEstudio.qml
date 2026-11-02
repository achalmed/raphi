// BarraEstudio — la barra de arriba de Raphi Studio: volver al catálogo, la búsqueda rápida de herramientas (Ctrl+F),
// las áreas del catálogo con cuántas herramientas tiene cada una, las entradas, Simular (F5) y Procesar (Ctrl+Intro)
// cuando hay una herramienta abierta, y la cola con lo que tiene en curso y pendiente (Ctrl+3).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.ToolBar {
    id: barra
    readonly property var e: studio.espacio
    readonly property var h: studio.herramientas
    readonly property var t: studio.trabajos
    position: QQC2.ToolBar.Header
    Accessible.name: "Barra del estudio"

    function enfocarBusqueda() { busqueda.forceActiveFocus(); busqueda.selectAll() }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing
        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            QQC2.ToolButton {
                visible: barra.e.vista !== "catalogo"
                icon.name: "go-previous"
                text: "Catálogo"
                onClicked: barra.e.fijarVista("catalogo")
                QQC2.ToolTip.text: "Volver al catálogo (Alt+←)"
                QQC2.ToolTip.visible: hovered
            }
            Kirigami.SearchField {
                id: busqueda
                Layout.preferredWidth: Kirigami.Units.gridUnit * 16
                placeholderText: "Buscar una herramienta (Ctrl+F)"
                text: barra.e.busqueda
                onTextChanged: barra.e.fijarBusqueda(text)
                Keys.onEscapePressed: { text = ""; focus = false }
                Accessible.name: "Buscar una herramienta"
            }
            Item { Layout.fillWidth: true }
            QQC2.ToolButton {
                icon.name: "document-open"
                text: studio.archivos.total > 0 ? studio.archivos.total + " entrada" + (studio.archivos.total === 1 ? "" : "s") : "Añadir archivos"
                onClicked: studio.acciones.accion("archivo.anadir").disparar()
                QQC2.ToolTip.text: studio.archivos.total > 0 ? studio.archivos.resumen + " (Ctrl+O añade; se sueltan desde Dolphin)" : "Archivos de entrada (Ctrl+O, o suéltalos desde Dolphin)"
                QQC2.ToolTip.visible: hovered
            }
            QQC2.ToolSeparator { visible: barra.e.vista === "herramienta" }
            BotonAccion { visible: barra.e.vista === "herramienta"; accion: studio.acciones.accion("op.simular") }
            QQC2.Button {
                readonly property var a: studio.acciones.accion("op.aplicar")
                visible: barra.e.vista === "herramienta"
                highlighted: true
                text: "Procesar"
                icon.name: a.icono
                enabled: a.habilitada
                onClicked: a.disparar()
                QQC2.ToolTip.text: (a.habilitada ? a.descripcion : studio.operaciones.motivoNoAplicar) + " (" + a.atajoTexto + ")"
                QQC2.ToolTip.visible: hovered
            }
            QQC2.ToolSeparator {}
            QQC2.ToolButton {
                icon.name: barra.t.enCurso ? "media-playback-start" : "view-task"
                checkable: true
                checked: barra.e.vista === "cola"
                text: "Cola" + (barra.t.contadores.en_curso + barra.t.contadores.en_cola > 0 ? " · " + (barra.t.contadores.en_curso + barra.t.contadores.en_cola) : "")
                onClicked: barra.e.fijarVista(checked ? "cola" : "catalogo")
                QQC2.ToolTip.text: barra.t.resumen + " (Ctrl+3)"
                QQC2.ToolTip.visible: hovered
            }
        }
        // las áreas del catálogo
        Flow {
            Layout.fillWidth: true
            visible: barra.e.vista === "catalogo"
            spacing: Kirigami.Units.smallSpacing
            Repeater {
                model: barra.e.areas
                delegate: QQC2.ToolButton {
                    required property var modelData
                    readonly property int cuantas: barra.h.porArea[modelData.nombre] || 0
                    visible: modelData.nombre === "" || cuantas > 0
                    checkable: true
                    checked: barra.e.area === modelData.nombre
                    icon.name: modelData.icono
                    text: modelData.texto + "  " + cuantas
                    onClicked: barra.e.fijarArea(modelData.nombre)
                    QQC2.ToolTip.text: modelData.descripcion || "Todas las herramientas y recetas"
                    QQC2.ToolTip.visible: hovered && modelData.nombre !== ""
                    QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                    Accessible.name: modelData.texto + ": " + cuantas + " herramientas"
                }
            }
        }
    }
}
