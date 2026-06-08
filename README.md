# Chatbot Pastelería "La Básica" — Simulador de pedidos Take Away

Trabajo Práctico Integrador de **Organización Empresarial** (TUP a Distancia).

Como consultores tecnológicos, se identificó un **proceso administrativo manual e ineficiente**
—la gestión de pedidos de tortas para retiro programado— y se lo automatizó mediante un
**chatbot** cuya lógica responde fielmente a un modelo de procesos **BPMN 2.0**. La entrega es
una **simulación de proceso** por consola, con persistencia en archivos y manejo de errores de
entrada (caminos infelices).

## Datos del trabajo

- **Institución:** Universidad Tecnológica Nacional — TUP a Distancia
- **Materia:** Organización Empresarial
- **Comisión:** N° 11 — Regional Venado Tuerto
- **Integrantes:** Gonzalo Isaias, Franco Kaddour
- **Repositorio:** https://github.com/gjisaias/UTN-TPIntegrador-OE

## El proceso automatizado

El bot guía al cliente de punta a punta: elección de tortas (carrito con agrupación de
cantidades), validación de stock en tiempo real, toma y validación de datos (nombre y teléfono),
selección de fecha y turno con control de cupo, forma de pago, generación de un comprobante con
identificador único y persistencia del pedido. El proceso se modeló en sus dos flujos —**AS-IS**
(manual, actual) y **TO-BE** (automatizado con el chatbot)— en notación BPMN 2.0.

## Arquitectura: del BPMN al código

La lógica está implementada como una **máquina de estados**, de modo que el bot "tiene memoria"
y sabe en qué paso del proceso se encuentra el cliente:

- Cada **estado** del diagrama BPMN es una función en `main.py` (despachador `ESTADOS`).
- Cada **compuerta (gateway)** es una estructura `if/elif` que devuelve el próximo estado.
- Cada **regla de negocio (RN-01 … RN-13)** se valida en tiempo de ejecución.

Así, el código puede leerse siguiendo el diagrama: el BPMN actúa como "contrato" del software.

**Robustez (caminos infelices).** El bot maneja entradas inválidas sin romperse: texto donde se
espera un número, opción fuera de rango, campo vacío, nombre o teléfono mal formados, torta sin
stock y turno completo. Además, el cliente puede escribir `cancelar` en cualquier paso para
abortar el pedido en curso y volver al menú principal (flujo de excepción).

## Stack

- **Lenguaje:** Python 3 (solo librería estándar: `csv`, `os`, `datetime`). No requiere instalar
  dependencias externas.
- **Plataforma:** simulación por consola (CLI). El diseño separa la lógica de estados de la
  interfaz, por lo que es portable a Telegram/WhatsApp reemplazando solo la capa de
  entrada/salida.
- **Persistencia:** archivos CSV como base de datos simulada (tortas, pedidos, detalle y turnos).

## Cómo desplegar y ejecutar

Requiere Python 3 instalado. Desde la carpeta del proyecto:

```bash
python main.py
```

Los archivos CSV deben estar en la misma carpeta que `main.py` (el programa los lee al iniciar y
los actualiza al confirmar un pedido).

## Estructura del repositorio

```
chatbot_pasteleria/
├── main.py                          # Código fuente: máquina de estados del chatbot
├── tortas.csv                       # Persistencia: catálogo y stock de tortas
├── pedidos.csv                      # Persistencia: pedidos registrados
├── detalle_pedidos.csv              # Persistencia: líneas de cada pedido (torta y cantidad)
├── turnos.csv                       # Persistencia: cupo de pedidos por fecha y turno
├── as_is_pasteleria.png             # Diagrama BPMN 2.0 — proceso actual (AS-IS)
├── bpmn_pasteleria.png              # Diagrama BPMN 2.0 — proceso propuesto (TO-BE)
├── capturas_oe/                     # Capturas de las consultas a la IA (ia_1.png, ia_2.png)
├── Informe_TPI_OE_Pasteleria.pdf    # Informe técnico (PDF)
└── README.md
```

## Reglas de negocio implementadas

| Regla | Descripción |
|---|---|
| RN-01 | Nombre y apellido válidos (solo letras y guion) |
| RN-02 | Teléfono válido (solo dígitos, 6 a 15) |
| RN-03 / RN-04 | Mostrar y seleccionar una de 5 fechas desde el día siguiente |
| RN-05 | Turnos disponibles: 09:00–12:00 y 13:00–17:00 |
| RN-06 / RN-07 | Máximo 10 pedidos por turno; si está completo, elegir otro |
| RN-08 / RN-09 | Verificar stock antes de agregar; si no hay, elegir otra torta |
| RN-10 | Un pedido puede contener varias tortas |
| RN-11 | Seleccionar forma de pago |
| RN-12 | Generar identificador único de pedido (PED-XXXX) |
| RN-13 | Generar comprobante y almacenar el pedido |

## Manual de usuario

| Acción | Cómo |
|---|---|
| Iniciar | Ejecutar `python main.py` y elegir **1. Realizar un pedido**. |
| Elegir tortas | Ingresar el número de la torta; repetir respondiendo **s** a "¿Agregar otra?". |
| Confirmar | Cargar nombre, teléfono, fecha, turno y forma de pago; el bot emite el comprobante. |
| Abortar pedido | Escribir **cancelar** en cualquier paso: descarta el carrito y vuelve al menú principal. |
| Salir | Opción **2** del menú. |

## Documentación

El informe técnico completo (descripción del proceso, AS-IS/TO-BE, reglas de negocio, diagramas
BPMN 2.0, máquina de estados, diccionario de datos, diseño de persistencia, pruebas de estrés,
herramientas de IA utilizadas y manual de usuario) está en
[`Informe_TPI_OE_Pasteleria.pdf`](Informe_TPI_OE_Pasteleria.pdf).

