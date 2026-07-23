# Estado actual de implementación - CertFlow

Fecha de actualización: 2026-07-22

## Propósito de este documento

Este archivo complementa la documentación base del proyecto y describe el **estado real implementado** del MVP actual.

Los documentos `01_arquitectura.md` y `05_diseno_interfaz.md` siguen representando la **arquitectura objetivo** y la **visión futura**. En cambio, este documento resume qué partes ya existen en código y cuáles siguen pendientes.

---

## 1. Stack vigente

Actualmente CertFlow está implementado como una **aplicación de escritorio en Python** con:

- `customtkinter` para la interfaz
- persistencia en archivos JSON
- separación base por capas:
  - `app/ui`
  - `app/services`
  - `app/core`
  - `config`
  - `metadata`

> Nota: parte de la documentación histórica menciona una UI web/local. El código vigente utiliza una UI desktop con `customtkinter`.

---

## 2. Flujo actualmente disponible

### Home

Archivo principal: `app/ui/pages/home_page.py`

Estado:
- lista CRQs desde `metadata/crqs.json`
- permite crear un nuevo CRQ
- permite eliminar un CRQ
- permite abrir un CRQ existente
- muestra CRQs como tarjetas compactas en grid
- expone una acción rápida para añadir tests desde cada tarjeta
- la acción `+` ya abre el flujo real de selección de servicio/transacción/versión

### Nuevo CRQ

Archivo principal: `app/ui/pages/new_crq_page.py`

Estado:
- captura:
  - SDATOOL
  - CRQ
  - Descripción
  - Portafolio
  - Fecha de instalación
  - Typology
- guarda en `metadata/crqs.json`
- usa una tarjeta central con scroll y estilos alineados al dashboard principal
- al crear el CRQ continúa directamente al flujo de `Añadir tests`

### Detalle de CRQ

Archivo principal: `app/ui/pages/crq_detail_page.py`

Estado:
- abre desde Home al seleccionar un CRQ
- muestra resumen del CRQ
- muestra estructura visible de:
  - Test Plan
  - Test Set
  - Tests
- permite ir a Discovery desde el detalle
- incluye acción funcional para añadir más tests
- prepara integración con enlace configurable a Jira desde `config/ui.json`
- ya refleja la estrategia base por typology:
  - `Integrado` como base principal de afectación
  - `Aceptación` como copia validable de Integración cuando ambas existan
  - `Regresión` como planning separado de no afectación
- si existe planning persistido por CRQ, lo reutiliza en lugar de regenerarlo siempre

### Añadir tests

Archivo principal: `app/ui/pages/add_tests_page.py`

Estado:
- nuevo flujo guiado de catálogo local
- permite seleccionar:
  - servicio
  - transacción
  - versión cuando aplique
- permite dar de alta nuevos servicios, transacciones y versiones directamente desde la pantalla
- cada transacción ya puede registrar de 0 a N librerías consumidas
- resuelve la request Bruno asociada por configuración local
- ejecuta Bruno real si está configurado y, si no, puede caer a mock según `config/bruno.json`
- arma un mapa manual de nodos JSON candidatos a test set
- permite activar/desactivar tests base por campo antes de guardar
- persiste el resultado en `metadata/plannings/<crq>.json`
- reutiliza inventario local de cobertura desde `metadata/coverage_catalog.json`

### Discovery

Archivo principal: `app/ui/pages/discovery_page.py`

Estado:
- ya forma parte del flujo de navegación real
- recibe el CRQ seleccionado desde Home
- muestra el estado actual del CRQ:
  - CRQ seleccionado
  - discovery disponible o pendiente
  - metadata funcional registrada o pendiente
- permite abrir metadata aunque el discovery automático todavía no esté implementado

### Metadata

Archivo principal: `app/ui/pages/metadata_page.py`

Estado:
- recibe el CRQ seleccionado
- si existe discovery guardado, compara discovery vs metadata funcional
- si no existe discovery pero sí metadata funcional persistida, muestra esa metadata existente
- si no existe ninguna de las dos, informa claramente que aún no hay datos técnicos o funcionales para ese CRQ

---

## 3. Cambios recientes incorporados

