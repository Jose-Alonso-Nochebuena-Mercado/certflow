# CertFlow

Aplicación desktop en Python para construir y mantener el planning de certificación por CRQ usando catálogos locales, metadata JSON y estructura compatible con Xray.

## Estado actual

Hoy el flujo principal permite:

- crear CRQs desde la UI y continuar inmediatamente al armado de tests
- visualizar el detalle y el planning por tipología
- abrir el flujo de **Añadir tests**
- seleccionar servicio, transacción y versión desde un catálogo local
- ejecutar una request Bruno en modo real
- descubrir nodos JSON candidatos a test set
- elegir qué nodos y qué tests base por campo guardar
- persistir el planning por CRQ en `metadata/plannings/`
- agregar nuevos servicios, transacciones y versiones directamente desde `Añadir tests`
- asociar 0..N librerías consumidas a cada transacción para enriquecer el test planning futuro
- lanzar desde el Home una automatización asistida con Playwright para abrir Jira/Xray y precargar formularios dummy de `Test`, `Test Set`, `Test Plan` y `Test Execution`

## Archivos clave del nuevo bloque

- `config/services_catalog.json`: catálogo local de servicios/transacciones/versiones y request Bruno asociada
- `config/bruno.json`: estrategia de ejecución real/mock para Bruno
- `config/mocks/*.json`: respuestas mock iniciales para el adapter de Bruno
- `metadata/coverage_catalog.json`: inventario local existente de test sets/tests
- `app/services/test_catalog_service.py`: resolución del catálogo, carga de mocks y mapeo JSON
- `app/services/bruno_catalog_service.py`: exploración de colecciones Bruno en una ruta absoluta externa al workspace
- `app/services/planning_service.py`: persistencia y sincronización del planning por CRQ
- `app/ui/pages/add_tests_page.py`: flujo UI real de Añadir tests
- `app/ui/pages/settings_page.py`: configuración por pestañas de Bruno/Jira, exploración de colecciones e importación de requests `.bru` al catálogo

## Ejecución

```python
python -m playwright install chrome
python main.py
```

## Notas

- El flujo vigente está orientado a Bruno en modo real.
- La automatización asistida de Jira/Xray usa Playwright en modo visible y reutiliza un perfil local en `metadata/jira_automation/playwright_profile` para conservar sesión cuando sea posible.
- La primera vez que uses los botones del Home, Playwright puede abrir Chrome y esperar pasivamente a que inicies sesión manualmente en Jira; no debería recargar la página mientras escribes. Una vez autenticado, esa sesión suele reutilizarse en ejecuciones posteriores mientras Jira/SSO no la expire.
- Antes de probar los botones temporales del Home, completa en `Settings > Jira` al menos: `Jira base URL`, `Project Key`, `Project Name` y opcionalmente `Test Repository Path`.
- La ruta de colecciones Bruno puede vivir fuera del workspace, por ejemplo `C:\Users\XMF5325\Documents\Bruno Colections`, y se administra desde el engrane.
- En la pestaña `Bruno` debes capturar el comando real con el que ejecutas Bruno en tu equipo.
- El modo de respuesta se detecta automáticamente: si el comando usa `{output_file}`, se leerá archivo; en caso contrario se esperará JSON por stdout.
- Si el servicio real requiere VPN, actívala antes de probar la request importada desde `Añadir tests`.
- La estrategia de tipologías vigente es:
  - `Integrado` como base
  - `Aceptación` como copia validable de `Integrado`
  - `Regresión` como línea separada
- Para más detalle funcional revisa `docs/06_estado_actual.md`.

