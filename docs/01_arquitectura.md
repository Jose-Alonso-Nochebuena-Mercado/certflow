# Arquitectura - CertFlow


# 1. Introducción


CertFlow es una aplicación de escritorio/web local desarrollada en Python cuyo objetivo es automatizar el proceso completo de certificación funcional actualmente realizado mediante:

- Jira.
- Xray.
- Bruno.
- Validaciones manuales.
- Capturas de evidencia.


La arquitectura está diseñada para que el sistema sea asistido, reutilizable y extensible.

CertFlow no busca únicamente ejecutar pruebas.

Su objetivo es administrar todo el ciclo:


Descubrimiento técnico

    |

Metadata funcional

    |

Generación de pruebas

    |

Ejecución automática

    |

Evidencias

    |

Actualización Xray



---


# 2. Principios arquitectónicos


## 2.1 Sin base de datos


CertFlow no utilizará una base de datos local.


Toda la información será almacenada mediante archivos:



JSON

YAML

Archivos de configuración



Motivos:

- Fácil respaldo.
- Fácil versionamiento.
- Fácil auditoría.
- Fácil transporte.
- Sin dependencias externas.


---


## 2.2 Separación de responsabilidades


La arquitectura estará dividida en capas:


            Usuario

              |

              v

         Interfaz UI

              |

              v

         Orquestador

              |

 +------------+-------------+

 |            |             |

Metadata Ejecutor HTTP Xray

 |

Descubrimiento Técnico

 |

Validaciones

 |

Evidencias



---


# 3. Componentes principales


## 3.1 UI CertFlow


Responsable de:

- Selección de CRQ.
- Selección de transacciones.
- Visualización de metadata.
- Creación de escenarios.
- Revisión de diferencias.
- Ejecución.


La interfaz será una aplicación local.


Tecnología propuesta:



Python + Web Local



El usuario ejecutará:



python main.py



Y automáticamente:


- Levanta servidor local.
- Abre navegador.
- Carga interfaz.


---


# 3.2 Orquestador


Es el núcleo de CertFlow.


Responsable de coordinar:



CRQ

|

Descubrimiento

|

Metadata

|

Generación

|

Ejecución

|

Xray

|

Evidencias



No contiene reglas específicas de negocio.


---


# 3.3 Motor de descubrimiento técnico


Responsable de analizar:


- Colecciones Bruno.
- Requests.
- Responses.
- Estructuras JSON.


Genera:



Metadata técnica



Ejemplo:


Entrada:



Bruno Request

Detalle Movimiento



Salida:


```json
{
 "object":"card_extension.commerce",

 "fields":[
    "id",
    "name",
    "address"
 ]
}
3.4 Metadata funcional

Representa el conocimiento de certificación.

Define:

Qué validar.
Qué campos son importantes.
Qué escenarios existen.
Qué pruebas deben generarse.

Ejemplo:

{
 "field":"card_extension.commerce.id",

 "coverage":"complete"
}
3.5 Motor de ejecución

Responsable de:

Ejecutar requests.
Preparar datos.
Validar respuestas.
Generar resultados.

No crea información.

Solo ejecuta reglas existentes.

3.6 Integración Xray

Como la API Jira está bloqueada:

CertFlow NO utilizará API.

La integración será mediante:

Playwright

+

Navegador existente

Responsabilidades:

Buscar Test Plan.
Crear si no existe.
Buscar Test Set.
Reutilizar.
Crear Tests faltantes.
Asociar.
Ejecutar.
Adjuntar evidencia.
3.7 Evidencias

Cada prueba generará:

Screenshot

Logs

Resultado

La captura será una representación visual similar a Bruno.

La interfaz normal de CertFlow será independiente.

4. Flujo arquitectónico general
Usuario

 |

CRQ

 |

CertFlow

 |

Descubrimiento Técnico

 |

Comparación Metadata

 |

Generación Escenarios

 |

Generación Tests

 |

Ejecución

 |

Validación

 |

Evidencia

 |

Xray
5. Estructura general del proyecto
CertFlow

|

+-- main.py

|

+-- ui

|

+-- core

|

+-- discovery

|

+-- execution

|

+-- xray

|

+-- metadata

|

+-- config

|

+-- evidence

|

+-- logs

|

+-- storage
6. Entrada principal

El flujo inicial será:

def main():

    abrir_ventana()

    cargar_configuracion()

    seleccionar_crq()

    analizar_metadata()

    ejecutar_flujo()


El main únicamente coordina.

No contiene lógica.

7. Restricciones

CertFlow:

NO:

Utiliza API Jira.
Guarda información en SQL.
Genera datos de negocio.
Modifica sistemas externos.

SI:

Lee configuraciones.
Ejecuta consultas existentes.
Ejecuta requests.
Valida resultados.
Gestiona evidencias.
Automatiza Xray.