### Navegación

Se reforzó `app/core/router.py` para:

- registrar la ruta `discovery`
- registrar la ruta `crq_detail`
- permitir navegación con parámetros de contexto entre páginas
- mantener un historial simple para soportar regresar

Ejemplo actual de flujo:

`Home -> CRQ Detail -> Discovery -> Metadata`

### Robustez de rutas a archivos

Se actualizaron servicios para usar rutas absolutas basadas en la raíz del proyecto en lugar de depender del directorio de ejecución:

- `app/services/config_service.py`
- `app/services/crq_service.py`
- `app/services/metadata_service.py`
- `app/services/discovery_service.py`

Esto evita fallos cuando la aplicación se ejecuta desde una ubicación distinta al root del proyecto.

### Configuración Xray

`config_service.py` ahora soporta ambas claves:

- `portafolio_apps`
- `Portafolio_apps`

Con esto se mantiene compatibilidad con configuraciones legacy.

Adicionalmente:
- se agregó caché sobre la carga de catálogos frecuentes
- se centralizó `obtener_mapa_typology()` para reutilizar el mapeo id → nombre de certificación en distintas pantallas

### Header

El header ahora concentra navegación global y acciones comunes.

Estado actual:
- botón Inicio global
- botón Regresar global
- acción de configuración sin ruta funcional todavía
- marca BBVA simplificada como texto para evitar problemas visuales del asset actual

### CRQCard

Se compactó el diseño de `app/ui/components/crq_card.py`:

- menos padding vertical
- subtítulo compacto con SDATOOL y portafolio
- badges de tipología más pequeñas
- acciones en orden:
  - eliminar
  - añadir tests
  - abrir
- se eliminó el estado visual `Ejecución` porque no aporta al flujo operativo actual

---

## 4. Estado de persistencia

### CRQs

Archivo actual: `metadata/crqs.json`

Observación:
el campo `certificaciones` ya quedó homologado al formato A.

Formato vigente de persistencia:
- lista simple de ids de typology
- ejemplo: `"certificaciones": ["integrado", "accepted"]`

Notas:
- la UI muestra nombres amigables cuando necesita presentar estos valores
- el servicio de CRQ normaliza automáticamente datos legacy si aún aparecieran registros antiguos

### Discovery técnico

Ubicación prevista:
- `metadata/discoveries/<crq>.json`

Estado:
- ya existe soporte de lectura/escritura en servicio
- aún no existe integración automática con Bruno

### Metadata funcional

Ubicación prevista:
- `metadata/functional/<crq>.json`

Estado:
- existe servicio de carga, guardado y comparación
- aún falta la UI para crear/editar esa metadata de forma completa

### Planning por CRQ

Estado actual:
- ya se persiste como archivo propio en `metadata/plannings/<crq>.json`
- si todavía no existe archivo, se parte de la generación base de `xray_service.py`
- desde `Añadir tests` se sincronizan test sets por request seleccionada
- la persistencia conserva el origen funcional de cada test set:
  - servicio
  - transacción
  - versión
  - request Bruno lógica

Reglas vigentes:
- si el usuario pide solo `Integrado`, se construye un test plan base de afectación
- si pide `Integrado` y `Aceptación`, primero se arma Integración y Aceptación parte como copia de esa base
- en Aceptación solo debe validarse si se agregan o quitan test sets o tests
- si pide `Regresión`, se considera un planning separado de no afectación
- si pide las tres, `Regresión` se mantiene como línea separada respecto a `Integrado` / `Aceptación`

---

## 5. Pendientes inmediatos recomendados

### Prioridad alta

1. Implementar discovery real
   - consolidar ejecución multi-request cuando un servicio tenga varias variantes
   - guardar discovery técnico persistido por request real
   - habilitar comparación real en `MetadataPage`

2. Crear/editar metadata funcional desde UI
   - persistir `validated_fields`
   - persistir `ignored_fields`
   - preparar base para escenarios

