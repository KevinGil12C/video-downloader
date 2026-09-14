# Third-Party Notices

Este proyecto agradece y utiliza las siguientes bibliotecas y herramientas de terceros. La información de licencia de cada una se indica a continuación.

> **Nota de verificación:** antes de cada release, el mantenedor debe verificar que las versiones bloqueadas en `requirements.txt` y `requirements-dev.txt` mantienen las licencias aquí indicadas. Este documento refleja las licencias conocidas de los componentes en el momento de escribirse.

---

## Dependencias de runtime

| Componente | Licencia | Proyecto / copyright |
|------------|----------|----------------------|
| [Python](https://www.python.org/) | PSF License v2 | Python Software Foundation |
| [Eel](https://github.com/python-eel/Eel) | MIT | Chris Knott y colaboradores |
| [FastAPI](https://fastapi.tiangolo.com/) | MIT | Sebastián Ramírez |
| [Uvicorn](https://www.uvicorn.org/) | BSD-3-Clause | Encode OSS Ltd. y colaboradores |
| [Pydantic](https://docs.pydantic.dev/) | MIT | Samuel Colvin y colaboradores |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense | The yt-dlp maintainers |
| [FFmpeg](https://ffmpeg.org/) | LGPL-2.1-or-later (o GPL según build) | FFmpeg project |
| [Tailwind CSS](https://tailwindcss.com/) | MIT | Tailwind Labs, Inc. |
| [Material Icons](https://fonts.google.com/icons) | Apache-2.0 | Google LLC |

## Dependencias de desarrollo

| Componente | Licencia | Proyecto / copyright |
|------------|----------|----------------------|
| [pytest](https://pytest.org/) | MIT | Holger Krekel y colaboradores |
| [pytest-cov](https://pytest-cov.readthedocs.io/) | MIT | pytest-cov authors |
| [httpx](https://www.python-httpx.org/) | BSD-3-Clause | Encode OSS Ltd. |
| [ruff](https://docs.astral.sh/ruff/) | MIT | Astral Software Inc. |
| [mypy](https://www.mypy-lang.org/) | MIT | Jukka Lehtosalo y colaboradores |
| [types-requests](https://github.com/python/typeshed) | Apache-2.0 | TypeShed authors |

---

## Notas

- **FFmpeg** no es dependencia pip: es un binario externo. Su licencia depende de cómo se compiló el binario concreto (por defecto LGPL-2.1-or-later; GPL si se incluyeron componentes GPL). Consulta la documentación del binario que distribuyas.
- Las marcas y nombres de productos pertenecen a sus respectivos propietarios.
- La licencia del propio proyecto es MIT — ver [LICENSE](LICENSE).