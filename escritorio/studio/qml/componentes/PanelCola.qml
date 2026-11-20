// PanelCola — a la derecha del taller (rediseño aprobado del 2026-11-18): la cola entera, siempre a la vista mientras
// se elige una herramienta o se trabaja con ella. Arriba, el trabajo en curso con su barra de avance (indeterminada si
// el motor aún no dice cuánto lleva) y Detener; debajo, los trabajos por sección (en curso, en cola, hechos, con error)
// con su estado en color de estado. Un clic abre el trabajo en la vista Cola (Ctrl+3), con su resultado, sus salidas y
// su registro. Sin filtro: el de grupo es de la vista Cola.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: panel
    readonly property var t: studio.trabajos
    readonly property var c: t.contadores
    spacing: 0
    Accessible.name: "Cola de trabajos"

    // ------------------------------------------------------------------ cabecera: la cola y sus cuentas
    RowLayout {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        Layout.leftMargin: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.smallSpacing
        Kirigami.Heading { level: 4; text: "Cola"; Layout.fillWidth: true }
        BotonAccion { accion: studio.acciones.accion("trabajos.limpiar"); conTexto: false; enabled: panel.c.hechos + panel.c.con_error > 0 }
        BotonAccion { accion: studio.acciones.accion("ver.cola"); conTexto: false }
    }
    QQC2.Label {
        Layout.fillWidth: true
        Layout.leftMargin: Kirigami.Units.largeSpacing
        Layout.rightMargin: Kirigami.Units.largeSpacing
        visible: panel.c.todos > 0
        text: panel.c.todos === 0 ? "Sin trabajos"
              : [panel.c.en_curso ? panel.c.en_curso + " en curso" : "", panel.c.en_cola ? panel.c.en_cola + " en cola" : "",
                 panel.c.hechos ? panel.c.hechos + " hecho" + (panel.c.hechos === 1 ? "" : "s") : "",
                 panel.c.con_error ? panel.c.con_error + " con error" : ""].filter(x => x).join(" · ")
        font: Kirigami.Theme.smallFont
        color: Kirigami.Theme.disabledTextColor
        elide: Text.ElideRight
    }

    // ------------------------------------------------------------------ el trabajo en curso y su barra de avance (solo si
    // hay algo en curso o esperando: el vacío lo dice el mensaje de la lista, una sola vez)
    ColumnLayout {
        visible: panel.t.enCurso || panel.c.en_cola > 0
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.smallSpacing
        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon {
                source: panel.t.enCurso ? "media-playback-start" : "media-playback-stopped"
                implicitWidth: Kirigami.Units.iconSizes.small
                implicitHeight: implicitWidth
                color: panel.t.enCurso ? Kirigami.Theme.activeTextColor : Kirigami.Theme.disabledTextColor
                isMask: true
            }
            QQC2.Label {
                Layout.fillWidth: true
                text: panel.t.enCurso ? panel.t.tituloEnCurso : "Nada en curso"
                font.weight: panel.t.enCurso ? Font.DemiBold : Font.Normal
                color: panel.t.enCurso ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
                elide: Text.ElideRight
            }
            QQC2.Label {
                visible: panel.t.enCurso && panel.t.progresoEnCurso > 0
                text: panel.t.progresoEnCurso + " %"
            }
            BotonAccion { accion: studio.acciones.accion("op.cancelar"); conTexto: false; visible: panel.t.enCurso }
        }
        QQC2.ProgressBar {
            Layout.fillWidth: true
            from: 0
            to: 100
            value: panel.t.enCurso ? panel.t.progresoEnCurso : 0
            indeterminate: panel.t.enCurso && panel.t.progresoEnCurso === 0
            enabled: panel.t.enCurso
            Accessible.name: panel.t.enCurso ? "Avance de " + panel.t.tituloEnCurso : "Sin trabajo en curso"
        }
        QQC2.Label {
            Layout.fillWidth: true
            visible: text !== ""
            text: panel.t.enCurso ? (panel.t.mensajeEnCurso + (panel.c.en_cola ? (panel.t.mensajeEnCurso ? " · " : "") + "después, " + panel.c.en_cola + " más" : ""))
                                  : panel.c.en_cola ? panel.c.en_cola + " esperando" : ""
            font: Kirigami.Theme.smallFont
            color: Kirigami.Theme.disabledTextColor
            elide: Text.ElideRight
        }
    }
    Kirigami.Separator { Layout.fillWidth: true; visible: panel.t.enCurso || panel.c.en_cola > 0 }

    // ------------------------------------------------------------------ los trabajos
    ListView {
        id: lista
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        model: panel.t.modeloCompleto
        currentIndex: -1
        Accessible.name: "Trabajos"
        QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
        section.property: "seccion"
        section.delegate: Kirigami.ListSectionHeader { required property string section; width: lista.width; text: section }
        leftMargin: Kirigami.Units.smallSpacing
        rightMargin: Kirigami.Units.smallSpacing
        spacing: 2
        // cada trabajo: el elegido teñido del acento con su marca (nunca el bloque lleno: en Lliphi Oscuro el acento es
        // rojo y un trabajo hecho parecería un error); su estado, una etiqueta del color de su nivel
        delegate: QQC2.ItemDelegate {
            id: fila
            required property var model
            required property int index
            readonly property bool elegida: panel.t.hayActual && panel.t.id === model.id
            width: lista.width - Kirigami.Units.smallSpacing * 2
            hoverEnabled: true
            onClicked: panel.t.irA(model.id)
            Accessible.name: model.titulo + ": " + model.estado + (elegida ? ", elegido" : "")
            QQC2.ToolTip.text: "Ver el trabajo en la cola: su resultado, sus salidas y su registro"
            QQC2.ToolTip.visible: hovered
            QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
            // sin los márgenes que el estilo de KDE deja alrededor del fondo: el fondo es la fila entera y
            // el contenido respeta su relleno (con ellos, la marca de lo elegido caía encima del texto)
            leftInset: 0; rightInset: 0; topInset: 0; bottomInset: 0
            topPadding: Kirigami.Units.smallSpacing * 2; bottomPadding: Kirigami.Units.smallSpacing * 2
            background: FondoSeleccion { elegida: fila.elegida; sobre: fila.hovered; pulsada: fila.pressed; foco: fila.visualFocus }
            contentItem: ColumnLayout {
                spacing: Kirigami.Units.smallSpacing / 2
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing
                    QQC2.Label {
                        text: fila.model.titulo
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        font.weight: fila.elegida ? Font.DemiBold : Font.Normal
                    }
                    EtiquetaNivel {
                        text: fila.model.clave === "en_curso" ? fila.model.progreso : fila.model.estado
                        nivel: fila.model.nivel || ""
                        icono: fila.model.icono || ""
                    }
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    text: fila.model.archivos + (fila.model.duracion && fila.model.duracion !== "—" ? " · " + fila.model.duracion : "")
                    elide: Text.ElideRight
                    font.pointSize: Kirigami.Theme.smallFont.pointSize
                    color: Kirigami.Theme.disabledTextColor
                }
            }
        }
        Kirigami.PlaceholderMessage {
            anchors.centerIn: parent
            width: parent.width - Kirigami.Units.gridUnit * 2
            visible: lista.count === 0
            icon.name: "view-task"
            text: "La cola está vacía"
            explanation: "Elige una herramienta y procesa (Ctrl+Intro): el trabajo aparece aquí con su avance."
        }
    }
}
