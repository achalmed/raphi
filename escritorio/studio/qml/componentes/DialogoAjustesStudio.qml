// DialogoAjustesStudio — «Configurar Raphi Studio…»: qué hacer con lo que llega, la terminal y el intérprete del motor.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard
import GuiComun

DialogoAjustes {
    id: dialogo
    title: "Configurar Raphi Studio"
    readonly property var a: studio.ajustes
    modulos: [{ titulo: "General", icono: "configure", pagina: paginaGeneral }]
    onGuardado: { dialogo.a.guardar(); ventana.mensajes.mostrar("Preferencias guardadas.", "positivo") }

    Component {
        id: paginaGeneral
        ColumnLayout {
            function guardar() { dialogo.a.filtrarAlRecibir = filtrar.checked; dialogo.a.terminal = terminal.text }
            FormCard.FormHeader { title: "Lo que llega" }
            FormCard.FormCard {
                FormCard.FormCheckDelegate { id: filtrar; text: "Al soltar archivos, dejar la tabla con las herramientas que los aceptan"; checked: dialogo.a.filtrarAlRecibir; description: "Si solo una sirve, queda elegida. Ver › Solo las que aceptan los archivos lo quita." }
            }
            FormCard.FormHeader { title: "El motor" }
            FormCard.FormCard {
                FormCard.FormTextDelegate { text: "El motor corre como proceso con " + dialogo.a.interpreteMotor + (dialogo.a.hayVenv ? " (el .venv del repo)." : ". No existe el .venv del repo: Herramientas › El entorno del motor… dice cómo crearlo.") }
            }
            FormCard.FormHeader { title: "Sistema" }
            FormCard.FormCard {
                FormCard.FormTextFieldDelegate { id: terminal; label: "Terminal para «Abrir terminal aquí»"; text: dialogo.a.terminal; placeholderText: "konsole" }
            }
        }
    }
}
