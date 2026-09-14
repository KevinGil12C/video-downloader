# Changelog

Todas las notables modificaciones de este proyecto se documentan en este archivo. El formato se basa en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).

---

## [Unreleased]

### Added

- Esqueleto del proyecto Open Source: licencia MIT, documentación, CI, plantillas de issues/PR y dependabot.
- Scripts de instalación y mantenimiento para Windows en `scripts/` (install, start, test, update, uninstall).
- Backend FastAPI local: `app/` con configuración por entorno, seguridad (CORS local + validación de URLs), modelos Pydantic y endpoints `GET /api/health` y `GET /api/info`.
- `config.example.json` con las variables de entorno documentadas.
- Servicio de descarga (`app/services/downloader.py`) sobre yt-dlp: extracción de metadatos, selector de formato video/audio y calidad, hooks de progreso, inyectable para tests.
- Primeros tests unitarios (`tests/test_downloader.py`) con yt-dlp simulado, sin descargas reales.
- Ruff: sección isort con `app` como primer-party; pytest: `pythonpath = ["."]`.
- Servicio FFmpeg (`app/services/ffmpeg.py`): búsqueda del binario (proyecto/PATH), verificación y reporte de versión; `/api/info` expone `ffmpeg_available` y `ffmpeg_version`.
- Tests del servicio FFmpeg con `subprocess` simulado (`tests/test_ffmpeg.py`).
- Servicio Download manager (`app/services/manager.py`): cola en memoria con `DownloadRecord`, descargas en segundo plano con límite de concurrencia, cancelación cooperativa y borrado de historial.
- Endpoints de descargas en `app/backend/api/downloads.py`: `POST/GET /api/downloads`, `GET/DELETE /api/downloads/{id}` y `POST /api/downloads/{id}/cancel` (registrados en `create_app`).
- Tests del manager (ciclo de vida, cancelación, concurrencia) y del contrato HTTP de descargas con el manager sustituido por un stub.
- Sistema de progreso (`app/services/progress.py`): `ProgressEvent` y `ProgressHub` que retransmiten cambios de estado por WebSocket de forma segura desde hilos.
- Endpoint WebSocket `WS /ws/progress` (`app/backend/api/ws.py`): envía el estado actual al conectar y stream de actualizaciones (`download_id`, `status`, `progress`, `speed`, `eta`).
- El manager ahora captura y emite `speed`/`eta` formateados y admite un listener de actualizaciones (`set_update_listener`).
- Tests del hub de progreso y del stream WebSocket completo con fakes (`tests/test_progress.py`, `tests/test_progress_ws.py`).
- Shell de escritorio Eel (`app/desktop/main.py`): arranca el backend FastAPI en segundo plano (`UvicornThread`), inicializa `web/` y abre la ventana con Edge/Chrome; expone `get_app_info` y permite modo headless (`VD_BROWSER=false`).
- UI provisional de escritorio (`web/index.html`) con comprobación de estado del backend, que se reemplazará en la fase de frontend.
- Tests del shell: arranque/parada de uvicorn, info expuesta al UI y boot completo con `eel.start` simulado (`tests/test_desktop.py`).
- Frontend completo (`web/index.html`, `web/css/style.css`, `web/js/app.js`): formulario de descarga (URL, formato, calidad, subcarpeta opcional), lista de descargas con barra de progreso, velocidad, ETA, estado y errores, cancelación y borrado, actualización en tiempo real vía `WS /ws/progress` con sondeo HTTP como fallback, y comprobación del estado del backend (`/api/info`).
- El backend ahora sirve la UI estática en `/` (`StaticFiles`) y CORS incluye el origen de la ventana Eel (puerto API + 1); el JS resuelve la base del API vía `eel.get_app_info()` en escritorio con fallback al mismo origen.
- Tests del frontend: index y assets servidos, prioridad de rutas `/api` sobre estáticos, 404 y expansión CORS del origen de escritorio (`tests/test_frontend.py`).
- Extensión de navegador Manifest V3 (`extension/`): popup para enviar la URL de la pestaña activa o capturada (`content.js` inyectado) a `POST /api/downloads`, lista de descargas con progreso/cancelar/eliminar, página de opciones (`chrome.storage.sync`) y service worker que solo llama a los endpoints locales de la API.
- La extensión usa `host_permissions` solo hacia `127.0.0.1:8000`/`localhost:8000`; al no regirse por CORS, los orígenes `chrome-extension://` no se añaden a la allowlist del servidor (superficie mínima).
- Tests de la extensión: manifest MV3 válido, permisos y hosts locales, archivos referenciados presentes, endpoints coherentes con el backend y verificación de que un origen `chrome-extension://` no elude CORS (`tests/test_extension.py`).

### Changed
- Endurecimiento CORS: el middleware solo admite `GET/POST/DELETE/OPTIONS` con cabecera `Content-Type` y sin credenciales (`allow_credentials=False`).
- Nuevo `RejectDisallowedOrigin` (middleware más externo): toda petición HTTP con `Origin` no autorizada (incluido `Origin: null`) responde `403` antes de llegar a los routers, mitigando ataques tipo DNS rebinding; el WebSocket queda gobernado por las reglas de origen del navegador.
- `config.validate_host` rechaza `VD_HOST` que no sea loopback (`127.0.0.1`, `localhost`, `::1`): la API nunca se bindea a interfaces externas (`0.0.0.0`/`::`).
- Tests de CORS y binding: origen permitido reflejado, origen Eel, orígenes desautorizados (`403`), `Origin: null`, sin `Origin`, preflight permitido/denegado, sin credenciales, WS no bloqueado, extra de entorno y validación de host (`tests/test_cors.py`).
### Fixed
### Security