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

### Changed
### Fixed
### Security