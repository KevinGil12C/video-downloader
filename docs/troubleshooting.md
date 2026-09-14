# Troubleshooting

Problemas comunes y sus soluciones.

---

## 1. FFmpeg no encontrado

**Síntoma**

```
FFmpeg not found. Install it or add it to PATH.
```

**Solución**

1. Descarga FFmpeg desde https://ffmpeg.org/download.html.
2. Extrae el zip.
3. Opción A: añade la carpeta `bin/` de FFmpeg al `PATH` de Windows.
4. Opción B: colócalo en `bin/ffmpeg/ffmpeg.exe` dentro del proyecto.

**Verificar**

```bat
ffmpeg -version
```

---

## 2. Error con `pip` al instalar dependencias

**Síntoma**

Error al instalar una o varias dependencias.

**Solución**

1. Usa Python 3.10 o superior: `python --version`.
2. Crea un entorno virtual limpio:
   ```bat
   python -m venv venv
   venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Si falla una dependencia específica, instala el [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (componentes Python/native).

---

## 3. Puerto 8000 ocupado

**Síntoma**

```
[Errno 10048] error while attempting to bind on address ...
```

**Solución**

1. Encuentra quién usa el puerto:
   ```bat
   netstat -ano | findstr 8000
   ```
2. Cierra ese proceso o cambia el puerto en `config.example.json` / variable de entorno `VD_PORT`.

---

## 4. La extensión no conecta con localhost

1. Verifica que la API está activa:
   ```bat
   curl http://127.0.0.1:8000/api/health
   ```
2. Recarga la extensión (desmarcar y volver a marcar "desarrollador"/"load unpacked").
3. Confirma que el `host_permissions` incluye `http://127.0.0.1:8000/*`.
4. **Brave**: no desactives Shields; revisa los pasos de [browser-extension.md](browser-extension.md).

---

## 5. Error CORS al usar la UI web desde otra pestaña

- La API solo autoriza orígenes locales (`localhost`, `127.0.0.1`) y extensiones registradas.
- Asegúrate de abrir la UI desde `http://127.0.0.1:8000` (o servida por Eel), no desde `file://`.

---

## 6. yt-dlp obsoleto (`unsupported URL` o extracción errónea)

```bat
pip install -U yt-dlp
```

Si la plataforma cambia su sitio, actualizar yt-dlp suele resolverlo. Nunca uses tricks de la plataforma para saltar controles de acceso ni DRM.

---

## 7. Descarga falla con error de la plataforma

- Verifica que el enlace es correcto y accesible en tu navegador.
- Revisa los logs en `logs/` y adjúntalos al issue (sin datos sensibles).
- Los términos de servicio de la plataforma pueden limitar descargas; ver [Legal en el README](../README.md#legal-y-uso-responsable).

---

## 8. Propuesta para el servicio de descargas no inicia con el modo Desktop

- Confirma que `app/desktop/main.py` se ejecuta desde la raíz del proyecto (con `venv` activo).
- Verifica que `web/` existe y que Eel apunta a la ruta correcta.
- Si Eel no abre la ventana, abre manualmente `http://127.0.0.1:8000` en tu navegador.

---

## No encuentras tu problema

Abre un [Bug Report](../.github/ISSUE_TEMPLATE/bug_report.md) con: OS, versión de Python, versión de la app, navegador, pasos para reproducir, logs y screenshots. Sin datos sensibles.