// ReproductorMedios — audio y vídeo en la vista previa, con QtMultimedia de QML (el plugin de ffmpeg del sistema). En
// archivo aparte: si el módulo faltara, la vista previa lo carga con un Loader y, al fallar, dice que no puede
// reproducir (el resto del studio sigue). Reproducir no escribe nada.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import QtMultimedia
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz
    property url fuente
    property bool video: false
    spacing: Kirigami.Units.smallSpacing

    function hms(ms) {
        const s = Math.max(0, Math.floor(ms / 1000))
        return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0")
    }

    MediaPlayer {
        id: reproductor
        source: raiz.fuente
        audioOutput: AudioOutput { id: salidaAudio }
        videoOutput: salidaVideo
    }
    onFuenteChanged: reproductor.stop()

    Item {
        Layout.fillWidth: true
        Layout.fillHeight: true
        VideoOutput {
            id: salidaVideo
            anchors.fill: parent
            visible: raiz.video
        }
        Kirigami.Icon {
            anchors.centerIn: parent
            visible: !raiz.video
            source: "audio-x-generic"
            implicitWidth: Kirigami.Units.iconSizes.enormous
            implicitHeight: implicitWidth
        }
    }
    QQC2.Label {
        Layout.fillWidth: true
        visible: reproductor.error !== MediaPlayer.NoError
        text: "No se puede reproducir: " + reproductor.errorString
        color: Kirigami.Theme.negativeTextColor
        wrapMode: Text.WordWrap
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        QQC2.ToolButton {
            icon.name: reproductor.playbackState === MediaPlayer.PlayingState ? "media-playback-pause" : "media-playback-start"
            text: reproductor.playbackState === MediaPlayer.PlayingState ? "Pausa" : "Reproducir"
            display: QQC2.AbstractButton.IconOnly
            enabled: reproductor.mediaStatus !== MediaPlayer.NoMedia && reproductor.mediaStatus !== MediaPlayer.InvalidMedia
            onClicked: reproductor.playbackState === MediaPlayer.PlayingState ? reproductor.pause() : reproductor.play()
            Accessible.name: text
        }
        QQC2.ToolButton { icon.name: "media-playback-stop"; text: "Detener"; display: QQC2.AbstractButton.IconOnly; onClicked: reproductor.stop(); Accessible.name: text }
        QQC2.Slider {
            Layout.fillWidth: true
            from: 0
            to: Math.max(1, reproductor.duration)
            value: reproductor.position
            enabled: reproductor.seekable
            onMoved: reproductor.position = value
            Accessible.name: "Posición"
        }
        QQC2.Label { text: raiz.hms(reproductor.position) + " / " + raiz.hms(reproductor.duration); font.family: Kirigami.Theme.fixedWidthFont.family }
        Kirigami.Icon { source: "audio-volume-medium"; implicitWidth: Kirigami.Units.iconSizes.small; implicitHeight: implicitWidth }
        QQC2.Slider { Layout.preferredWidth: Kirigami.Units.gridUnit * 5; from: 0; to: 1; value: salidaAudio.volume; onMoved: salidaAudio.volume = value; Accessible.name: "Volumen" }
    }
}
