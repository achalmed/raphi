// Opciones — el formulario de la herramienta actual, generado de su ficha (PaginaFormulario del marco: un control por
// tipo de parámetro), dónde dejar la salida (junto a cada original · en una carpeta) y Simular / Aplicar.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.ScrollView {
    id: pagina
    readonly property var h: studio.herramientas
    readonly property var o: studio.operaciones
    contentWidth: availableWidth
    QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff
    ColumnLayout {
        id: columna
        width: pagina.availableWidth - Kirigami.Units.largeSpacing * 2
        x: Kirigami.Units.largeSpacing
        y: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing
        Kirigami.PlaceholderMessage { Layout.fillWidth: true; visible: !pagina.h.hayActual; text: "Ninguna herramienta"; explanation: "Elige una herramienta en la tabla: sus opciones salen de su ficha."; icon.name: "application-x-executable" }
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: pagina.h.hayActual && pagina.h.faltan.length > 0
            type: Kirigami.MessageType.Warning
            text: "Falta en esta máquina: " + pagina.h.faltan.join(", ") + ". Instálalo para usar esta herramienta (Herramientas › Lo que falta…)."
        }
        PaginaFormulario {
            id: formulario
            visible: pagina.h.hayActual
            Layout.fillWidth: true
            campos: pagina.h.campos
            nombreAccesible: "Opciones de " + (pagina.h.titulo || "la herramienta")
            mensajeVacio: pagina.h.esReceta ? "Una receta no tiene opciones: cada paso lleva las suyas." : "Esta herramienta no tiene opciones."
            onCamposChanged: poner(pagina.h.valores)
            onCambiado: (clave, valor) => pagina.h.fijarValor(clave, valor)
            Connections { target: pagina.h; function onOpcionesCambiadas() { if (JSON.stringify(formulario.valores) !== JSON.stringify(pagina.h.valores)) formulario.poner(pagina.h.valores) } }
            Component.onCompleted: poner(pagina.h.valores)
        }
        Kirigami.FormLayout {
            visible: pagina.h.hayActual
            Layout.fillWidth: true
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Dónde dejar el resultado" }
            QQC2.RadioButton {
                id: junto
                text: pagina.h.sinArchivos ? "En Descargas" : "Junto a cada original"
                checked: !pagina.h.enCarpeta
                onToggled: if (checked) pagina.h.fijarEnCarpeta(false)
                Accessible.name: text
            }
            QQC2.RadioButton {
                id: enCarpeta
                text: "En otra carpeta"
                checked: pagina.h.enCarpeta
                onToggled: if (checked) pagina.h.fijarEnCarpeta(true)
                Accessible.name: text
            }
            CampoRuta {
                id: campoDestino
                Kirigami.FormData.label: "Carpeta:"
                Layout.fillWidth: true
                Layout.maximumWidth: columna.width - Kirigami.Units.gridUnit * 6
                enabled: pagina.h.enCarpeta
                texto: pagina.h.destino
                titulo: "Carpeta de salida"
                nombreAccesible: "Carpeta de salida"
                onAceptada: t => pagina.h.fijarDestino(t)
                onTextoChanged: if (texto !== pagina.h.destino) pagina.h.fijarDestino(texto)
            }
            QQC2.Label { Kirigami.FormData.label: "Salida:"; text: pagina.h.destinoEfectivo; wrapMode: Text.WrapAnywhere; Layout.fillWidth: true; color: Kirigami.Theme.disabledTextColor }
            QQC2.Label { Kirigami.FormData.label: "Ahora:"; visible: !pagina.o.puedeSimular; text: pagina.o.motivoNoSimular; wrapMode: Text.WordWrap; Layout.fillWidth: true; color: Kirigami.Theme.neutralTextColor }
        }
        RowLayout {
            visible: pagina.h.hayActual
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            BotonAccion { accion: studio.acciones.accion("herramienta.restablecer"); conTexto: false }
            Item { Layout.fillWidth: true }
            BotonAccion { accion: studio.acciones.accion("op.cancelar"); conTexto: false; visible: pagina.o.enCurso }
            BotonAccion { accion: studio.acciones.accion("op.simular") }
            QQC2.Button {
                readonly property var a: studio.acciones.accion("op.aplicar")
                visible: pagina.o.escribe
                highlighted: true
                text: a.textoPlano; icon.name: a.icono; enabled: a.habilitada
                onClicked: a.disparar()
                QQC2.ToolTip.text: a.descripcion + " (" + a.atajoTexto + ")"; QQC2.ToolTip.visible: hovered
            }
        }
        Item { Layout.preferredHeight: Kirigami.Units.largeSpacing }
    }
}
