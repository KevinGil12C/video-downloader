# API documentación

Documento de referencia del API localhost de **Video Downloader Local**.

- Base URL: `http://127.0.0.1:8000`
- Formato: JSON
- Autenticación: **no requiere autenticación** (solo escucha en `127.0.0.1`)
- Interactivo: `GET /docs` (Swagger UI) cuando el servidor está activo

> Los endpoints que se listan forman parte del contrato previsto. Se implementan en las correspondientes fases del backend.

---

## Health

### `GET /api/health`

Comprueba que el servicio está activo.

**Respuesta `200`**

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

## Info

### `GET /api/info`

Devuelve el estado del entorno: versión de la aplicación, presencia de yt-dlp y FFmpeg.

**Respuesta `200`**

```json
{
  "version": "0.1.0",
  "yt_dlp_version": "2024.12.13",
  "ffmpeg_available": true,
  "downloads_dir": "C:\\...\\downloads",
  "platform": "Windows"
}
```

---

## Descargas

### `POST /api/downloads`

Crea una nueva descarga.

**Cuerpo**

```json
{
  "url": "https://example.com/video",
  "format": "video",        // "video" | "audio"
  "quality": "best",        // "best" | "1080" | "720" | "480" | "360" ...
  "directory": null         // opcional, subcarpeta dentro de downloads/
}
```

**Validación**

- `url` debe ser http/https válida (ver `security.py`).
- `format` y `quality` deben estar dentro de los valores permitidos.
- `directory` debe ser una subruta segura sin `..` ni caracteres reservados.

**Respuesta `201`**

```json
{
  "id": "uuid-de-la-descarga",
  "url": "https://example.com/video",
  "status": "pending",
  "progress": 0,
  "created_at": "2026-01-01T00:00:00Z"
}
```

**Errores**: `400` URL/parámetros inválidos.

---

### `GET /api/downloads`

Lista el historial de descargas.

**Respuesta `200`**

```json
{
  "items": [
    {
      "id": "uuid",
      "url": "https://example.com/video",
      "status": "completed",
      "progress": 100,
      "file": "video-title.mp4",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:05:00Z"
    }
  ]
}
```

**Estados posibles**

`pending` · `downloading` · `processing` · `completed` · `error` · `cancelled`

---

### `GET /api/downloads/{download_id}`

Detalle de una descarga.

**Respuesta `200`**: mismo esquema que el ítem anterior.
**Errores**: `404` si no existe.

---

### `DELETE /api/downloads/{download_id}`

Elimina la descarga (y su archivo si está completada) del historial.

**Respuesta `204`** sin contenido.
**Errores**: `404` si no existe, `409` si está en curso.

---

### `POST /api/downloads/{download_id}/cancel`

Cancela una descarga en curso.

**Respuesta `200`**

```json
{ "id": "uuid", "status": "cancelled" }
```

**Errores**: `404` si no existe, `400` si no se puede cancelar.

---

## Progreso en tiempo real

### `WS /ws/progress`

WebSocket opcional para recibir eventos de progreso sin polling.

**Evento (JSON)**

```json
{
  "download_id": "uuid",
  "status": "downloading",
  "progress": 42.5,
  "speed": "1.2 MiB/s",
  "eta": "00:01:30"
}
```

> Si el WebSocket no está disponible, la UI puede hacer polling contra `GET /api/downloads/{id}`.

---

## CORS

La API restringe CORS a:

- Orígenes `http://localhost:*` y `http://127.0.0.1:*`.
- Extensiones de navegador locales (Chrome/Brave/Edge): `chrome-extension://*`, `brave://*`, `edge://*` (o el patrón de origin de la extensión instalada, ver [security.md](security.md)).

Cualquier otro origen no autorizado recibirá el bloqueo CORS del navegador.