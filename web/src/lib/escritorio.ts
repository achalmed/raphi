/**
 * El puente con Raphi escritorio (R4). En el navegador no existe y todo funciona con subir y descargar; dentro de la
 * ventana del escritorio, `window.raphiEscritorio` (QWebChannel) da lo que un navegador no puede: elegir archivos del
 * disco por su ruta, abrir una carpeta, guardar en una carpeta elegida, vigilar carpetas y avisar al sistema.
 *
 * La web pregunta `hayEscritorio()` y ofrece esas opciones solo si está: ninguna pantalla existe solo en el escritorio.
 */
export interface PuenteEscritorio {
  elegirArchivos(filtro: string): Promise<string[]>
  elegirCarpeta(): Promise<string | null>
  abrirCarpeta(ruta: string): Promise<void>
  abrirArchivo(ruta: string): Promise<void>
  copiarA(rutas: string[], carpeta: string): Promise<string[]>
  vigilar(carpeta: string, receta: string): Promise<boolean>
  dejarDeVigilar(carpeta: string): Promise<boolean>
  vigiladas(): Promise<{ carpeta: string; receta: string }[]>
  menusDolphin(instalar: boolean): Promise<boolean>
  hayMenusDolphin(): Promise<boolean>
  notificar(titulo: string, texto: string): Promise<void>
}

declare global {
  interface Window {
    raphiEscritorio?: PuenteEscritorio
    /** Rutas soltadas sobre la ventana: el escritorio las anuncia con este evento (las de un navegador son File). */
    raphiRutasSoltadas?: string[]
  }
}

export const hayEscritorio = (): boolean => typeof window !== 'undefined' && Boolean(window.raphiEscritorio)
export const puente = (): PuenteEscritorio | undefined => (typeof window !== 'undefined' ? window.raphiEscritorio : undefined)

/** El evento con que el escritorio entrega rutas soltadas (de Dolphin, del escritorio de Plasma o de su menú). */
export const EVENTO_RUTAS = 'raphi:rutas'
