// Main.qml — Raphi Studio: las herramientas del motor, los archivos y los trabajos en un espacio de trabajo al estilo
// Dolphin/Kate sobre GuiComun.VentanaStudio. Navegación (Herramientas por familia · Trabajos por estado) · centro (la
// tabla de herramientas o la de trabajos) · detalles (Resumen, Archivos, Opciones generadas de la ficha, Resultado,
// Registro) · panel inferior (la salida del motor) · barra de estado. Soltar archivos en cualquier parte los añade.
// Ninguna llamada al motor ni al disco aquí: todo lo hacen los controladores de Python (studio.*).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami
import GuiComun
import "componentes"

VentanaStudio {
    id: ventana

    readonly property var espacio: studio.espacio
    readonly property var registro: studio.acciones
    readonly property var herramientas: studio.herramientas
    readonly property var archivos: studio.archivos
    readonly property var trabajos: studio.trabajos
    readonly property var ops: studio.operaciones
    readonly property bool enTrabajos: espacio.vista === "trabajos"

    title: (ventana.enTrabajos ? (trabajos.hayActual ? trabajos.titulo : "Trabajos") : (herramientas.hayActual ? herramientas.titulo : espacio.textoFamilia)) + " — Raphi Studio"
    acciones: registro
    tareas: studio.tareas
    consola: studio.consola
    descripcion: descripcionStudio
    autor: "Edison Achalma (@achalmed)"
    resumen: espacio.resumen
    contexto: espacio.contexto
    claveAjustes: "ventana"

    function accion(nombre) { return registro.accion(nombre) }
    function tablaActual() { return ventana.enTrabajos ? tablaTrabajos : tablaHerramientas }
    function irAPestana(i) { ventana.mostrarDetalles = true; detalles.pestanaActual = i }
    function religarNavegacion() { navegacion.actual = Qt.binding(() => espacio.nombreNavegacion) }

    Connections {
        target: studio.interfaz
        function onPedir(nombre, datos) {
            switch (nombre) {
            case "filtrar": filtro.forceActiveFocus(); filtro.selectAll(); break
            case "seleccionar_todo": { const t = tablaActual(); if (t && t.seleccionarTodo) t.seleccionarTodo(); break }
            case "seleccionar_fila": { const t = tablaActual(); if (t && datos.fila >= 0) t.seleccionarFila(datos.fila, true); break }
            case "elegir_archivos": selectorArchivos.open(); break
            case "elegir_carpeta": selectorCarpeta.open(); break
            case "quitar_archivos": paginaArchivos.quitarSeleccion(); break
            case "aplicar": dialogoAplicar.abrir(); break
            case "venv": dialogoVenv.open(); break
            case "dolphin": dialogoDolphin.open(); break
            case "vigilar": dialogoVigilar.open(); break
            case "faltan": dialogoFaltan.open(); break
            case "pestana": irAPestana(datos.indice); break
            case "paleta": ventana.paleta.abrir(datos.texto || ""); break
            case "aviso": ventana.mensajes.mostrar(datos.texto, datos.tipo || "informacion"); break
            case "activar": ventana.show(); ventana.raise(); ventana.requestActivate(); break
            }
        }
    }
    Connections { target: espacio; function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) } function onFiltroCambiado() { religarNavegacion() } function onVistaCambiada() { filtro.text = ""; religarNavegacion() } }
    Connections { target: archivos; function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) } }
    Connections {
        target: herramientas
        function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) }
        function onSeleccionar(fila) { if (fila >= 0) tablaHerramientas.seleccionarFila(fila, true); irAPestana(0) }
    }
    Connections {
        target: trabajos
        function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) }
        function onSeleccionar(fila) { if (fila >= 0) tablaTrabajos.seleccionarFila(fila, true); irAPestana(3) }
        function onTerminado(id, simulado, estado) { if (!ventana.enTrabajos) trabajos.irAlUltimoDe(herramientas.ref); irAPestana(3) }
    }
    Connections { target: ops; function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) } }

    // ------------------------------------------------------------------ soltar archivos en cualquier parte
    DropArea {
        anchors.fill: parent
        z: 100
        keys: ["text/uri-list"]
        onDropped: drop => {
            if (!drop.hasUrls) return
            const rutas = drop.urls.map(u => String(u))
            studio.archivos.recibir(rutas)
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

    // ------------------------------------------------------------------ barra: la operación y el filtro
    herramientasExtra: [
        QQC2.ComboBox {
            id: selectorOperacion
            Layout.preferredWidth: Kirigami.Units.gridUnit * 15
            model: ops.lista
            textRole: "titulo"
            currentIndex: ops.indiceActual
            onActivated: index => ops.fijarPorIndice(index)
            Accessible.name: "Operación"
            QQC2.ToolTip.text: ops.descripcion
            QQC2.ToolTip.visible: hovered && ops.descripcion !== ""
            Connections { target: ops; function onCambiado() { selectorOperacion.currentIndex = ops.indiceActual } }
        },
        Kirigami.SearchField {
            id: filtro
            Layout.preferredWidth: Kirigami.Units.gridUnit * 11
            placeholderText: "Filtrar (Ctrl+F)"
            onTextChanged: { const t = tablaActual(); if (t && t.modelo && t.modelo.filtrar) t.modelo.filtrar(text) }
            Keys.onEscapePressed: { text = ""; const t = tablaActual(); if (t) t.forceActiveFocus() }
            Accessible.name: "Filtrar"
        }
    ]

    // ------------------------------------------------------------------ navegación
    navegacion: PanelNavegacion {
        id: navegacion
        secciones: [
            { titulo: "Herramientas", filas: herramientas.filasNavegacion },
            { titulo: "Trabajos", filas: trabajos.filasNavegacion }
        ]
        onElegida: nombre => {
            if (nombre.startsWith("trabajos")) espacio.fijarGrupo(nombre.length > 8 ? nombre.substring(9) : "todos")
            else espacio.fijarFamilia(nombre.length > 7 ? nombre.substring(8) : "")
            religarNavegacion()
        }
        Component.onCompleted: religarNavegacion()
    }

    // ------------------------------------------------------------------ centro
    centro: StackLayout {
        id: centro
        currentIndex: espacio.indiceVista

        TablaDatos {                                              // 0 · Herramientas
            id: tablaHerramientas
            modelo: herramientas.modelo
            claveAjustes: "herramientas"
            umbralEstrecho: Kirigami.Units.gridUnit * 44
            mensajeVacio: herramientas.total === 0 ? (herramientas.motivoSinFichas ? "El motor no respondió: " + herramientas.motivoSinFichas : "Leyendo las fichas del motor… (F6 las relee)")
                                                   : "Ninguna herramienta cumple el filtro «" + espacio.textoFiltro + "»"
            iconoVacio: "application-x-executable"
            columnas: [
                { ancho: 0, minimo: 12, conIcono: true },
                { ancho: 7, secundaria: true, estrecho: true },
                { ancho: 7, secundaria: true, estrecho: true },
                { ancho: 10, secundaria: true, estrecho: true },
                { ancho: 6, secundaria: true, estrecho: true },
                { ancho: 5, alinear: "derecha", secundaria: true, estrecho: true },
                { ancho: 9, semantica: true }
            ]
            onOrdenar: (columna, descendente) => herramientas.modelo.ordenar(columna, descendente)
            onFilaActualCambiada: fila => herramientas.fijarFila(fila)
            onActivada: fila => { herramientas.fijarFila(fila); irAPestana(archivos.total > 0 ? 2 : 1) }
            menuContextual: MenuAcciones {
                acciones: ventana.registro
                conAtajos: false
                elementos: [
                    { tipo: "accion", nombre: "op.simular" }, { tipo: "accion", nombre: "op.aplicar" },
                    { tipo: "separador" },
                    { tipo: "accion", nombre: "herramienta.archivos" }, { tipo: "accion", nombre: "herramienta.opciones" }, { tipo: "accion", nombre: "herramienta.resultado" },
                    { tipo: "separador" },
                    { tipo: "accion", nombre: "herramienta.restablecer" }
                ]
            }
        }
        TablaDatos {                                              // 1 · Trabajos
            id: tablaTrabajos
            modelo: trabajos.modelo
            claveAjustes: "trabajos"
            umbralEstrecho: Kirigami.Units.gridUnit * 44
            mensajeVacio: trabajos.total === 0 ? "Ningún trabajo todavía: elige una herramienta, añade archivos y simula (F5)" : "Ningún trabajo cumple el filtro «" + espacio.textoFiltro + "»"
            iconoVacio: "view-task"
            columnas: [
                { ancho: 0, minimo: 12, conIcono: true },
                { ancho: 12, secundaria: true, estrecho: true },
                { ancho: 7, semantica: true },
                { ancho: 5, alinear: "derecha", secundaria: true },
                { ancho: 6, mono: true, secundaria: true, estrecho: true },
                { ancho: 6, alinear: "derecha", secundaria: true, estrecho: true },
                { ancho: 5, alinear: "derecha", secundaria: true, estrecho: true }
            ]
            onOrdenar: (columna, descendente) => trabajos.modelo.ordenar(columna, descendente)
            onFilaActualCambiada: fila => trabajos.fijarFila(fila)
            onActivada: fila => { trabajos.fijarFila(fila); irAPestana(3) }
            menuContextual: MenuAcciones {
                acciones: ventana.registro
                conAtajos: false
                elementos: [
                    { tipo: "accion", nombre: "trabajos.herramienta" }, { tipo: "accion", nombre: "op.cancelar" }, { tipo: "accion", nombre: "trabajos.quitar" },
                    { tipo: "separador" },
                    { tipo: "accion", nombre: "archivo.abrir" }, { tipo: "accion", nombre: "archivo.mostrar" },
                    { tipo: "separador" },
                    { tipo: "accion", nombre: "trabajos.limpiar" }
                ]
            }
        }
    }

    // ------------------------------------------------------------------ detalles
    detalles: PanelDetalles {
        id: detalles
        anchoPreferido: Kirigami.Units.gridUnit * 30
        anchoMinimo: Kirigami.Units.gridUnit * 20
        titulo: ventana.enTrabajos ? (trabajos.hayActual ? trabajos.titulo : "") : (herramientas.hayActual ? herramientas.titulo : "")
        subtitulo: ventana.enTrabajos ? (trabajos.hayActual ? trabajos.textoEstado + " · " + trabajos.textoArchivos : "")
                                      : (herramientas.hayActual ? herramientas.textoFamilia + " · " + herramientas.descripcion : "")
        icono: ventana.enTrabajos ? "" : herramientas.icono
        mensajeVacio: ventana.enTrabajos ? "Elige un trabajo en la tabla: su resultado, sus salidas y su registro"
                                         : "Elige una herramienta en la tabla: su ficha, los archivos, sus opciones y su resultado"
        iconoVacio: ventana.enTrabajos ? "view-task" : "application-x-executable"
        accionesCabecera: ventana.enTrabajos ? [ventana.accion("archivo.abrir"), ventana.accion("archivo.mostrar"), ventana.accion("trabajos.herramienta")]
                                             : [ventana.accion("op.simular"), ventana.accion("op.aplicar"), ventana.accion("archivo.anadir")]
        pestanas: [
            { titulo: "Resumen" },
            { titulo: "Archivos", contador: ventana.enTrabajos ? trabajos.archivos.length : archivos.total },
            { titulo: "Opciones", contador: herramientas.campos.length, visible: !ventana.enTrabajos },
            { titulo: "Resultado", contador: trabajos.nSalidas },
            { titulo: "Registro" }
        ]
        Resumen {}
        Archivos { id: paginaArchivos }
        Opciones {}
        Resultado {}
        Registro {}
    }

    inferior: PanelInferior { consola: studio.consola }

    // ------------------------------------------------------------------ diálogos
    FileDialog {
        id: selectorArchivos
        title: "Añadir archivos"
        fileMode: FileDialog.OpenFiles
        nameFilters: herramientas.hayActual && herramientas.extensionesFiltro !== "" ? ["Lo que acepta " + herramientas.titulo + " (" + herramientas.extensionesFiltro + ")", "Todos los archivos (*)"] : ["Todos los archivos (*)"]
        onAccepted: { archivos.agregar(selectedFiles.map(u => String(u))); irAPestana(1) }
    }
    FolderDialog {
        id: selectorCarpeta
        title: "Añadir una carpeta"
        onAccepted: { archivos.agregar([String(selectedFolder)]); irAPestana(1) }
    }
    Kirigami.PromptDialog {
        id: dialogoAplicar
        title: "Aplicar: " + herramientas.titulo
        subtitle: ops.textoConfirmacion
        standardButtons: Kirigami.Dialog.Cancel
        customFooterActions: [Kirigami.Action { text: "Aplicar"; icon.name: "dialog-ok-apply"; enabled: ops.puedeAplicar; onTriggered: { ops.aplicar(); dialogoAplicar.close() } }]
        function abrir() {
            if (!ops.puedeAplicar) { ventana.mensajes.mostrar(ops.motivoNoAplicar, "aviso"); return }
            open()
        }
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
        customFooterActions: [Kirigami.Action { text: "Doctor (F5)"; icon.name: "checkmark"; onTriggered: { ops.fijar("doctor"); ops.simular(); dialogoFaltan.close() } }]
    }
    DialogoVigilar { id: dialogoVigilar }
    dialogoAjustes: DialogoAjustesStudio {}
}