3. Evolucionar la acción real de añadir tests
   - conectar ejecución real con Bruno
   - permitir revisión más granular de escenarios por campo
   - enriquecer el inventario local con sincronización posterior hacia Jira/Xray
   - a futuro implementar actualización completa de Test Sets ya existentes, incluyendo agregar nuevos Tests y modificar Tests existentes; este trabajo se pospone porque implica resolver edición diferencial, reconciliación con Jira/Xray y preservación segura de asociaciones ya creadas

### Prioridad media

4. Evolucionar pantalla de configuración
   - ya existe acceso desde el engrane
   - ya usa una configuración por pestañas separando Bruno, Jira y resumen general
   - ya permite definir ruta de colecciones Bruno y ver árbol de carpetas/requests
   - ya permite importar requests `.bru` seleccionadas directamente al catálogo funcional
5. Revisar si `app/ui/router.py` seguirá existiendo o debe retirarse del proyecto
6. Normalizar catálogos Xray
   - ortografía de portafolios
   - ids/nombres/labels de typology

7. Revisar branding BBVA definitivo
   - decidir si se conserva texto plano en header
   - o si se sustituye por un asset optimizado para fondo oscuro

---

## 6. Decisión de arquitectura vigente

Hasta nuevo aviso, el proyecto seguirá avanzando sobre esta base:

- UI desktop con `customtkinter`
- almacenamiento en JSON
- navegación por páginas
- servicios pequeños y específicos
- evolución incremental hacia discovery, metadata funcional, escenarios y Xray

Esta decisión permite terminar primero el flujo operativo antes de refactorizar hacia una arquitectura más extensa.

---

## 7. Dirección de modularización aplicada

Sin hacer una reestructura grande todavía, el proyecto ya empezó a moverse hacia componentes y servicios más reutilizables.

Mejoras aplicadas hasta ahora:
- centralización del mapeo de tipologías en `config_service.py`
- reutilización del mismo mapeo en:
  - `CRQCard`
  - `CRQDetailPage`
  - `MetadataPage`
- incorporación de constantes de UI para formularios y acciones comunes

Principios que se buscarán reforzar en próximas iteraciones:
- **S**: separar mejor validación, renderizado y persistencia
- **O**: facilitar agregar pantallas/componentes sin tocar demasiados archivos base
- **D**: reducir dependencias directas de páginas hacia detalles internos de servicios

Refactors futuros recomendados:
- extraer componente reutilizable para badges de tipología
- separar mejor servicios de configuración UI y catálogos Xray
- convertir el router a un registro más declarativo

---

## 8. Estado actual de uniformidad visual

La UI principal ya cuenta con una base visual reutilizable en `app/ui/theme/`.

Elementos ya uniformados:
- `Header` global
- `Home`
- `Nuevo CRQ`
- `Detalle de CRQ`
- `ConfirmDialog`
- `MessageBox`

Tokens reutilizables ya definidos:
- colores para acciones de header
- hover secundario
- tamaños de botones circulares e iconográficos
- paddings horizontales de página
- tamaños de diálogos
- estilos suaves de cards y badges

Decisiones vigentes:
- las páginas deben privilegiar **cards compactas** sobre layouts muy largos
- cuando un campo necesite bastante texto, debe usar **scroll interno local** y no forzar scroll global de toda la ventana
- el header debe seguir funcionando como navegación global persistente

---

## 9. Lineamientos para futuras ventanas

Toda nueva ventana o página debe intentar seguir estas reglas:

1. **Usar tokens del theme antes de hardcodear valores**
   - colores desde `colors.py`
   - tamaños desde `dimensions.py`
   - estilos desde `styles.py`

2. **Mantener la misma estructura visual base**
   - header global fijo
   - hero breve con título claro
   - contenido dentro de cards con borde suave
   - acciones principales alineadas al mismo lenguaje visual

3. **No depender de scroll global si puede evitarse**
   - preferir distribución en columnas
   - usar scroll interno en campos o zonas largas

4. **Reutilizar patrones existentes**
   - badges de tipología
   - cards de resumen
   - botones secundarios suaves
   - diálogos con card interna

5. **Separar lógica y UI siempre que sea razonable**
   - validación fuera del render cuando sea posible
   - mapeos/catálogos centralizados en servicios
   - evitar duplicar strings o estilos entre páginas

