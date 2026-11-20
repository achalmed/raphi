// BarraEstudio — la barra de arriba de Raphi Studio: volver al catálogo, la búsqueda rápida de herramientas (Ctrl+F),
// las áreas del catálogo con cuántas herramientas tiene cada una, Simular (F5) y Procesar (Ctrl+Intro) cuando hay una
// herramienta abierta, y la cola con lo que tiene en curso y pendiente (Ctrl+3). Las entradas, desde el taller del
// 2026-11-18, en la zona para soltar de debajo (ZonaSoltar).
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
            QQC2.ToolSeparator { visible: barra.e.vista === "herramienta" }
            BotonAccion { visible: barra.e.vista === "herramienta"; accion: studio.acciones.accion("op.simular") }
            // la acción principal del taller, una sola vez y con el relleno del acento (con Kvantum el «highlighted» de
            // un Button no pinta nada)
            BotonPrincipal {
                readonly property var a: studio.acciones.accion("op.aplicar")
                visible: barra.e.vista === "herramienta" && studio.operaciones.escribe
                text: studio.herramientas.accion || "Procesar"
                icon.name: studio.herramientas.accion === "Descargar" ? "download" : a.icono
                enabled: a.habilitada
                onClicked: a.disparar()
                QQC2.ToolTip.text: (a.habilitada ? a.descripcion : studio.operaciones.motivoNoAplicar) + " (" + a.atajoTexto + ")"
                QQC2.ToolTip.visible: hovered
                QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
            }
            QQC2.ToolSeparator {}
            // la cola: una opción teñida mientras se ve (no el bloque del acento de un botón marcado), con lo pendiente
            OpcionColor {
                icon.name: barra.t.enCurso ? "media-playback-start" : "view-task"
                elegida: barra.e.vista === "cola"
                text: "Cola" + (barra.t.contadores.en_curso + barra.t.contadores.en_cola > 0 ? " · " + (barra.t.contadores.en_curso + barra.t.contadores.en_cola) : "")
                descripcion: barra.t.resumen
                atajo: "Ctrl+3"
                onClicked: barra.e.fijarVista(elegida ? "catalogo" : "cola")
            }
        }
        // las áreas del catálogo: un selector segmentado con la cifra de cada una; si no caben, se desplazan de lado
        Flickable {
            id: areas
            Layout.fillWidth: true
            Layout.preferredHeight: selector.implicitHeight
            visible: barra.e.vista === "catalogo"
            contentWidth: selector.implicitWidth
            contentHeight: selector.implicitHeight
            flickableDirection: Flickable.HorizontalFlick
            boundsBehavior: Flickable.StopAtBounds
            clip: contentWidth > width
            SelectorSegmentado {
                id: selector
                titulo: "Áreas del catálogo"
                compacto: barra.width < Kirigami.Units.gridUnit * 80
                opciones: barra.e.areas.map(a => ({ clave: a.nombre, texto: a.texto, icono: a.icono, contador: barra.h.porArea[a.nombre] || 0,
                                                     descripcion: a.descripcion || "Todas las herramientas y recetas",
                                                     visible: a.nombre === "" || (barra.h.porArea[a.nombre] || 0) > 0 }))
                actual: barra.e.area
                onElegida: (clave) => barra.e.fijarArea(clave)
            }
        }
    }
}
