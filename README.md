# Monitor de licitaciones públicas · Demo

> **Demo con datos simulados:** no consulta portales reales ni usa modelos de IA en vivo.

Versión pública y autocontenida de un sistema que monitorea convocatorias de licitaciones públicas
federales de México para **servicios de seguridad privada**. Esta demo reproduce la experiencia de uso
del sistema real con un dataset 100% sintético: sirve para mostrar el flujo y la interfaz sin exponer
documentos, clientes ni la forma en que el sistema real obtiene la información.

Diseño y desarrollo: [Alan Mendoza](https://portafolio-ki87.vercel.app)

---

## Qué hace el sistema real (a alto nivel)

1. **Busca** las convocatorias vigentes de la partida de servicios de vigilancia en el portal
   gubernamental de compras públicas.
2. **Descarga** los anexos de cada expediente (convocatoria, anexo técnico, modelo de contrato, actas…).
3. **Clasifica** cada PDF como *con texto* o *escaneado* según la cantidad de caracteres por página.
4. Aplica **OCR solo donde hace falta** (los escaneados) y extrae texto de PDF, Word y otros formatos.
5. Genera una **ficha técnica** por expediente (aspectos técnicos, legales y económicos, evaluación de
   factibilidad, puntos críticos y citas verificables) validada con un esquema **Pydantic**, usando
   adaptadores intercambiables de modelos de lenguaje.
6. Ofrece una **UI en Streamlit** y una **CLI** para consultar expedientes, fichas y correr el pipeline.

## Qué incluye esta demo

| Vista | Qué muestra |
|---|---|
| **Panorama** | Filtros por entidad, dependencia, fecha de apertura y monto; métricas y tabla de expedientes. Al seleccionar una fila se abre su detalle. |
| **Detalle** | Documentos del expediente con badge *Texto* / *Escaneado · OCR*, texto extraído (sintético) y la ficha técnica en pestañas **Técnica / Legal / Económica**, con puntos críticos, citas y descarga en Markdown. |
| **Simular corrida** | Botón que anima las etapas del pipeline con `st.status` y `st.progress`, usando temporizadores sobre los datos locales. Está rotulado como simulación. |
| **Gráficas** | Documentos por expediente, texto vs escaneado por tipo de documento y tiempos simulados de procesamiento por etapa. |

**Lo que NO hace:** no hay scraping, ni OCR real, ni llamadas a APIs de IA, ni claves, ni variables de
entorno. En ejecución no hace ninguna petición de red fuera del propio servidor de Streamlit.

### Uso de recursos

- El dataset se lee y valida **una sola vez** con `st.cache_data`; las tablas derivadas también se cachean.
- La navegación usa un único `st.segmented_control`: en cada rerun solo se ejecuta la vista activa.
- El detalle construye **solo el expediente seleccionado** y, dentro de la ficha, **solo la pestaña
  abierta** (`st.tabs(on_change="rerun")` + `.open`). Los expanders pesados también son perezosos.
- Las gráficas solo se construyen al abrir su vista. El Markdown se genera recién al pulsar *Descargar*.
- La simulación corre únicamente al pulsar el botón: sin autoplay ni bucles en segundo plano.
- No hay imágenes ni fuentes empaquetadas en el repositorio.

## Datos simulados

Todo vive en `demo_data/` y fue escrito para la demo:

| Archivo | Contenido |
|---|---|
| `expedientes.json` | 15 expedientes con ID `DEMO-…`, dependencias marcadas como *(ficticio/ficticia)*, fechas de 2026, montos, guardias, turnos y de 3 a 7 documentos cada uno (tipo, páginas, texto o escaneado, tiempos simulados). |
| `textos.json` | Fragmentos de texto extraído por documento, redactados desde cero. |
| `fichas.json` | Una ficha técnica precalculada por expediente, con los mismos campos del esquema del sistema real. En la UI se rotula como *Ficha de ejemplo precalculada para la demo*. |

Al arrancar, la app valida los tres archivos con Pydantic (`monitor_demo/datos.py` y
`monitor_demo/esquemas.py`): tipos, prefijo `DEMO-`, marca de ficticio, coherencia de fechas, umbral de
texto/escaneado y que cada cita literal exista en el texto del documento que menciona. Si algo falla,
muestra un error claro con la lista de problemas en lugar de la app.

## Stack

- Python 3.12+
- [Streamlit](https://streamlit.io) 1.64 (UI, caché, estado)
- [Pydantic](https://docs.pydantic.dev) 2 (esquemas y validación)
- [pandas](https://pandas.pydata.org) 3 (tablas)
- [Altair](https://altair-viz.github.io) 6 (gráficas)

## Estructura

```
.
├── streamlit_app.py          # Punto de entrada: banner, navegación y ruteo de vistas
├── requirements.txt          # Dependencias fijadas
├── .streamlit/config.toml    # Tema oscuro con acento azul, sin métricas de uso
├── demo_data/                # Dataset sintético (JSON)
└── monitor_demo/
    ├── esquemas.py           # Modelos Pydantic de la ficha técnica
    ├── datos.py              # Modelos del dataset + carga y validación
    ├── consultas.py          # Consultas cacheadas con st.cache_data
    ├── markdown.py           # Ficha → Markdown (generado localmente)
    ├── ui.py                 # Estilos, banner, formatos y badges
    └── vistas/               # panorama, detalle, simulacion, graficas
```

## Ejecutar localmente

```bash
python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Abrí <http://localhost:8501>. La configuración oculta el mensaje de bienvenida de Streamlit (que en modo
*headless* consulta la IP pública de la máquina), por eso la terminal no imprime la URL.

Enlaces directos: `?vista=detalle&id=DEMO-2026-0103`, `?vista=simular`, `?vista=graficas`.

## Desplegar en Streamlit Community Cloud

1. Subí este repositorio a GitHub (puede ser público).
2. Entrá a <https://share.streamlit.io> y elegí **Continue with GitHub** para iniciar sesión.
   La primera vez, autorizá a Streamlit a leer tus repositorios.
3. Hacé clic en **Create app** (en versiones anteriores del panel, **New app**) y elegí la opción de
   desplegar una app desde un repositorio de GitHub.
4. Completá el formulario:
   - **Repository:** `tu-usuario/demo-monitor-licitaciones`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
   - **App URL** (opcional): un subdominio a elección.
5. En **Advanced settings** elegí **Python 3.12** o superior. No hace falta cargar *secrets*.
6. Pulsá **Deploy**. Community Cloud instala `requirements.txt` y publica la app; cada `git push` a `main`
   la actualiza automáticamente.

## Créditos

Diseño y desarrollo: [Alan Mendoza](https://portafolio-ki87.vercel.app).
Los nombres de dependencias, sedes, montos, textos y fichas de esta demo son ficticios.
