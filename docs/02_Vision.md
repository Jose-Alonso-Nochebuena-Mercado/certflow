# Visión General - CertFlow


# Introducción


CertFlow es una plataforma de automatización de certificaciones funcionales orientada a reducir el trabajo manual realizado actualmente mediante Jira, Xray y Bruno.


El objetivo no es únicamente ejecutar pruebas.

El objetivo es crear un asistente inteligente capaz de administrar todo el ciclo de certificación.


---


# Problema actual


Actualmente el proceso requiere:


- Crear Test Plans manualmente.
- Crear Test Executions.
- Buscar Test Sets.
- Crear Tests.
- Ejecutar requests en Bruno.
- Validar respuestas.
- Capturar evidencias.
- Actualizar resultados en Xray.


Este proceso es repetitivo y propenso a errores.


---


# Objetivo principal


Automatizar la mayor cantidad posible del proceso:



CRQ

↓

Análisis

↓

Generación

↓

Ejecución

↓

Evidencia

↓

Xray



---


# Objetivos específicos


## Automatización


Reducir tareas manuales:


- Navegación Jira.
- Creación de elementos Xray.
- Ejecución repetitiva.
- Capturas.
- Organización.


---


## Reutilización


Los conocimientos generados deben permanecer.


Ejemplo:


CRQ 1:



commerce.id
commerce.name



CRQ 2:



commerce.address



Resultado:


El mismo Test Set se reutiliza.


---


# Alcance


CertFlow podrá:


- Leer colecciones Bruno.
- Crear catálogo de requests.
- Detectar estructuras JSON.
- Crear metadata inicial.
- Comparar cambios.
- Crear escenarios.
- Crear Tests Xray.
- Ejecutar pruebas.
- Generar evidencias.
- Actualizar Xray.


---


# Filosofía


El usuario debe indicar:



¿Qué quiero certificar?



No:



¿Cómo debo hacerlo?



CertFlow debe encargarse del proceso técnico.


---


# Principio central


La información funcional vive en metadata.


El código ejecuta.


La metadata decide qué probar.