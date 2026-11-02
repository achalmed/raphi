// DialogoVigilar — las carpetas vigiladas: lo que llegue a una pasa por la receta elegida y queda en su subcarpeta
// «raphi»; vigilar una carpeta nueva y dejar de vigilar una.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

Kirigami.Dialog {
    id: dialogo
    readonly property var o: studio.operaciones
    title: "Carpetas vigiladas"
    preferredWidth: Kirigami.Units.gridUnit * 36
    standardButtons: Kirigami.Dialog.Close
    padding: Kirigami.Units.largeSpacing
    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        QQC2.Label { Layout.fillWidth: true; text: "Lo que aparezca en una carpeta vigilada pasa por la receta elegida y el resultado queda en su subcarpeta «raphi». Un archivo se procesa una sola vez, cuando dejó de crecer."; wrapMode: Text.WordWrap }
        Repeater {
            model: dialogo.o.vigiladas
            RowLayout {
                required property var modelData
                Layout.fillWidth: true
                Kirigami.Icon { source: "folder-sync"; implicitWidth: Kirigami.Units.iconSizes.smallMedium; implicitHeight: implicitWidth }
                QQC2.Label { Layout.fillWidth: true; text: modelData.carpeta + " → " + modelData.receta; elide: Text.ElideMiddle }
                QQC2.ToolButton { icon.name: "list-remove"; text: "Dejar de vigilar"; display: QQC2.AbstractButton.IconOnly; onClicked: dialogo.o.dejarDeVigilar(modelData.carpeta); Accessible.name: "Dejar de vigilar " + modelData.carpeta; QQC2.ToolTip.text: "Dejar de vigilar"; QQC2.ToolTip.visible: hovered }
            }
        }
        QQC2.Label { visible: dialogo.o.vigiladas.length === 0; text: "Ninguna carpeta vigilada."; color: Kirigami.Theme.disabledTextColor }
        Kirigami.Separator { Layout.fillWidth: true }
        Kirigami.FormLayout {
            Layout.fillWidth: true
            CampoRuta { id: carpeta; Kirigami.FormData.label: "Carpeta:"; Layout.fillWidth: true; titulo: "Carpeta que vigilar"; nombreAccesible: "Carpeta que vigilar" }
            QQC2.ComboBox { id: receta; Kirigami.FormData.label: "Receta:"; Layout.fillWidth: true; model: dialogo.o.recetasParaVigilar; textRole: "titulo"; valueRole: "id"; Accessible.name: "Receta" }
        }
        QQC2.Button {
            Layout.alignment: Qt.AlignRight
            text: "Vigilar"
            icon.name: "list-add"
            enabled: carpeta.texto !== "" && receta.currentIndex >= 0
            onClicked: { if (dialogo.o.vigilar(carpeta.texto, receta.currentValue)) carpeta.texto = "" }
        }
    }
}
