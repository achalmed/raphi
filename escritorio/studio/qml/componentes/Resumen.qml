// Resumen — la herramienta actual (su ficha en Markdown: qué hace, qué recibe, qué necesita, sus opciones) o, en la
// vista Trabajos, el trabajo actual (estado, archivos, opciones, salida, tiempos).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

Item {
    id: pagina
    readonly property var h: studio.herramientas
    readonly property var t: studio.trabajos
    readonly property bool enTrabajos: studio.espacio.vista === "trabajos"
    function colorEstado(nivel) {
        switch (nivel) {
        case "positivo": return Kirigami.Theme.positiveTextColor
        case "neutro": return Kirigami.Theme.neutralTextColor
        case "negativo": return Kirigami.Theme.negativeTextColor
        case "activo": return Kirigami.Theme.activeTextColor
        default: return Kirigami.Theme.textColor
        }
    }
    VistaTexto {
        anchors.fill: parent
        visible: !pagina.enTrabajos
        texto: pagina.h.resumenMarkdown
        markdown: true
        mensajeVacio: "Ninguna herramienta"
        iconoVacio: "application-x-executable"
        nombreAccesible: "Resumen de " + (pagina.h.titulo || "ninguna herramienta")
    }
    QQC2.ScrollView {
        anchors.fill: parent
        visible: pagina.enTrabajos
        contentWidth: availableWidth
        QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff
        ColumnLayout {
            width: parent.availableWidth - Kirigami.Units.largeSpacing * 2
            x: Kirigami.Units.largeSpacing
            y: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.largeSpacing
            Kirigami.PlaceholderMessage { Layout.fillWidth: true; visible: !pagina.t.hayActual; text: "Ningún trabajo"; explanation: "Elige un trabajo en la tabla."; icon.name: "view-task" }
            Kirigami.FormLayout {
                visible: pagina.t.hayActual
                Layout.fillWidth: true
                QQC2.Label { Kirigami.FormData.label: "Estado:"; text: pagina.t.textoEstado + (pagina.t.simulado ? " (simulación)" : ""); color: pagina.colorEstado(pagina.t.nivelEstado); font.bold: true }
                QQC2.Label { Kirigami.FormData.label: "Mensaje:"; visible: pagina.t.mensaje !== ""; text: pagina.t.mensaje; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                QQC2.ProgressBar { Kirigami.FormData.label: "Progreso:"; visible: pagina.t.estado === "en_curso"; from: 0; to: 100; value: pagina.t.progreso; Layout.fillWidth: true }
                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "El trabajo" }
                QQC2.Label { Kirigami.FormData.label: "Herramienta:"; text: pagina.t.titulo; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                QQC2.Label { Kirigami.FormData.label: "Archivos:"; text: pagina.t.textoArchivos; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                QQC2.Label { Kirigami.FormData.label: "Opciones:"; text: pagina.t.textoOpciones; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                QQC2.Label { Kirigami.FormData.label: "Salida:"; text: pagina.t.destino; wrapMode: Text.WrapAnywhere; Layout.fillWidth: true }
                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Tiempos" }
                QQC2.Label { Kirigami.FormData.label: "Inicio:"; text: pagina.t.inicio; font: Kirigami.Theme.fixedWidthFont }
                QQC2.Label { Kirigami.FormData.label: "Duración:"; visible: pagina.t.duracion !== ""; text: pagina.t.duracion }
                QQC2.Label { Kirigami.FormData.label: "Salidas:"; text: pagina.t.nSalidas > 0 ? pagina.t.nSalidas + " (pestaña Resultado)" : (pagina.t.simulado ? "ninguna: fue una simulación" : "ninguna") }
            }
            Item { Layout.preferredHeight: Kirigami.Units.largeSpacing }
        }
    }
}
