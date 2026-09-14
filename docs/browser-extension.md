# Extensión de navegador

Guía de instalación, permisos y funcionamiento de la extensión (carpeta `extension/`).

---

## Compatibilidad

- **Google Chrome**
- **Brave**
- **Microsoft Edge**
- Cualquier navegador compatible con WebExtensions / Manifest V3 (base Chromium)

## Permisos

La extensión solicita **únicamente** los permisos necesarios:

| Permiso | Motivo |
|---------|--------|
| `activeTab` | Leer la URL de la pestaña activa |
| `scripting` | Inyectar el capturador de video en la página |
| `host_permissions` | `http://127.0.0.1:8000/*` y `http://localhost:8000/*` — comunicarse con la API local |
| `storage` | Guardar configuración local de la extensión (sin datos sensibles) |

No solicita permisos de: navegación, cookies, lectura del historial ni acceso genérico a todos los sitios.

---

## Instalación en modo desarrollador

### Chrome

1. Abre `chrome://extensions`.
2. Activa **Modo de desarrollador** (arriba a la derecha).
3. Pulsa **Cargar descomprimida** → selecciona la carpeta `extension/`.
4. La extensión aparece en la barra de herramientas.

### Brave

1. Abre `brave://extensions`.
2. Activa **Modo de desarrollador**.
3. **Cargar descomprimida** → selecciona `extension/`.

> **No es necesario** desactivar Shields, CORS ni usar `--disable-web-security`. El flujo funciona con permisos de extensión + API localhost + CORS correcto.

### Edge

1. Abre `edge://extensions`.
2. Activa **Modo de desarrollador** (en el panel lateral).
3. **Cargar descomprimida** → selecciona `extension/`.

---

## Funcionamiento

1. La API localhost debe estar ejecutándose (`scripts\start.bat` o `python -m app.desktop.main`).
2. Abre un video en una pestaña.
3. Pulsa el icono de la extensión.
4. La extensión captura la URL del video (`content.js`), la envía a `http://127.0.0.1:8000/api/downloads` (`background.js`) y muestra el estado en el popup (`popup.html`/`popup.js`).
5. El archivo se descarga localmente en `downloads/`.

### Comunicación con localhost

- La extensión realiza peticiones `fetch`/`XMLHttpRequest` con `host_permissions` sobre `127.0.0.1:8000`.
- El servidor local responde con cabeceras CORS correctas (ver [api.md](api.md#cors)).
- El API web no interveniene en el procesamiento de la propia web navegada.

---

## Permisos en Brave / Shields

Brave Shields bloquea rastreadores y scripts de terceros en las **páginas web**, pero no bloquea el tráfico de una **extensión** con `host_permissions` hacia `localhost`, siempre que el API responda con las cabeceras CORS y `Origin` adecuadas.

Si la extensión no conecta:

1. Verifica que la API está corriendo (curl `http://127.0.0.1:8000/api/health`).
2. Verifica que la versión de la extensión coincide con la configuración de CORS del servidor.
3. Consulta [troubleshooting.md](troubleshooting.md) → *Extensión no conecta con localhost*.

---

## Implementación

- `manifest.json` — definición Manifest V3, permisos y scripts.
- `background.js` — service worker: recibe la acción, llama al API local.
- `content.js` — detecta el elemento de video en la página y extrae su URL.
- `popup.html` / `popup.js` — interfaz mínima de la extensión.
- `icons/` — iconos 16/32/48/128 px.

Ver también [architecture.md](architecture.md) → Extensión.