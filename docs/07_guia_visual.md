# Guía visual - CertFlow

Fecha de actualización: 2026-07-22

## Objetivo

Definir una base visual simple, reutilizable y consistente para todas las pantallas futuras de CertFlow.

---

## 1. Principios visuales

La interfaz debe sentirse:

- corporativa
- limpia
- clara
- compacta
- guiada
- consistente entre páginas

Evitar:

- bloques visuales demasiado largos
- hardcodes repetidos de color/tamaño
- diálogos con estilos distintos al resto de la aplicación
- acciones principales con iconografía inconsistente

---

## 2. Estructura recomendada por página

### Header global

Siempre visible.

Debe contener:
- marca / identidad
- navegación global
- acciones persistentes

### Hero de página

Usar:
- título principal
- subtítulo corto solo si realmente agrega contexto

Evitar:
- explicaciones largas en la parte superior
- duplicar mensajes que ya aparecen en la card principal

### Cuerpo principal

Debe vivir preferentemente dentro de una o varias `cards` con:
- borde suave
- radio consistente
- padding interior amplio

### Footer o acciones

Acciones primarias:
- color `PRIMARY`
- texto claro

Acciones secundarias:
- fondos suaves
- borde tenue
- mismo radio que el resto del sistema

---

## 3. Tokens base a reutilizar

### Colores

Usar siempre `app/ui/theme/colors.py`.

Tokens importantes:
- `PRIMARY`
- `PRIMARY_LIGHT`
- `PRIMARY_SOFT`
- `BACKGROUND`
- `SURFACE`
- `SURFACE_ALT`
- `BORDER`
- `TEXT_PRIMARY`
- `TEXT_SECONDARY`
- `TEXT_MUTED`
- `SECONDARY_HOVER`
- `HEADER_ACTION_BG`
- `HEADER_ACTION_BORDER`
- `HEADER_ACTION_SEPARATOR`
- `HEADER_ACTION_HOVER`

### Dimensiones

Usar siempre `app/ui/theme/dimensions.py`.

Tokens importantes:
- `PAGE_HORIZONTAL_PADDING`
- `BUTTON_HEIGHT`
- `ICON_BUTTON_SIZE`
- `ICON_BUTTON_RADIUS`
- `CIRCULAR_BUTTON_SIZE`
- `CIRCULAR_BUTTON_RADIUS`
- `FORM_INPUT_WIDTH`
- `FORM_CARD_WIDTH`
- `DIALOG_WIDTH`
- `DIALOG_HEIGHT`
- `MESSAGE_BOX_WIDTH`
- `MESSAGE_BOX_HEIGHT`

### Estilos

Usar `app/ui/theme/styles.py` cuando aplique.

Patrones ya definidos:
- `SOFT_CARD_STYLE`
- `SECONDARY_BUTTON`
- `HEADER_ACTION_GROUP`
- `ICON_BUTTON_LIGHT`
- `SOFT_BADGE_STYLE`

---

## 4. Reglas de composición

### Formularios

- preferir layouts en dos columnas cuando el contenido lo permita
- evitar que todo dependa de un scroll global largo
- cuando un campo requiera mucho texto, usar scroll interno local
- mantener botones de acción fijos o fáciles de ubicar
- cuando se capture una fecha, preferir un selector visual pequeño reutilizable en lugar de texto libre

### Tarjetas

- información principal arriba
- metadata secundaria en badges suaves
- acciones claras y compactas abajo
- no saturar con estados que no aporten a la decisión del usuario

### Diálogos

- usar card interior
- una sola acción principal
- una sola acción secundaria
- mensaje corto y centrado

### Header

- navegación global agrupada
- iconos compactos y uniformes
- evitar mezclar estilos diferentes dentro del mismo grupo

---

## 5. Checklist para nuevas ventanas

Antes de agregar una nueva página o modal, validar:

- [ ] ¿usa colores del theme en lugar de hardcodes?
- [ ] ¿usa paddings y tamaños reutilizables?
- [ ] ¿respeta el header global existente?
- [ ] ¿mantiene acciones primarias/secundarias con el mismo lenguaje visual?
- [ ] ¿evita scroll global innecesario?
- [ ] ¿si hay mucho contenido, se resolvió con secciones o scroll local?
- [ ] ¿el diseño es consistente con Home, Nuevo CRQ y Detalle CRQ?

---

## 6. Dirección futura

A medida que CertFlow crezca, conviene extraer componentes reutilizables adicionales:

- badge tipológico reutilizable
- card resumen de CRQ
- toolbar de acciones de página
- contenedor estándar para formularios
- patrón unificado de mensajes y confirmaciones

Esto permitirá que las nuevas ventanas se construyan más rápido y con menos dependencias directas.

