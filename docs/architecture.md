# Arquitectura

Este documento describe los componentes de **Video Downloader Local** y cómo fluyen los datos entre ellos.

---

## Visión general

La aplicación ofrece dos modos de uso con el **mismo backend local**:

```
Modo Desktop                Modo Browser
-----------                 -------------
Eel (Chromium + HTML/JS)    Browser → Extension (MV3) → localhost
        │                                                    │
        └───────────────▶ FastAPI (127.0.0.1:8000) ◀─────────┘
                                │
                        Download Service
                                │
                          yt-dlp / FFmpeg
                                │
                         Archivos locales
                        (downloads/ + logs/)
```

En ambos modos el trabajo pesado lo hace el backend Python local. No hay servidores remotos.

---

## Componentes

### 1. Backend Python (`app/backend/`)

- **`server.py`** — crea y configura la aplicación FastAPI (CORS, routers, arranque).
- **`config.py`** — configuración central: puerto, host, carpetas, límites. Cargada desde variables de entorno y `config.example.json`.
- **`security.py`** — validación de URLs, sanitización de nombres de archivo, CORS y bind de `127.0.0.1`.
- **`models.py`** — modelos Pydantic de los contratos de la API.
- **`api/`** — routers:
  - `health.py` → `GET /api/health`
  - `info.py` → `GET /api/info`
  - `downloads.py` → CRUD y control de descargas.

### 2. Servicios (`app/services/`)

- **`downloader.py`** — orquesta descargas con yt-dlp.
- **`ffmpeg.py`** — localiza y verifica el binario FFmpeg (mezcla de audio/video, conversión).
- **`progress.py`** — estado y progreso de cada descarga (pendiente, descargando, finalizada, error, cancelada).

### 3. Desktop (`app/desktop/main.py`)

Punto de entrada del **modo Desktop**: arranca FastAPI en un hilo y abre la ventana Eel apuntando al frontend (`web/`).

### 4. Frontend (`web/`)

HTML + CSS + JavaScript (Tailwind CSS + Material Icons, mobile-first):

- `index.html`
- `css/app.css`
- `js/api.js` — cliente HTTP del API localhost.
- `js/downloads.js` — lógica de descargas (lista, estados, cancelación).
- `js/ui.js` — renderizado y UX.
- `js/app.js` — bootstrap de la aplicación.

### 5. Extensión (`extension/`)

Extensión Manifest V3 (Chrome / Brave / Edge):

- `manifest.json` — permisos mínimos (solo URL de la pestaña activa + acceso a localhost).
- `background.js` — comunicación con `localhost`.
- `content.js` — captura de la URL del video en la página.
- `popup.html` / `popup.js` — UI de la extensión.

---

## Flujo de una descarga

1. El usuario envía una URL (desde la UI Eel o desde la extensión).
2. `api/downloads.py` valida la URL (`security.py`).
3. `downloader.py` crea el trabajo y lanza yt-dlp.
4. `progress.py` registra el progreso en tiempo real.
5. Si es necesario, `ffmpeg.py` mezcla/secuencia audio-video.
6. El archivo se guarda localmente en `downloads/`.
7. El estado se notifica por WebSocket (o polling) a la UI.

---

## Estructura de carpetas

```
video-downloader/
├── app/backend/        # FastAPI (config, security, models, api/)
├── app/services/       # downloader, ffmpeg, progress
├── app/desktop/        # punto de entrada Eel
├── web/                # frontend (HTML/CSS/JS)
├── extension/          # browser extension (MV3)
├── scripts/            # instalación y arranque (Windows)
├── tests/              # pytest (sin descargas reales)
├── docs/               # documentación técnica
├── downloads/          # salida de descargas (ignorada en Git)
└── logs/               # logs de la aplicación (ignorada en Git)
```

---

## Decisiones de arquitectura

| Decisión | Justificación |
|----------|---------------|
| Backend Python en `127.0.0.1` | Privacidad: todo local; nada expuesto a la red o Internet |
| Mismo API para Desktop y Browser | Una sola fuente de verdad; la extensión y Eel comparten contrato |
| yt-dlp + FFmpeg | Estándar de facto, activo y auditado para extracción y procesado |
| Pydantic para contratos | Validación estricta de entrada/salida |
| Eel sobre Electron | Ligero, Python nativo, sin distribuir Chromium completo por separado |
| Extension MV3 | API moderna de Chrome; permisos mínimos y declarados |

Ver también [security.md](security.md) y [api.md](api.md).