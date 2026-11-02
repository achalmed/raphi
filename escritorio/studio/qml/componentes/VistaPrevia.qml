// VistaPrevia — lo que muestra el monitor del espacio de trabajo (reingeniería X4), del controlador studio.vista: una
// imagen, un PDF página a página (pdftoppm, por demanda), audio o vídeo (ReproductorMedios, con QtMultimedia), un
// texto (subtítulos, Markdown, una transcripción) o, si no hay nada que mostrar, qué es y cómo abrirlo. Solo lee.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.Control {
    id: raiz
    readonly property var v: studio.vista
    property string vacio: "Elige una entrada o una salida para verla aquí"
    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    Accessible.name: "Vista previa"
    background: Rectangle { color: Kirigami.Theme.alternateBackgroundColor }

    contentItem: ColumnLayout {
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            visible: raiz.v.ruta !== ""
            spacing: Kirigami.Units.smallSpacing
            QQC2.Label { text: raiz.v.nombre; font.weight: Font.DemiBold; elide: Text.ElideMiddle; Layout.maximumWidth: raiz.width * 0.5 }
            QQC2.Label { text: raiz.v.descripcion; color: Kirigami.Theme.disabledTextColor; elide: Text.ElideRight; Layout.fillWidth: true }
            BotonAccion { accion: studio.acciones.accion("archivo.abrir"); conTexto: false }
            BotonAccion { accion: studio.acciones.accion("archivo.mostrar"); conTexto: false }
        }
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: ["imagen", "pdf", "audio", "video", "texto"].indexOf(raiz.v.tipo) + 1

            Kirigami.PlaceholderMessage {                                  // 0 · nada
                icon.name: raiz.v.ruta === "" ? "view-preview" : raiz.v.tipo === "carpeta" ? "folder" : "unknown"
                text: raiz.v.ruta === "" ? "Vista previa" : raiz.v.tipo === "carpeta" ? "Una carpeta" : "Sin vista previa"
                explanation: raiz.v.ruta === "" ? raiz.vacio : "Ábrelo con su aplicación o muéstralo en Dolphin (los botones de arriba)."
            }
            Image {                                                        // 1 · imagen
                source: raiz.v.tipo === "imagen" ? raiz.v.url : ""
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                cache: false
                sourceSize.width: Math.max(64, width * 2)
                Accessible.name: "Imagen: " + raiz.v.nombre
            }
            ListView {                                                     // 2 · PDF
                id: paginas
                clip: true
                model: raiz.v.paginas
                spacing: Kirigami.Units.largeSpacing
                topMargin: Kirigami.Units.largeSpacing
                bottomMargin: Kirigami.Units.largeSpacing
                Accessible.name: "Páginas del PDF"
                QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
                delegate: Item {
                    id: hoja
                    required property var model
                    // la proporción de la imagen ya renderizada manda: pdfinfo da el tamaño sin la rotación de la página
                    readonly property real proporcion: lienzo.status === Image.Ready && lienzo.implicitWidth > 0 ? lienzo.implicitHeight / lienzo.implicitWidth
                                                                                                                 : model.alto / model.ancho
                    width: paginas.width
                    height: (paginas.width - Kirigami.Units.gridUnit * 2) * proporcion
                    Component.onCompleted: raiz.v.pedir(model.pagina)
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: paginas.width - Kirigami.Units.gridUnit * 2
                        height: parent.height
                        color: Kirigami.Theme.backgroundColor
                        border.color: Kirigami.Theme.disabledTextColor
                        border.width: 1
                        Image { id: lienzo; anchors.fill: parent; anchors.margins: 1; source: hoja.model.imagen; asynchronous: true; fillMode: Image.PreserveAspectFit; mipmap: true }
                        QQC2.BusyIndicator { anchors.centerIn: parent; running: hoja.model.imagen === ""; visible: running }
                        QQC2.Label { anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: Kirigami.Units.smallSpacing; text: hoja.model.pagina; font: Kirigami.Theme.smallFont; color: Kirigami.Theme.disabledTextColor }
                    }
                }
            }
            Loader {                                                       // 3 · audio
                active: raiz.v.tipo === "audio"
                source: "ReproductorMedios.qml"
                onLoaded: { item.video = false; item.fuente = Qt.binding(() => raiz.v.url) }
                onStatusChanged: if (status === Loader.Error) sinMedios.visible = true
            }
            Loader {                                                       // 4 · vídeo
                active: raiz.v.tipo === "video"
                source: "ReproductorMedios.qml"
                onLoaded: { item.video = true; item.fuente = Qt.binding(() => raiz.v.url) }
                onStatusChanged: if (status === Loader.Error) sinMedios.visible = true
            }
            VistaTexto {                                                   // 5 · texto
                texto: raiz.v.texto
                markdown: raiz.v.nombre.toLowerCase().endsWith(".md")
                ajustarLineas: true
                nombreAccesible: "Texto de " + raiz.v.nombre
            }
        }
        Kirigami.InlineMessage {
            id: sinMedios
            Layout.fillWidth: true
            visible: false
            type: Kirigami.MessageType.Warning
            text: "Este sistema no tiene el módulo QtMultimedia de QML: el audio y el vídeo no se pueden reproducir aquí (ábrelos con su aplicación)."
        }
    }
}
