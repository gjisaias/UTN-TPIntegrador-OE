# Chatbot Pastelería "La Básica" — Simulador de pedidos Take Away

Trabajo Práctico Integrador de **Organización Empresarial** (TUP a Distancia).

Como consultores tecnológicos, se identificó un **proceso administrativo manual e ineficiente**
—la gestión de pedidos de tortas para retiro programado— y se lo automatizó mediante un
**chatbot** cuya lógica responde fielmente a un modelo de procesos **BPMN 2.0**. La entrega es
una **simulación de proceso** por consola.

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
(manual, actual) y **TO-BE** (automatizado)— en notación BPMN 2.0.

## Arquitectura: del BPMN al código

La lógica está implementada como una **máquina de estados**, de modo que el bot "tiene memoria"
y sabe en qué paso del proceso se encuentra el cliente:

- Cada **estado** del diagrama BPMN es una función en `main.py`.
- Cada **compuerta (gateway)** es una estructura `if/elif` que devuelve el próximo estado.
- Cada **regla de negocio (RN-01 … RN-13)** se valida en tiempo de ejecución.

Así, el código puede leerse siguiendo el diagrama: el BPMN actúa como "contrato" del software.
El cliente puede escribir `cancelar` en cualquier paso para abortar el pedido en curso y volver
al menú principal (**camino infeliz** / flujo de excepción).

## Stack

- **Lenguaje:** Python 3 (solo librería estándar: `csv`, `os`, `datetime`).
- **Plataforma:** simulación por consola (CLI). El diseño separa la lógica de estados de la
  interfaz, por lo que es portable a Telegram/WhatsApp reemplazando solo la capa de
  entrada/salida.
- **Persistencia:** archivos CSV como base de datos simulada (tortas, pedidos, detalle y turnos).

## Cómo desplegar y ejecutar

Requiere Python 3 instalado. Desde la carpeta del proyecto:

```bash
python main.py
```

Los archivos CSV deben estar en la misma carpeta que `main.py` (el programa los lee al iniciar).
No requiere instalar dependencias externas.

## Estructura del repositorio

```
chatbot_pasteleria/
├── main.py                          # Código fuente: máquina de estados del chatbot
├── tortas.csv                       # Persistencia: catálogo y stock de tortas
├── pedidos.csv                      # Persistencia: pedidos registrados
├── detalle_pedidos.csv              # Persistencia: líneas de cada pedido (torta y cantidad)
├── turnos.csv                       # Persistencia: cupo de pedidos por fecha y turno
├── as_is_pasteleria.drawio          # Diagrama BPMN 2.0 — proceso actual (AS-IS)
├── bpmn_pasteleria.drawio           # Diagrama BPMN 2.0 — proceso propuesto (TO-BE)
├── capturas_oe/                     # Diagramas exportados y capturas de uso de IA
├── Informe_TPI_OE_Pasteleria.pdf    # Informe técnico (PDF)
└── README.md
```

## Reglas de negocio implementadas

RN-01 nombre/apellido válidos · RN-02 teléfono válido · RN-03/04 cinco fechas desde el día
siguiente · RN-05 turnos 09–12 y 13–17 · RN-06/07 máximo 10 pedidos por turno · RN-08/09
verificación de stock · RN-10 múltiples tortas · RN-11 forma de pago · RN-12 ID único ·
RN-13 comprobante y almacenamiento.

## Manual de usuario (resumen)

| Acción | Cómo |
|---|---|
| Iniciar | Ejecutar `python main.py` y elegir **1. Realizar un pedido**. |
| Elegir tortas | Ingresar el número de la torta; repetir respondiendo **s** a "¿Agregar otra?". |
| Confirmar | Cargar nombre, teléfono, fecha, turno y forma de pago; el bot emite el comprobante. |
| Abortar pedido | Escribir **cancelar** en cualquier paso: descarta el carrito y vuelve al menú principal. |
| Salir | Opción **2** del menú. |

## Documentación

El informe técnico completo (descripción del proceso, AS-IS/TO-BE, reglas de negocio, diagramas
BPMN 2.0, máquina de estados, diccionario de datos, persistencia, pruebas de estrés, herramientas
de IA utilizadas y manual de usuario) está en
[`Informe_TPI_OE_Pasteleria.pdf`](Informe_TPI_OE_Pasteleria.pdf).
