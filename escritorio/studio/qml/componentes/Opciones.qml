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
        Kirigami.PlaceholderMessage { Layout.fillWidth: true; visible: !pagina.h.hayActual; text: "Ninguna herramienta"; explanation: "Elige una herramienta en el catálogo: sus opciones salen de su ficha."; icon.name: "application-x-executable" }
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: pagina.h.hayActual && pagina.h.faltan.length > 0
            type: Kirigami.MessageType.Warning
            text: "Falta en esta máquina: " + pagina.h.faltan.join(", ") + ". Instálalo para usar esta herramienta (Herramientas › Lo que falta…)."
        }
        EditorEnlace {
            visible: pagina.h.hayActual && !!pagina.h.paramEnlace.clave
            Layout.fillWidth: true
            h: pagina.h
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
        EditorTramo {
            visible: pagina.h.hayActual && !!pagina.h.paramTramo.clave
            Layout.fillWidth: true
            h: pagina.h
        }
        // Los parámetros plegados de la ficha (su `grupo`, p. ej. «Más opciones»)
        QQC2.ToolButton {
            id: verMas
            visible: pagina.h.hayActual && pagina.h.tituloMas !== ""
            checkable: true
            text: pagina.h.tituloMas
            icon.name: checked ? "arrow-down" : "arrow-right"
            Accessible.name: text
        }
        PaginaFormulario {
            id: formularioMas
            visible: verMas.visible && verMas.checked
            Layout.fillWidth: true
            campos: pagina.h.camposMas
            nombreAccesible: pagina.h.tituloMas
            onCamposChanged: poner(pagina.h.valores)
            onCambiado: (clave, valor) => pagina.h.fijarValor(clave, valor)
            Connections { target: pagina.h; function onOpcionesCambiadas() { if (JSON.stringify(formularioMas.valores) !== JSON.stringify(pagina.h.valores)) formularioMas.poner(pagina.h.valores) } }
            Component.onCompleted: poner(pagina.h.valores)
        }
        // dónde dejar el resultado: un título alineado con el resto (no la sección centrada de FormLayout), y solo si
        // la herramienta escribe algo
        Kirigami.Heading {
            visible: pagina.h.hayActual && pagina.o.escribe
            level: 4
            text: "Dónde dejar el resultado"
            Layout.topMargin: Kirigami.Units.smallSpacing
        }
        Kirigami.FormLayout {
            visible: pagina.h.hayActual && pagina.o.escribe
            Layout.fillWidth: true
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
        // Simular y Procesar viven una sola vez, en la barra de arriba; aquí, volver a las opciones de siempre
        RowLayout {
            visible: pagina.h.hayActual
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            BotonAccion { accion: studio.acciones.accion("herramienta.restablecer"); conTexto: true }
            Item { Layout.fillWidth: true }
            QQC2.Label {
                visible: !pagina.o.escribe
                text: "Solo lee: el resultado sale en el monitor (F5)."
                color: Kirigami.Theme.disabledTextColor
                font.pointSize: Kirigami.Theme.smallFont.pointSize
            }
        }
        Item { Layout.preferredHeight: Kirigami.Units.largeSpacing }
    }
}
