// Main.qml — Raphi Studio (reingeniería del 2026-11-02, docs/reingenieria.md): un estudio multimedia sobre
// GuiComun.VentanaBase (sin navegación lateral, tabla ni panel de detalles impuestos). Arriba, la barra del estudio:
// volver, buscar herramientas, las áreas del catálogo, Simular y Procesar, la cola con su contador. En el centro, una de
// tres vistas: el Catálogo (cuadrícula de herramientas), la Herramienta (entradas · vista previa · opciones) y la Cola
// (trabajos con su progreso, su resultado, sus salidas y repetir). Abajo, la barra de estado con el trabajo en curso.
// Soltar archivos desde Dolphin en cualquier parte los añade a las entradas. Ninguna llamada al motor ni al disco
// aquí: todo lo hacen los controladores de Python (studio.*).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun
import "componentes"

VentanaBase {
    id: ventana

    readonly property var espacio: studio.espacio
    readonly property var registro: studio.acciones
    readonly property var herramientas: studio.herramientas
    readonly property var archivos: studio.archivos
    readonly property var trabajos: studio.trabajos
    readonly property var ops: studio.operaciones
    readonly property string vista: espacio.vista

    title: (vista === "cola" ? "Cola" : vista === "herramienta" && herramientas.hayActual ? herramientas.titulo : espacio.textoArea) + " — Raphi Studio"
    acciones: registro
    tareas: studio.tareas
    consola: studio.consola
    descripcion: descripcionStudio
    autor: "Edison Achalma (@achalmed)"
    claveAjustes: "ventana-3"
    width: 1360
    height: 860

    function accion(nombre) { return registro.accion(nombre) }

    Connections {
        target: studio.interfaz
        function onPedir(nombre, datos) {
            switch (nombre) {
            case "buscar": barra.enfocarBusqueda(); break
            case "elegir_archivos": selectorArchivos.abrir(archivos.carpetaComun); break
            case "elegir_carpeta": selectorCarpeta.abrir(archivos.carpetaComun); break
            case "quitar_archivos": if (vistaHerramienta.quitarSeleccion) vistaHerramienta.quitarSeleccion(); else archivos.vaciar(); break
            case "venv": dialogoVenv.open(); break
            case "dolphin": dialogoDolphin.open(); break
            case "vigilar": dialogoVigilar.open(); break
            case "faltan": dialogoFaltan.open(); break
            case "salida": dialogoSalida.open(); break
            case "paleta": ventana.paleta.abrir(datos.texto || ""); break
            case "aviso": ventana.mensajes.mostrar(datos.texto, datos.tipo || "informacion"); break
            case "activar": ventana.show(); ventana.raise(); ventana.requestActivate(); break
            }
        }
    }
    Connections { target: espacio; function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) } }
    Connections { target: archivos; function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) } }
    Connections { target: herramientas; function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) } }
    Connections { target: trabajos; function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) } }
    Connections { target: ops; function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) } }

    // ------------------------------------------------------------------ la barra del estudio
    header: BarraEstudio { id: barra }

    // ------------------------------------------------------------------ las tres vistas
    StackLayout {
        anchors.fill: parent
        currentIndex: espacio.indiceVista
        PaginaCatalogo { id: vistaCatalogo }
        EspacioHerramienta { id: vistaHerramienta }
        PaginaCola { id: vistaCola }
    }

    // soltar archivos desde Dolphin en cualquier parte
    DropArea {
        anchors.fill: parent
        z: 100
        keys: ["text/uri-list"]
        onDropped: drop => {
            if (!drop.hasUrls) return
            studio.archivos.recibir(drop.urls.map(u => String(u)))
            drop.accept(Qt.CopyAction)
        }
        Rectangle {
            anchors.fill: parent
            visible: parent.containsDrag
            color: Kirigami.Theme.highlightColor
            opacity: 0.12
            border.color: Kirigami.Theme.highlightColor
            border.width: 2
        }
    }

    footer: BarraEstado {
        resumen: espacio.resumen
        contexto: espacio.contexto
        tareas: studio.tareas
        onProgresoPulsado: espacio.fijarVista("cola")
    }

    // ------------------------------------------------------------------ diálogos (los de archivos y carpetas: los de KDE)
    ElegirArchivos {
        id: selectorArchivos
        titulo: "Añadir archivos de entrada"
        multiple: true
        filtros: herramientas.hayActual && herramientas.extensionesFiltro !== "" ? ["Lo que acepta " + herramientas.titulo + " (" + herramientas.extensionesFiltro + ")"] : []
        onElegidos: rutas => archivos.recibir(rutas)
    }
    ElegirCarpeta {
        id: selectorCarpeta
        titulo: "Añadir una carpeta de entrada"
        onElegida: ruta => archivos.recibir([ruta])
    }
    Kirigami.PromptDialog {
        id: dialogoVenv
        title: "El entorno del motor"
        subtitle: (studio.ajustes.hayVenv ? "El motor corre como proceso con " + studio.ajustes.interpreteMotor + " (el .venv del repo: pikepdf, PyMuPDF, Pillow, pyhanko…); la ventana, con el Python del sistema."
                                           : "No existe el .venv del repo: las herramientas que necesitan pikepdf, PyMuPDF o Pillow fallarán.")
                  + "\n\nPara crearlo (sin sudo ni apt):\n" + studio.ajustes.ordenVenv
        standardButtons: Kirigami.Dialog.Close
        customFooterActions: [Kirigami.Action { text: "Copiar la orden"; icon.name: "edit-copy"; onTriggered: { espacio.copiar(studio.ajustes.ordenVenv); dialogoVenv.close() } }]
    }
    Kirigami.PromptDialog {
        id: dialogoDolphin
        title: "Menús de Dolphin"
        subtitle: (ops.dolphinInstalado ? "Están instalados: clic derecho sobre un archivo → Raphi → la herramienta, sin abrir la ventana."
                                        : "No están instalados. Añaden «Raphi ▸ Abrir en Raphi · Comprimir PDF · PDF a Word · A JPG · A PDF · Quitar metadatos…» al clic derecho de Dolphin.")
                  + "\n\nSe escriben en la configuración de KDE de tu usuario (kio/servicemenus); quitarlos borra solo los de Raphi."
        standardButtons: Kirigami.Dialog.Cancel
        customFooterActions: [Kirigami.Action { text: ops.dolphinInstalado ? "Quitar los menús" : "Instalar los menús"; icon.name: ops.dolphinInstalado ? "list-remove" : "list-add"; onTriggered: { ops.instalarDolphin(!ops.dolphinInstalado); dialogoDolphin.close() } }]
    }
    Kirigami.PromptDialog {
        id: dialogoFaltan
        title: "Lo que falta en esta máquina"
        subtitle: herramientas.faltantes.length === 0 ? "Están todos los programas y módulos: cada herramienta puede correr."
                  : herramientas.faltantes.map(f => f.programa + " — lo usan: " + f.usan.join(", ")).join("\n") + "\n\nLos programas del sistema los instala backends/docflow/install.sh; los módulos de Python, install.sh (el .venv)."
        standardButtons: Kirigami.Dialog.Close
    }
    Kirigami.Dialog {
        id: dialogoSalida
        title: "Salida del motor"
        standardButtons: Kirigami.Dialog.Close
        preferredWidth: Math.min(ventana.width * 0.85, Kirigami.Units.gridUnit * 60)
        preferredHeight: Math.min(ventana.height * 0.7, Kirigami.Units.gridUnit * 30)
        padding: 0
        PanelInferior { consola: studio.consola; implicitHeight: dialogoSalida.preferredHeight - Kirigami.Units.gridUnit * 4 }
    }
    DialogoVigilar { id: dialogoVigilar }
    dialogoAjustes: DialogoAjustesStudio {}
}
