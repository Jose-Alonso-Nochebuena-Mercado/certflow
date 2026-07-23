# Prompt de operación del proyecto CertFlow


# Objetivo


Este documento define cómo debe actuar cualquier asistente que participe en el desarrollo de CertFlow.


Debe mantener consistencia con la arquitectura y decisiones tomadas.


---


# Reglas generales


Siempre:


- Revisar documentación existente antes de proponer cambios.
- Mantener separación entre código y metadata.
- Evitar soluciones que dependan de base de datos.
- Diseñar pensando en extensibilidad.
- Documentar cambios importantes.


---


# Antes de modificar arquitectura


Si una nueva idea afecta:


- Modelo de dominio.
- Metadata.
- Flujo.
- Xray.
- Ejecución.


Debe indicarse qué documentos serán afectados.


Ejemplo:



Cambio solicitado:

Agregar nuevos tipos de escenarios.

Documentos afectados:

04_modelo_metadatos.md

10_modelo_dominio.md

12_reglas_negocio.md



---


# Forma de respuesta


Cuando una decisión afecte documentación:


Agregar:



Actualización requerida:

Archivo:
xxxxx.md

Sección:
xxxxx

Cambio:
xxxxx



---


# Principios técnicos


Nunca asumir:


- Que existe API Jira.
- Que existe SQL.
- Que existen datos dinámicos.
- Que Bruno ejecutará directamente.


---


# Arquitectura obligatoria


Mantener:



Descubrimiento Técnico

    |

Metadata Técnica

    |

Metadata Funcional

    |

Escenarios

    |

Tests Xray

    |

Ejecución

    |

Evidencia



---


# Objetivo final


Crear un sistema mantenible que pueda evolucionar sin modificar código para agregar nuevos productos, transacciones u objetos.