# Seguridad

La seguridad de **Video Downloader Local** es una prioridad. Esta política explica cómo reportar vulnerabilidades de forma responsable.

---

## Reportar vulnerabilidades

Si has encontrado una vulnerabilidad, **no la publiques como GitHub Issue público**. Reporta de forma privada:

- Email: **developer@kevscl.com**

### Información que debes incluir

- Descripción clara de la vulnerabilidad.
- Pasos detallados para reproducirla.
- Versión de la aplicación afectada.
- Versión de Python y sistema operativo.
- Impacto potencial (privacidad, ejecución remota, denegación de servicio, etc.).
- Cualquier prueba de concepto (PoC) que puedas incluir de forma segura.

### Información que NO debes incluir públicamente

- No publiques la vulnerabilidad en GitHub Issues, Pull Requests ni discusiones públicas.
- No compartas archivos de descarga de videos ni muestras que contengan metadatos personales o URLs sensibles del usuario.
- No incluyas tokens, cookies, credenciales o información de acceso en el reporte.

---

## Proceso de revisión

1. Confirmación de recepción (dentro de 48 h).
2. Evaluación de severidad y alcance.
3. Desarrollo de corrección (cuando aplique).
4. Publicación de la corrección en una versión parche.
5. Crédito al reportador (salvo que solicite anonimato).

## Divulgación responsable

Se recomienda una ventana de **90 días** para corregir la vulnerabilidad antes de cualquier divulgación pública. Mantendremos al reportador informado del progreso.

## Cobertura de GitHub

Este repositorio tiene habilitado:

- **Dependabot** para alertas de dependencias → ver `.github/dependabot.yml`.
- **Secret scanning** para detectar credenciales accidentalmente comprometidas.
- **Push protection** para bloquear el push de secretos detectados.
- **Code scanning** para análisis estático del código fuente.