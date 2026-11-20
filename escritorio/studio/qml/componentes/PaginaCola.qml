// PaginaCola — la cola de trabajos como vista propia (reingeniería X5): a la izquierda los trabajos por sección (en
// curso con su barra de progreso, en cola, hechos, con error), filtrables por grupo; a la derecha el trabajo elegido —
// sus entradas, opciones y salida, el resultado (el plan si fue simulado), las salidas con su vista previa (abrir con
// su aplicación, mostrar en Dolphin) y el registro del motor — con Detener, Quitar, Repetir e Ir a su herramienta.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.SplitView {
    id: raiz
    readonly property var t: studio.trabajos
    readonly property var e: studio.espacio
    orientation: Qt.Horizontal

    Connections { target: raiz.t; function onSeleccionar(fila) { if (fila >= 0) lista.currentIndex = fila } }

    ColumnLayout {
        QQC2.SplitView.preferredWidth: Kirigami.Units.gridUnit * 30
        QQC2.SplitView.minimumWidth: Kirigami.Units.gridUnit * 18
        clip: true
        spacing: 0
        // los grupos de la cola: un selector con la cifra de cada uno (y limpiar los terminados al lado)
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            Layout.leftMargin: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing
            Flickable {
                Layout.fillWidth: true
                Layout.preferredHeight: grupos.implicitHeight
                contentWidth: grupos.implicitWidth
                flickableDirection: Flickable.HorizontalFlick
                boundsBehavior: Flickable.StopAtBounds
                clip: contentWidth > width
                SelectorSegmentado {
                    id: grupos
                    titulo: "Grupos de la cola"
                    compacto: true
                    opciones: raiz.t.filasNavegacion.map(f => ({ clave: f.nombre === "trabajos" ? "todos" : f.nombre.substring(9), texto: f.texto,
                                                                   contador: f.contador }))
                    actual: raiz.e.grupo
                    onElegida: (clave) => raiz.e.fijarGrupo(clave)
                }
            }
            BotonAccion { accion: studio.acciones.accion("trabajos.limpiar"); conTexto: false }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        ListView {
            id: lista
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: raiz.t.modelo
            currentIndex: -1
            Accessible.name: "Trabajos"
            QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
            section.property: "seccion"
            section.delegate: Kirigami.ListSectionHeader { required property string section; width: lista.width - Kirigami.Units.smallSpacing * 2; text: section }
            leftMargin: Kirigami.Units.smallSpacing
            rightMargin: Kirigami.Units.smallSpacing
            spacing: 2
            // el elegido teñido con su marca; su estado, una etiqueta del color de su nivel (también sobre lo elegido)
            delegate: QQC2.ItemDelegate {
                id: fila
                required property var model
                required property int index
                width: lista.width - Kirigami.Units.smallSpacing * 2
                hoverEnabled: true
                onClicked: { lista.currentIndex = index; raiz.t.fijarFila(index) }
                Accessible.name: model.titulo + ": " + model.estado + (ListView.isCurrentItem ? ", elegido" : "")
                // sin los márgenes que el estilo de KDE deja alrededor del fondo: el fondo es la fila entera y
                // el contenido respeta su relleno (con ellos, la marca de lo elegido caía encima del texto)
                leftInset: 0; rightInset: 0; topInset: 0; bottomInset: 0
                topPadding: Kirigami.Units.smallSpacing * 2; bottomPadding: Kirigami.Units.smallSpacing * 2
                background: FondoSeleccion { elegida: fila.ListView.isCurrentItem; sobre: fila.hovered; pulsada: fila.pressed; foco: fila.visualFocus }
                contentItem: ColumnLayout {
                    spacing: Kirigami.Units.smallSpacing / 2
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Kirigami.Units.smallSpacing
                        QQC2.Label { text: fila.model.titulo; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                        EtiquetaNivel { text: fila.model.estado; nivel: fila.model.nivel || ""; icono: fila.model.icono || "" }
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: fila.model.archivos + (fila.model.salidas ? " → " + fila.model.salidas + " salida" + (fila.model.salidas === 1 ? "" : "s") : "")
                              + " · " + fila.model.inicio + (fila.model.duracion !== "—" ? " · " + fila.model.duracion : "")
                        elide: Text.ElideRight
                        font.pointSize: Kirigami.Theme.smallFont.pointSize
                        color: Kirigami.Theme.disabledTextColor
                    }
                    QQC2.ProgressBar { Layout.fillWidth: true; visible: fila.model.clave === "en_curso"; from: 0; to: 100; value: fila.model.porcentaje }
                    QQC2.Label { Layout.fillWidth: true; visible: fila.model.mensaje !== "" && fila.model.clave !== "hecho"; text: fila.model.mensaje; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight; font: Kirigami.Theme.smallFont }
                }
            }
            Kirigami.PlaceholderMessage {
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.gridUnit * 4
                visible: lista.count === 0
                icon.name: "view-task"
                text: raiz.t.total === 0 ? "La cola está vacía" : "Ningún trabajo " + raiz.e.textoGrupo.toLowerCase()
                explanation: raiz.t.total === 0 ? "Elige una herramienta, añade entradas y procesa (Ctrl+Intro): el trabajo aparece aquí con su progreso." : ""
            }
        }
    }

    // ------------------------------------------------------------------ el trabajo elegido
    ColumnLayout {
        QQC2.SplitView.fillWidth: true
        QQC2.SplitView.minimumWidth: Kirigami.Units.gridUnit * 20
        spacing: 0
        Kirigami.PlaceholderMessage {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !raiz.t.hayActual
            icon.name: "view-task"
            text: "Elige un trabajo"
            explanation: "Su resultado, sus salidas con vista previa y el registro del motor."
        }
        ColumnLayout {
            visible: raiz.t.hayActual
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing
            RowLayout {
                Layout.fillWidth: true
                Kirigami.Heading { level: 2; text: raiz.t.titulo + (raiz.t.simulado ? " (simulación)" : ""); elide: Text.ElideRight; Layout.fillWidth: true }
                BotonAccion { accion: studio.acciones.accion("op.cancelar"); visible: raiz.t.estado === "en_curso" }
                BotonAccion { accion: studio.acciones.accion("trabajos.quitar"); visible: raiz.t.estado === "en_cola" }
                BotonAccion { accion: studio.acciones.accion("trabajos.repetir"); visible: raiz.t.estado !== "en_cola" && raiz.t.estado !== "en_curso" }
                BotonAccion { accion: studio.acciones.accion("trabajos.herramienta"); conTexto: false }
            }
            QQC2.ProgressBar { Layout.fillWidth: true; visible: raiz.t.estado === "en_curso"; from: 0; to: 100; value: raiz.t.progreso }
            Kirigami.FormLayout {
                Layout.fillWidth: true
                wideMode: true
                Layout.alignment: Qt.AlignLeft
                QQC2.Label { Kirigami.FormData.label: "Estado:"; text: raiz.t.textoEstado + (raiz.t.mensaje ? " · " + raiz.t.mensaje : ""); wrapMode: Text.WordWrap; Layout.fillWidth: true }
                QQC2.Label { Kirigami.FormData.label: "Entradas:"; text: raiz.t.textoArchivos; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                QQC2.Label { Kirigami.FormData.label: "Opciones:"; text: raiz.t.textoOpciones; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                QQC2.Label { Kirigami.FormData.label: "Salida:"; text: raiz.t.destino; wrapMode: Text.WrapAnywhere; Layout.fillWidth: true }
                QQC2.Label { Kirigami.FormData.label: "Inicio:"; text: raiz.t.inicio + (raiz.t.duracion ? " · " + raiz.t.duracion : "") }
            }
        }
        SelectorSegmentado {
            id: pestanas
            // qué se ve del trabajo: su propio estado (el selector de la base solo avisa con `elegida`)
            property string vista: "resultado"
            readonly property int currentIndex: ["resultado", "salidas", "registro"].indexOf(vista)
            visible: raiz.t.hayActual
            Layout.leftMargin: Kirigami.Units.largeSpacing
            Layout.bottomMargin: Kirigami.Units.smallSpacing
            titulo: "Lo que se ve del trabajo"
            actual: vista
            onElegida: (clave) => vista = clave
            opciones: [{ clave: "resultado", texto: "Resultado", icono: "view-task" },
                       { clave: "salidas", texto: "Salidas", icono: "document-preview", contador: raiz.t.nSalidas, visible: raiz.t.nSalidas > 0 },
                       { clave: "registro", texto: "Registro", icono: "utilities-terminal" }]
            Connections { target: raiz.t; function onCambiado() { if (raiz.t.nSalidas === 0 && pestanas.vista === "salidas") pestanas.vista = "resultado" } }
        }
        StackLayout {
            visible: raiz.t.hayActual
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: pestanas.currentIndex
            VistaTexto {
                texto: raiz.t.resultado
                markdown: true
                mensajeVacio: raiz.t.estado === "en_curso" ? "En curso: " + raiz.t.progreso + " %" : raiz.t.estado === "en_cola" ? "En cola" : "Sin informe"
                iconoVacio: "view-task"
                nombreAccesible: "Resultado del trabajo"
            }
            ColumnLayout {
                spacing: 0
                Flow {
                    Layout.fillWidth: true
                    Layout.margins: Kirigami.Units.smallSpacing
                    spacing: Kirigami.Units.smallSpacing
                    Repeater {
                        model: raiz.t.salidas
                        delegate: QQC2.Button {
                            required property var modelData
                            required property int index
                            text: String(modelData).split("/").pop()
                            icon.name: "document-preview"
                            checkable: true
                            checked: raiz.t.salidaActual === String(modelData)
                            onClicked: { raiz.t.fijarSalida(index); studio.vista.mostrar(String(modelData)) }
                        }
                    }
                }
                VistaPrevia {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    vacio: "Elige una salida arriba"
                }
            }
            VistaTexto {
                texto: raiz.t.registro
                definicion: "Bash"
                mensajeVacio: "Sin registro todavía"
                iconoVacio: "utilities-terminal"
                nombreAccesible: "Registro del trabajo"
            }
        }
    }
}
