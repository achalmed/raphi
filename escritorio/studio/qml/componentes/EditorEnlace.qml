// EditorEnlace — la vista «enlace» de un parámetro (genérica: la dibuja cualquier herramienta cuya ficha tenga un
// parámetro con vista «enlace»): donde se pegan los enlaces y, debajo, qué es el primero (miniatura, título, canal,
// duración, si es una lista o si está EN VIVO y de qué hora a qué hora se puede bajar), consultado sin bajar nada.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz
    required property var h            // studio.herramientas
    readonly property var p: h.paramEnlace
    readonly property var info: h.infoEnlace
    readonly property bool vivo: info.en_vivo === true
    spacing: Kirigami.Units.smallSpacing

    function reloj(s) {
        const t = Math.max(0, Math.round(s)), hh = Math.floor(t / 3600), mm = Math.floor((t % 3600) / 60), ss = t % 60
        const dos = n => (n < 10 ? "0" : "") + n
        return hh ? hh + ":" + dos(mm) + ":" + dos(ss) : mm + ":" + dos(ss)
    }
    function hora(epoca) { return new Date((epoca + (info.zona || 0)) * 1000).toISOString().slice(11, 19) }

    Kirigami.Heading { level: 4; text: raiz.p.etiqueta || "Enlace"; Layout.fillWidth: true }
    QQC2.TextArea {
        id: campo
        Layout.fillWidth: true
        Layout.minimumHeight: Kirigami.Units.gridUnit * 2.5
        placeholderText: "https://www.youtube.com/watch?v=…   ·   https://www.facebook.com/…   ·   https://www.tiktok.com/…"
        wrapMode: TextEdit.WrapAnywhere
        text: raiz.h.valores[raiz.p.clave] || ""
        Accessible.name: raiz.p.etiqueta || "Enlace"
        onTextChanged: { if (text !== (raiz.h.valores[raiz.p.clave] || "")) raiz.h.fijarValor(raiz.p.clave, text); espera.restart() }
        Timer { id: espera; interval: 700; onTriggered: raiz.h.consultarEnlace(campo.text) }
        Component.onCompleted: if (text) raiz.h.consultarEnlace(text)
    }
    QQC2.Label {
        Layout.fillWidth: true
        visible: raiz.h.estadoEnlace === ""
        text: "Pega el enlace: Raphi muestra qué video es antes de bajarlo."
        color: Kirigami.Theme.disabledTextColor
        wrapMode: Text.WordWrap
    }
    RowLayout {
        Layout.fillWidth: true
        visible: raiz.h.estadoEnlace === "consultando"
        QQC2.BusyIndicator { running: parent.visible; Layout.preferredHeight: Kirigami.Units.gridUnit * 1.5; Layout.preferredWidth: Layout.preferredHeight }
        QQC2.Label { text: "Consultando el enlace…"; color: Kirigami.Theme.disabledTextColor }
    }
    Kirigami.InlineMessage {
        Layout.fillWidth: true
        visible: raiz.h.estadoEnlace === "error"
        type: Kirigami.MessageType.Warning
        text: raiz.info.error || ""
    }
    RowLayout {
        Layout.fillWidth: true
        visible: raiz.h.estadoEnlace === "listo"
        spacing: Kirigami.Units.largeSpacing
        Rectangle {
            Layout.preferredWidth: raiz.info.vertical ? Kirigami.Units.gridUnit * 4 : Kirigami.Units.gridUnit * 8
            Layout.preferredHeight: raiz.info.vertical ? Kirigami.Units.gridUnit * 7 : Kirigami.Units.gridUnit * 4.5
            Layout.alignment: Qt.AlignTop
            radius: Kirigami.Units.cornerRadius
            color: Kirigami.Theme.alternateBackgroundColor
            clip: true
            Image { anchors.fill: parent; source: raiz.info.miniatura || ""; fillMode: Image.PreserveAspectCrop; asynchronous: true }
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            spacing: Kirigami.Units.smallSpacing
            QQC2.Label { Layout.fillWidth: true; text: raiz.info.titulo || ""; font.weight: Font.Medium; wrapMode: Text.WordWrap }
            QQC2.Label {
                Layout.fillWidth: true
                text: [raiz.info.canal !== raiz.info.titulo ? raiz.info.canal : "", raiz.info.sitio].filter(x => x).join(" · ")
                color: Kirigami.Theme.disabledTextColor
                wrapMode: Text.WordWrap
            }
            RowLayout {
                spacing: Kirigami.Units.smallSpacing
                Rectangle {
                    visible: raiz.vivo
                    color: Kirigami.Theme.negativeBackgroundColor
                    radius: height / 2
                    implicitWidth: enVivo.implicitWidth + Kirigami.Units.largeSpacing
                    implicitHeight: enVivo.implicitHeight + Kirigami.Units.smallSpacing
                    QQC2.Label { id: enVivo; anchors.centerIn: parent; text: "EN VIVO"; color: Kirigami.Theme.negativeTextColor; font.weight: Font.Medium }
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    color: Kirigami.Theme.disabledTextColor
                    text: {
                        const i = raiz.info, partes = []
                        if (raiz.vivo && i.ventana && i.ventana.desde) partes.push("se puede bajar de las " + raiz.hora(i.ventana.desde) + " a las " + raiz.hora(i.ventana.hasta))
                        else if (i.duracion) partes.push("Dura " + raiz.reloj(i.duracion))
                        if (i.lista) partes.push("lista de " + i.elementos + " videos")
                        if (i.vertical) partes.push("vertical")
                        if (i.calidades && i.calidades.length) partes.push("hasta " + i.calidades[0] + "p")
                        if (i.varios) partes.push("(y más enlaces)")
                        return partes.join(" · ")
                    }
                }
            }
        }
    }
}
