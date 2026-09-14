# Desarrollo

Guía para preparar el entorno de desarrollo y trabajar en el proyecto.

---

## Requisitos

- Windows 10/11, Python 3.10+, Git 2.x, FFmpeg (ver [instalación](troubleshooting.md)).

## Clonar y preparar entorno

```bat
git clone https://github.com/KevinGil12C/video-downloader.git
cd video-downloader

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Ejecutar la aplicación

- **Modo Desktop** — lanza la ventana Eel:
  ```bat
  python -m app.desktop.main
  ```
- **Solo API localhost** — para desarrollo de la web o la extensión:
  ```bat
  python -m uvicorn app.backend.server:app --host 127.0.0.1 --port 8000
  ```

## Tests

```bat
pytest
pytest -v
pytest --cov=app tests/
```

- Los tests se definen en `tests/` y **nunca** descargan contenido real de Internet (usan mocks).
- Cualquier nueva funcionalidad debe incluir tests.

## Lint y formato

```bat
ruff check .
ruff format --check .
```

Para auto-corregir:

```bat
ruff check . --fix
ruff format .
```

Tipos estáticos (opcional):

```bat
mypy app
```

## Convenciones

- Python 3.10+, tipado en firmas públicas.
- Ruff con línea de 88 caracteres; config en `pyproject.toml`.
- Conventional Commits (ver [CONTRIBUTING.md](../CONTRIBUTING.md)).
- Ramas con prefijos `feature/`, `fix/`, `docs/`, etc.

## Desarrollo de la extensión de navegador

1. Carga la extensión desempaquetada desde `extension/` (ver [browser-extension.md](browser-extension.md)).
2. Levanta la API localhost.
3. Prueba el flujo: pestaña activa → extensión → `POST /api/downloads`.

## Estructura del código

```
app/backend/server.py      FastAPI app factory
app/backend/config.py      Configuración (env + config.example.json)
app/backend/security.py    Validación de URLs, CORS, sanitización
app/backend/models.py      Modelos Pydantic
app/backend/api/*.py       Routers
app/services/*.py          Lógica de descarga, FFmpeg y progreso
web/                       Frontend
extension/                 Extensión MV3
```

## Commits y Pull Requests

Ver [CONTRIBUTING.md](../CONTRIBUTING.md) para el flujo completo (fork → branch → commit → PR).