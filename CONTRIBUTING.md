# Contributing

¡Gracias por tu interés en contribuir a **Video Downloader Local**!

Este proyecto es Open Source (MIT). Cualquier persona puede participar: reportar bugs, proponer funciones, mejorar la documentación o revisar código. Antes de empezar, lee el [Código de Conducta](CODE_OF_CONDUCT.md).

---

## Flujo general

```
fork → clone → install → develop → test → commit → push → pull request
```

---

## 1. Fork

Haz **fork** del repositorio desde GitHub y configura tu remote:

```bash
git clone https://github.com/<tu-usuario>/video-downloader.git
cd video-downloader
git remote add upstream https://github.com/KevinGil12C/video-downloader.git
git fetch upstream
```

## 2. Entorno de desarrollo

Ver [docs/development.md](docs/development.md) y [README → Desarrollo](README.md#desarrollo):

```bash
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest                           # pruebas
ruff check .                     # lint
ruff format --check .            # formato
mypy app                         # tipos (opcional)
```

## 3. Ramas (`branches`)

**Nunca trabajes directamente sobre `main`.** `main` debe permanecer estable.

Convención de nomenclatura:

```
feature/nombre-de-la-funcionalidad
fix/nombre-del-arreglo
docs/nombre-del-cambio-de-documentacion
refactor/nombre-del-refactor
test/nombre-de-la-prueba
chore/tarea-de-mantenimiento       # dependencias, CI, tooling
security/correccion-de-seguridad
```

Parte siempre de la rama más reciente:

```bash
git checkout -b feature/download-history upstream/main
```

## 4. Commits

Usamos **Conventional Commits**. Un commit tiene: `tipo(alcance): descripcion`.

```
feat: add download queue
fix: resolve progress parsing
docs: improve installation guide
refactor: separate download service
test: add API health tests
chore: update dependencies
security: restrict localhost origins
```

Convención:

- Escribe la descripción en imperativo y minúsculas.
- Describe el **qué** y el **por qué**, no el cómo.
- Un commit = un cambio lógico (se pueden hacer varios commits por rama).
- No subas `venv/`, `downloads/`, `logs/`, secretos, tokens ni archivos generados. Revisa `.gitignore`.

## 5. Pruebas

- Todo cambio de lógica debe incluir o actualizar pruebas (`tests/`).
- Los tests **nunca** realizan descargas reales de contenido externo. Utiliza mocks.
- Ejecuta localmente antes de publicar:

```bash
pytest
ruff check .
ruff format --check .
```

## 6. Push y Pull Request

```bash
git push origin feature/download-history
```

Abre el PR contra la rama `main` de `KevinGil12C/video-downloader`. Revisa [PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md).

### El PR debe incluir

- **Descripción**: qué hace y por qué.
- **Problema**: qué resuelve (referencia la issue: `Closes #12`).
- **Solución**: cómo lo resuelve.
- **Pruebas**: qué tests se ejecutan y resultado.
- **Screenshots** si cambia la UI.
- **Breaking changes** si aplica.
- **Checklist** completo.

### Criterios de revisión

- Pasa CI (lint + tests).
- Sigue las convenciones del proyecto.
- No añade dependencias innecesarias (cada dependencia debe justificar su existencia).
- Sin breaking changes innecesarios.
- Documentación actualizada si aplica.
- No incluye secretos ni datos sensibles.

## 7. Después del merge

- `main` queda estable.
- Elimina tu rama local y remota.
- Sincroniza tu fork con `upstream`.

---

## Reportar bugs

Usa la plantilla [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md). Incluye:

- OS, versión de Python, versión de la aplicación, navegador.
- Pasos para reproducir.
- Comportamiento esperado vs. real.
- Logs y screenshots.

**Nunca** compartas contraseñas, cookies, tokens ni información sensible en issues o PRs.

## Dudas

Para preguntas, usa [GitHub Discussions](https://github.com/KevinGil12C/video-downloader/discussions) (si está habilitado) o el canal de soporte en [SUPPORT.md](SUPPORT.md).