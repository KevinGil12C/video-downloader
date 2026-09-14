# Modelo de seguridad

Documento técnico sobre las decisiones de seguridad de **Video Downloader Local**.

---

## Principios

1. **Todo es local.** No existen servidores remotos involucrados en el procesamiento ni en las descargas.
2. **Superficie mínima.** La API escucha solo en `127.0.0.1`; no se expone a la red local ni a Internet.
3. **Menos permisos.** La extensión y la UI solicitan únicamente lo que necesitan.
4. **Sin secretos.** El proyecto no almacena credenciales, cookies ni tokens de servicios externos.

---

## Red

- FastAPI se ejecuta en `127.0.0.1` (loopleback) — nunca en `0.0.0.0`.
- Puerto configurable por entorno (`VD_PORT`, por defecto `8000`).
- El modo Desktop (Eel) usa el mismo backend local; no abre servidores adicionales.

## CORS

La aplicación define una **allowlist de orígenes**:

- `http://localhost` y `http://127.0.0.1` en el puerto de la API y en el puerto de la ventana Eel (API + 1).
- Orígenes extra explícitos vía `VD_ALLOWED_ORIGINS`.
- La **extensión MV3 no necesita CORS**: sus peticiones con `host_permissions` hacia la API local no se rigen por CORS, por lo que sus orígenes `chrome-extension://...` **no** se añaden a la allowlist.
- Cualquier petición con `Origin` no autorizada es rechazada por el navegador (reglas CORS).

La implementación valida la cabecera `Origin` en el middleware y **no** usa `allow_origin_regex=".*"`.

## Validación de entrada

### URLs

- `security.py` valida que la URL sea `http`/`https`, candidate con `urllib.parse`, rechaza esquemas no permitidos (`file`, `javascript`, `data`, etc.) y limita el largo.
- No se resuelven URLs con credenciales embebidas (`user:pass@host`).

### Nombres de archivo

- Sanitizados: se eliminan caracteres reservados de Windows (`<>:"/\|?*`), espacios finales y puntos.
- Se evitan rutas de salida (`..`) y nombres reservados (`CON`, `NUL`, etc.).

### Directorios

- El campo `directory` (opcional) debe ser una subcarpeta relativa dentro de `downloads/` sin componentes peligrosos.
- Se usa `resolve()`/`relative_to()` para prevenir *path traversal*.

## Descargas

- El motor yt-dlp se invoca con `--no-overwrites` y `--paths downloads/` fijo.
- No se pasan cookies del usuario al proceso.
- La cancelación termina el subproceso de descarga.
- Los archivos generados se mantienen bajo `downloads/` (ignorada por Git).

## Registros (logs)

- `logs/` contiene solo información operativa (coordenadas de descarga, errores).
- **Regla:** nunca se registran URLs con credenciales, cookies, tokens ni contenido de los archivos.

## Extensión de navegador

- Permisos mínimos (`activeTab`, `scripting`, `storage`, `host_permissions` solo para localhost).
- Sin `webRequest` global ni acceso a cookies.
- La captura de la URL usa `content.js` sobre la pestaña donde el usuario accionó la extensión.

## Gestión del riesgo

- **Ataque desde una web maliciosa en el mismo navegador**: mitigado por CORS strict y auth por `Origin`; la API responde pero el navegador bloquea la lectura.
  - Recomendación: la API debería exigir un **token local** opcional para descargas en versiones futuras (fuera del alcance de v0.1).
- **Ataque de origen local (otro proceso en la misma máquina)**: en Windows se mitiga encauciendo solicitudes por `Origin` y, en futuras versiones, mediante un token aleatorio.
- **Path traversal**: bloqueado por sanitización y resolución de rutas.
- **Comandos maliciosos**: yt-dlp se invoca por lista de argumentos (no por shell string).

Ver también [SECURITY.md](../SECURITY.md) para la política de reporte de vulnerabilidades.