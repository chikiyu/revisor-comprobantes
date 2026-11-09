import { useEffect, useState } from 'react'
import './App.css'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function pedirComprobantes() {
  const respuesta = await fetch(`${API}/comprobantes`)
  if (!respuesta.ok) throw new Error('No se pudo cargar la lista')
  return respuesta.json()
}

export default function App() {
  const [comprobantes, setComprobantes] = useState([])
  const [subiendo, setSubiendo] = useState(false)
  const [errores, setErrores] = useState([])

  // Se ejecuta una vez, al abrir la página
  useEffect(() => {
    pedirComprobantes()
      .then(setComprobantes)
      .catch((e) => setErrores([e.message]))
  }, [])

  async function subir(evento) {
    const archivos = [...evento.target.files]
    evento.target.value = '' // para poder elegir el mismo archivo otra vez
    setSubiendo(true)
    setErrores([])

    const nuevosErrores = []
    for (const archivo of archivos) {
      const formulario = new FormData()
      formulario.append('archivo', archivo)
      try {
        const respuesta = await fetch(`${API}/comprobantes`, { method: 'POST', body: formulario })
        if (!respuesta.ok) {
          const cuerpo = await respuesta.json()
          nuevosErrores.push(`${archivo.name}: ${cuerpo.detail}`)
        }
      } catch {
        nuevosErrores.push(`${archivo.name}: no se pudo conectar con el servidor`)
      }
    }

    setErrores(nuevosErrores)
    setSubiendo(false)
    setComprobantes(await pedirComprobantes())
  }

  const observados = comprobantes.filter((c) => c.estado === 'observado').length

  return (
    <main>
      <h1>Revisor de comprobantes</h1>
      <p className="ayuda">
        Sube facturas en PDF. La IA extrae los datos y las reglas contables revisan RUC, IGV y totales.
      </p>

      <div className="acciones">
        <label className={`boton ${subiendo ? 'desactivado' : ''}`}>
          {subiendo ? 'Revisando…' : 'Subir PDF'}
          <input type="file" accept="application/pdf" multiple hidden disabled={subiendo} onChange={subir} />
        </label>
        <a className="boton secundario" href={`${API}/comprobantes/export.csv`}>Exportar CSV</a>
        <span className="resumen">
          {comprobantes.length} comprobantes · {observados} observados
        </span>
      </div>

      {errores.map((e) => <p className="error" key={e}>{e}</p>)}

      <div className="tabla">
        <table>
          <thead>
            <tr>
              <th>Estado</th><th>Emisor</th><th>Serie</th><th>Fecha</th>
              <th>Categoría</th><th className="monto">Total</th><th>Observaciones</th>
            </tr>
          </thead>
          <tbody>
            {comprobantes.map((c) => (
              <tr key={c.id} className={c.estado}>
                <td><span className={`etiqueta ${c.estado}`}>{c.estado}</span></td>
                <td>{c.razon_social}<small>RUC {c.ruc_emisor}</small></td>
                <td>{c.serie_numero}</td>
                <td>{c.fecha}</td>
                <td>{c.categoria}</td>
                <td className="monto">{c.moneda} {c.total}</td>
                <td>{c.observaciones.join(' · ') || '—'}</td>
              </tr>
            ))}
            {comprobantes.length === 0 && (
              <tr><td colSpan="7" className="vacio">Todavía no hay comprobantes.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  )
}
