// Archivos — la lista de archivos de entrada del espacio (nombre, tipo, tamaño, carpeta): se sueltan sobre la
// ventana, se añaden con el diálogo y se quitan con Supr; en la vista Trabajos, los archivos del trabajo actual.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: pagina
    readonly property var a: studio.archivos
    readonly property var h: studio.herramientas
    readonly property var t: studio.trabajos
    readonly property bool enTrabajos: studio.espacio.vista === "trabajos"
    spacing: 0
    function quitarSeleccion() {
        if (pagina.enTrabajos) return
        const filas = tabla.seleccion.selectedRows ? tabla.seleccion.selectedRows().map(i => i.row) : []
        if (filas.length) pagina.a.quitarFilas(filas)
        else if (tabla.filaActual >= 0) pagina.a.quitar(tabla.filaActual)
    }
    QQC2.Label {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        visible: !pagina.enTrabajos && pagina.h.hayActual
        text: pagina.h.sinArchivos ? "«" + pagina.h.titulo + "» trabaja sin archivos."
              : (pagina.a.total === 0 ? "Suelta aquí (o en cualquier parte) lo que acepta «" + pagina.h.titulo + "»: " + pagina.h.textoAcepta
                 : (pagina.h.aceptaLosArchivos ? "«" + pagina.h.titulo + "» acepta estos " + pagina.a.total + " archivo(s)."
                                                : "«" + pagina.h.titulo + "» acepta " + pagina.h.textoAcepta + ": quita lo que no sirva."))
        wrapMode: Text.WordWrap
        font: Kirigami.Theme.smallFont
        color: pagina.h.sinArchivos || pagina.a.total === 0 || pagina.h.aceptaLosArchivos ? Kirigami.Theme.disabledTextColor : Kirigami.Theme.neutralTextColor
    }
    TablaDatos {
        id: tabla
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: !pagina.enTrabajos
        modelo: pagina.a.modelo
        claveAjustes: "archivos"
        umbralEstrecho: 0
        mensajeVacio: "Sin archivos: suéltalos sobre la ventana o añádelos (Ctrl+O; Ctrl+Mayús+O, una carpeta)"
        iconoVacio: "document-open"
        columnas: [{ ancho: 0, minimo: 10, conIcono: true }, { ancho: 7, secundaria: true, estrecho: true }, { ancho: 5, alinear: "derecha", secundaria: true },
                   { ancho: 12, secundaria: true, estrecho: true }]
        onFilaActualCambiada: fila => pagina.a.fijarFila(fila)
        onActivada: fila => { pagina.a.fijarFila(fila); studio.acciones.accion("archivo.abrir").disparar() }
        onSuprimir: pagina.quitarSeleccion()
        menuContextual: MenuAcciones {
            acciones: studio.acciones
            conAtajos: false
            elementos: [{ tipo: "accion", nombre: "archivo.abrir" }, { tipo: "accion", nombre: "archivo.mostrar" }, { tipo: "accion", nombre: "archivo.copiar" }, { tipo: "separador" },
                        { tipo: "accion", nombre: "archivo.quitar" }, { tipo: "accion", nombre: "archivo.vaciar" }]
        }
    }
    RowLayout {
        visible: !pagina.enTrabajos
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing
        BotonAccion { accion: studio.acciones.accion("archivo.anadir") }
        BotonAccion { accion: studio.acciones.accion("archivo.anadir_carpeta") }
        Item { Layout.fillWidth: true }
        BotonAccion { accion: studio.acciones.accion("archivo.quitar"); conTexto: false }
        BotonAccion { accion: studio.acciones.accion("archivo.vaciar"); conTexto: false }
    }
    QQC2.ScrollView {
        visible: pagina.enTrabajos
        Layout.fillWidth: true
        Layout.fillHeight: true
        ListView {
            model: pagina.t.archivos
            delegate: QQC2.ItemDelegate {
                required property string modelData
                width: ListView.view.width
                text: modelData
                icon.name: "text-x-generic"
                onClicked: studio.espacio.mostrarEnCarpeta(modelData)
                Accessible.name: modelData
            }
            Kirigami.PlaceholderMessage { anchors.centerIn: parent; width: parent.width - Kirigami.Units.gridUnit * 4; visible: parent.count === 0; text: pagina.t.hayActual ? "El trabajo no tenía archivos de entrada" : "Ningún trabajo"; icon.name: "view-task" }
        }
    }
}
