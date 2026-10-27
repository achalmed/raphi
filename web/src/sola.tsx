/**
 * Raphi SOLA en el navegador, y la página que muestra Raphi escritorio: la cáscara mínima de Tiqsi con el módulo web
 * de Raphi, contra raphi.sola o raphi.escritorio. No importa nada de Qillqa. Se construye con `npm run web:construir`.
 */
import { createRoot } from 'react-dom/client'
import { CascaronMinimo } from '@qillqa/tiqsi/minimo'
import { RAPHI } from './modulo'

createRoot(document.getElementById('root')!).render(<CascaronMinimo modulo={RAPHI} />)
