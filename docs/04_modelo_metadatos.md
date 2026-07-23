# Modelo de Metadatos - CertFlow


# Objetivo


Define cómo CertFlow almacenará el conocimiento necesario para realizar certificaciones.


La metadata será dividida en:



Metadata Técnica

    |

Metadata Funcional

    |

Cobertura

    |

Escenarios

    |

Tests



---


# 1. Metadata Técnica


Generada automáticamente.


Fuente:


- Bruno.
- Responses JSON.
- Requests.


Representa lo que existe realmente.


Ejemplo:


```json
{
 "transaction":"detalle_movimiento_v2",

 "objects":[

  {
   "name":"card_extension.commerce",

   "fields":[
      "id",
      "name",
      "country",
      "address"
   ]

  }

 ]
}
2. Metadata Funcional

Define qué debe validarse.

Ejemplo:

{
 "object":"card_extension.commerce",

 "fields":[

  {
   "name":"id",
   "required":true
  },

  {
   "name":"address",
   "required":false
  }

 ]
}
3. Cobertura

Define si existe prueba.

Estados:

NEW

PENDING

COVERED

IGNORED

Ejemplo:

{
 "field":"commerce.id",

 "coverage":"COVERED"
}
4. Escenarios

Un campo puede tener múltiples escenarios.

Ejemplo:

{
 "field":"commerce.id",

 "scenarios":[

 {
  "name":"Amazon happy path",

  "expected":"AMAZON"
 }

 ]

}
5. Regla importante

Existencia técnica no significa cobertura.

Ejemplo:

Existe:

commerce.country

Pero:

coverage=PENDING

porque todavía no tiene pruebas.

6. Relación final
Transaction

|

Object

|

Field

|

Coverage

|

Scenario

|

Xray Test
7. Descubrimiento incremental

Si aparece:

commerce.address

CertFlow debe:

Detectarlo.
Compararlo.
Mostrarlo.
Permitir crear escenarios.

No debe modificar automáticamente pruebas existentes.

---

# 8. Relación con typology y planning

Además de la metadata funcional, CertFlow necesita construir planning por CRQ con base en la typology solicitada.

Reglas actuales del dominio:

- `Integrado` representa la base principal de pruebas de afectación.
- `Aceptación` normalmente reutiliza la misma base de `Integrado`.
- cuando un CRQ pida ambas (`Integrado` + `Aceptación`), primero se define Integración y luego Aceptación parte como copia.
- `Aceptación` no debe reconstruirse desde cero salvo que el usuario decida agregar o quitar test sets o tests.
- `Regresión` representa pruebas de no afectación y debe tratarse como una línea separada.

Relación esperada:

CRQ

|

Typology

|

Test Plan

|

Test Set

|

Test

Esto significa que un mismo CRQ puede tener múltiples test plans, uno por typology seleccionada.
