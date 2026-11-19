// EditorTramo — la vista «tramo» de un parámetro (genérica, como en la web): «Todo» o «Solo un tramo», elegido con una
// barra de dos asas y dos horas sobre lo que dijo el enlace (EditorEnlace):
// - un video: sobre su duración («1:02:00-1:05:30», desde el comienzo);
// - una transmisión EN VIVO: siempre un tramo, por la HORA del reloj («@11:18:44-@11:20:47»), con atajos.
// Sin datos del enlace, un campo de texto. El valor es el texto que entiende el motor (`leer_tramo`).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz
    property var h: studio.herramientas        // por omisión, el de la ventana (Opciones lo pasa igual)
    readonly property var p: h.paramTramo
    readonly property var info: h.estadoEnlace === "listo" && !h.infoEnlace.varios ? h.infoEnlace : ({})
    readonly property bool vivo: info.en_vivo === true && !!info.ventana && !!info.ventana.desde
    // En vivo la ventana crece mientras se mira: el reloj la corre cada segundo (y el inicio, si ya está llena)
    property real ahora: Date.now() / 1000
    readonly property real paso: vivo ? Math.max(0, ahora - (info.consultado || ahora)) : 0
    readonly property var escala: vivo ? [info.ventana.desde + (info.ventana.llena ? paso : 0), info.ventana.hasta + paso]
                                       : (info.duracion ? [0, info.duracion] : null)
    Timer { interval: 1000; repeat: true; running: raiz.vivo && raiz.visible; onTriggered: raiz.ahora = Date.now() / 1000 }
    readonly property string valor: h.valores[p.clave] || ""
    property bool pide: valor !== ""
    readonly property bool quiere: vivo || pide
    readonly property var actual: leer(valor)
    spacing: Kirigami.Units.smallSpacing

    function dos(n) { return (n < 10 ? "0" : "") + n }
    function reloj(s) {
        const t = Math.max(0, Math.round(s)), hh = Math.floor(t / 3600), mm = Math.floor((t % 3600) / 60), ss = t % 60
        return hh ? hh + ":" + dos(mm) + ":" + dos(ss) : mm + ":" + dos(ss)
    }
    function hora(epoca) { return new Date((epoca + (info.zona || 0)) * 1000).toISOString().slice(11, 19) }
    function formato(x) { return vivo ? hora(x) : reloj(x) }
    function segundos(t) { return t.trim().split(":").reduce((a, x) => a * 60 + Number(x), 0) }
    function valido(t) { return /^\d+(:\d{1,2}){0,2}$/.test(t.trim()) }
    function leer(v) {
        const m = v.match(/^\s*(@?[\d:]+)\s*(?:-|\.\.|\sa\s)\s*(@?[\d:]+)\s*$/)
        if (!m || !escala) return null
        if (vivo) {
            if (m[1][0] !== "@" || m[2][0] !== "@") return null
            const dia = t => { const x = t.slice(1); return segundos(x.split(":").length === 2 ? x + ":00" : x) }
            const hasta = escala[1], base = hasta + info.zona, medianoche = base - (base % 86400) - info.zona
            let a = medianoche + dia(m[1]), b = medianoche + dia(m[2])
            if (a > hasta + 300) { a -= 86400; b -= 86400 }
            if (b <= a) b += 86400
            return [a, b]
        }
        if (m[1][0] === "@") return null
        return [segundos(m[1]), segundos(m[2])]
    }
    function escribir(a, b) { raiz.h.fijarValor(raiz.p.clave, vivo ? "@" + formato(a) + "-@" + formato(b) : formato(a) + "-" + formato(b)) }
    function porOmision() {
        if (!quiere || !escala) return
        const a = leer(valor)           // no `actual`: puede estar aún sin recalcular con la escala nueva
        if (a && a[0] >= escala[0] && a[1] <= escala[1] + 1) return
        if (vivo) escribir(Math.max(escala[0], escala[1] - 120), escala[1])
        else escribir(escala[0], Math.min(escala[1], escala[0] + 60))
    }
    onInfoChanged: porOmision()
    onQuiereChanged: porOmision()

    Kirigami.Heading { level: 4; text: raiz.p.etiqueta || "Tramo" }
    QQC2.Label { visible: raiz.vivo; text: "Está en vivo: elige qué parte bajar (por la hora)."; color: Kirigami.Theme.disabledTextColor; Layout.fillWidth: true; wrapMode: Text.WordWrap }
    RowLayout {
        Layout.fillWidth: true
        visible: !raiz.vivo
        spacing: Kirigami.Units.largeSpacing
        QQC2.RadioButton { visible: !raiz.vivo; text: "Todo el video"; checked: !raiz.pide; onToggled: if (checked) { raiz.pide = false; raiz.h.fijarValor(raiz.p.clave, "") } }
        QQC2.RadioButton { visible: !raiz.vivo; text: "Solo un tramo"; checked: raiz.pide; onToggled: if (checked) raiz.pide = true }
        Item { Layout.fillWidth: true }
    }
    ColumnLayout {
        Layout.fillWidth: true
        visible: raiz.quiere && raiz.escala !== null
        spacing: Kirigami.Units.smallSpacing
        Flow {
            Layout.fillWidth: true
            visible: raiz.vivo
            spacing: Kirigami.Units.smallSpacing
            QQC2.Label { text: "Atajos:"; color: Kirigami.Theme.disabledTextColor; height: implicitHeight }
            Repeater {
                model: [5, 15, 30]
                QQC2.Button { text: "Los últimos " + modelData + " min"; onClicked: raiz.escribir(Math.max(raiz.escala[0], raiz.escala[1] - modelData * 60), raiz.escala[1]) }
            }
        }
        QQC2.RangeSlider {
            id: barra
            Layout.fillWidth: true
            from: raiz.escala ? raiz.escala[0] : 0
            to: raiz.escala ? raiz.escala[1] : 1
            stepSize: 1
            // `to` en la expresión: al llegar la escala, el valor se recalcula (si no, quedaría recortado a la escala vieja)
            first.value: raiz.actual && to > from ? raiz.actual[0] : from
            second.value: raiz.actual && to > from ? raiz.actual[1] : to
            first.onMoved: raiz.escribir(first.value, second.value)
            second.onMoved: raiz.escribir(first.value, second.value)
            Accessible.name: "Tramo: de " + raiz.formato(first.value) + " a " + raiz.formato(second.value)
        }
        RowLayout {
            Layout.fillWidth: true
            QQC2.Label { text: raiz.escala ? raiz.formato(raiz.escala[0]) : ""; color: Kirigami.Theme.disabledTextColor }
            Item { Layout.fillWidth: true }
            QQC2.Label { text: raiz.escala ? raiz.formato(raiz.escala[1]) + (raiz.vivo ? " (ahora)" : "") : ""; color: Kirigami.Theme.disabledTextColor }
        }
        Flow {
            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing
            RowLayout {
                spacing: Kirigami.Units.smallSpacing
                QQC2.Label { text: raiz.vivo ? "Desde las" : "Desde" }
                QQC2.TextField {
                    id: desde
                    text: raiz.actual ? raiz.formato(raiz.actual[0]) : ""
                    placeholderText: raiz.vivo ? "HH:MM:SS" : "H:MM:SS"
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 5.5
                    Accessible.name: "Inicio del tramo"
                    onEditingFinished: if (raiz.valido(text) && raiz.valido(hasta.text)) raiz.h.fijarValor(raiz.p.clave, raiz.vivo ? "@" + text + "-@" + hasta.text : text + "-" + hasta.text)
                }
            }
            RowLayout {
                spacing: Kirigami.Units.smallSpacing
                QQC2.Label { text: raiz.vivo ? "hasta las" : "hasta" }
                QQC2.TextField {
                    id: hasta
                    text: raiz.actual ? raiz.formato(raiz.actual[1]) : ""
                    placeholderText: raiz.vivo ? "HH:MM:SS" : "H:MM:SS"
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 5.5
                    Accessible.name: "Fin del tramo"
                    onEditingFinished: if (raiz.valido(desde.text) && raiz.valido(text)) raiz.h.fijarValor(raiz.p.clave, raiz.vivo ? "@" + desde.text + "-@" + text : desde.text + "-" + text)
                }
            }
        }
        QQC2.Label {
            Layout.fillWidth: true
            visible: !!raiz.actual
            text: raiz.actual ? "Se bajarán " + raiz.reloj(raiz.actual[1] - raiz.actual[0]) + (raiz.vivo ? " (horas locales)" : "") : ""
            color: Kirigami.Theme.disabledTextColor
            wrapMode: Text.WordWrap
        }
    }
    QQC2.TextField {
        Layout.fillWidth: true
        visible: raiz.quiere && raiz.escala === null
        text: raiz.valor
        placeholderText: "1:02:00-1:05:30"
        Accessible.name: raiz.p.etiqueta || "Tramo"
        onEditingFinished: raiz.h.fijarValor(raiz.p.clave, text)
    }
    QQC2.Label {
        Layout.fillWidth: true
        visible: raiz.quiere && raiz.escala === null
        text: raiz.p.ayuda || ""
        color: Kirigami.Theme.disabledTextColor
        wrapMode: Text.WordWrap
    }
}
