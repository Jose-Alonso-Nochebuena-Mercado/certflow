# Diseño de Interfaz - CertFlow


# Objetivo


Definir la experiencia visual y funcional de CertFlow.


La aplicación debe permitir que un usuario funcional pueda generar y ejecutar certificaciones sin conocer detalles técnicos.


La interfaz debe ocultar:

- Archivos JSON.
- Metadata interna.
- Estructuras Xray.
- Colecciones Bruno.
- Validaciones técnicas.


---


# Principios de diseño


CertFlow debe tener una interfaz:


- Simple.
- Guiada.
- Minimalista.
- Visual.
- Orientada a decisiones.


El usuario debe responder preguntas funcionales.


Ejemplo:


"¿Qué deseas certificar?"


No:


"Selecciona archivo metadata.json"


---


# Tecnología visual


La implementación vigente funciona como una **aplicación de escritorio local** desarrollada con `customtkinter`.


Flujo actual:



python main.py

    |

    v

Abre ventana desktop de CertFlow

    |

    v

Carga navegación interna por páginas

    |

    v

Permite abrir enlaces externos de Jira cuando estén configurados



La interfaz principal es independiente del navegador y únicamente usará navegación externa cuando se requiera abrir Jira/Xray.


---


# Estructura general


La aplicación estará dividida en módulos visuales:



CertFlow

+-- Inicio

+-- Configuración

+-- Descubrimiento

+-- Diseño de pruebas

+-- Ejecución

+-- Evidencias

+-- Historial



---


# Pantalla inicial


Objetivo:

Iniciar una certificación.


Vista:


         CertFlow

CRQ

[ CRQ-12345 ▼ ]

Información detectada:

Producto:

Movimientos

Estado:

Metadata encontrada

[ Continuar ]



---


# Selección de alcance


Después de seleccionar CRQ:



Selecciona qué deseas certificar:

Producto:

[ Movimientos ▼ ]

Transacción:

☑ Listado Movimiento

☑ Detalle Movimiento

Versión:

[ v2 ▼ ]

[ Continuar ]



---


# Selección de objetos


CertFlow muestra la estructura detectada:


Ejemplo:



Detalle Movimiento v2

Respuesta:

card_extension

|

commerce

|

financing

|

applied_fees

Seleccionar:

☑ card_extension.commerce



---


# Vista de campos


Cuando se selecciona un objeto:


Ejemplo:



Objeto:

card_extension.commerce

Campos detectados:

✔ id

✔ name

✔ address

✔ country

Estado:

id

Pruebas existentes

name

Pruebas existentes

country

Existe pero sin pruebas

address

Nuevo campo



---


# Acciones disponibles


Para cada campo:



id

[ Ver escenarios ]

name

[ Ver escenarios ]

country

[ Crear pruebas ]

address

[ + Crear pruebas ]



---


# Gestión de escenarios


Vista:



Campo:

commerce.address

Escenarios existentes:

✔ Happy Path

Dirección registrada

✔ Alterno

Sin dirección

Agregar:

[ + Nuevo escenario ]



---


# Creación de escenario


Formulario:



Nombre:

[ Comercio con dirección ]

Tipo:

[ Happy Path ▼ ]

Request:

Detalle Movimiento

Bruno:

GET /movements/{id}

Body:

{
"movementId":"12345"
}

Campo esperado:

card_extension.commerce.address

Valor esperado:

Amazon México

[ Guardar ]



---


# Editor de Body


El body será editable.


Objetivo:


Permitir modificar datos enviados a la petición sin modificar Bruno original.


Ejemplo:



Request original Bruno:

{
"movementId":"12345"
}

Body utilizado:

{
"movementId":"99999"
}



El sistema conservará:


- Request original.
- Modificación utilizada.
- Resultado.


---


# Pantalla de ejecución


Esta pantalla representa la simulación visual de Bruno.


Objetivo:


Generar evidencia.


Ejemplo:



CertFlow Bruno Runner

GET

/movements/detail

Status:

200 OK

Response:

{
"card_extension":{
"commerce":{
"id":"AMAZON"
}
}

}

Validación:

✔ commerce.id correcto



Esta pantalla será utilizada para captura.


---


# Diferencia entre interfaz CertFlow y Bruno


La aplicación normal:



CertFlow UI

Creación

Configuración

Metadata

Escenarios

Xray



La pantalla de ejecución:



Simulación Bruno

Request

Response

Resultado



Solamente esta última busca parecerse a Bruno.


---


# Historial


La aplicación debe mostrar ejecuciones anteriores.


Ejemplo:



CRQ-12345

Integrado

35 PASS

0 FAIL

Accepted

35 PASS

0 FAIL

Fecha:

2026-01-01



---


# Principio UX


El usuario nunca debe preguntarse:


"¿Qué archivo debo modificar?"


"¿Qué test debo crear?"


"¿Qué objeto existe?"


CertFlow debe mostrar la información y permitir decidir.