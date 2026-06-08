# ============================================================================
#  CHATBOT PASTELERIA "LA BASICA" - Simulador de pedidos Take Away
#  TPI Organizacion Empresarial - TUP a Distancia
#
#  El programa implementa el proceso modelado en el BPMN como una MAQUINA DE
#  ESTADOS: cada estado es una funcion que devuelve el nombre del proximo
#  estado, y cada compuerta (gateway) del BPMN se traduce en un if/elif.
#  De esta forma el codigo puede leerse siguiendo el diagrama BPMN.
# ============================================================================

import csv
import os
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# CONFIGURACION Y RUTAS DE ARCHIVOS (persistencia en CSV)
# ---------------------------------------------------------------------------
CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_TORTAS = os.path.join(CARPETA, "tortas.csv")
ARCHIVO_PEDIDOS = os.path.join(CARPETA, "pedidos.csv")
ARCHIVO_DETALLE = os.path.join(CARPETA, "detalle_pedidos.csv")
ARCHIVO_TURNOS = os.path.join(CARPETA, "turnos.csv")

COL_TORTAS = ["id_torta", "nombre", "precio", "stock"]
COL_PEDIDOS = ["id_pedido", "fecha_pedido", "cliente", "telefono",
               "fecha_retiro", "turno", "forma_pago", "total", "estado"]
COL_DETALLE = ["id_pedido", "id_torta", "cantidad", "subtotal"]
COL_TURNOS = ["fecha", "turno", "pedidos_registrados"]

# Reglas de negocio parametrizadas.
TURNOS_DISPONIBLES = ["09:00 a 12:00", "13:00 a 17:00"]   # RN-05
CAPACIDAD_TURNO = 10                                       # RN-06
FORMAS_PAGO = ["Efectivo", "Online"]                       # RN-11
CANT_FECHAS = 5                                            # RN-03

DIAS_ES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]


class AbortarPedido(Exception):
    """Se lanza cuando el usuario escribe 'cancelar' para abortar la carga.

    No es una cancelacion de negocio: el pedido aun no se confirmo ni se
    persistio nada, asi que solo se descarta el carrito y se vuelve al menu.
    """
    pass


def leer(mensaje):
    """Lee y limpia el texto. Si el usuario escribe 'cancelar', aborta la carga."""
    texto = input(mensaje).strip()
    if texto.lower() == "cancelar":
        raise AbortarPedido()
    return texto


def pedir_si_no(mensaje):
    """Pide una respuesta limitada estrictamente a 's' o 'n'."""
    while True:
        respuesta = leer(mensaje).lower()
        if respuesta == "s":
            return True
        if respuesta == "n":
            return False
        print("  > Responde solamente 's' o 'n'.")


# ===========================================================================
# CAPA DE PERSISTENCIA (lectura/escritura de los CSV)
# ===========================================================================
def cargar_tortas():
    """Devuelve la lista de tortas como diccionarios (VALIDACION_STOCK)."""
    tortas = []
    with open(ARCHIVO_TORTAS, "r", encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            tortas.append({
                "id_torta": int(fila["id_torta"]),
                "nombre": fila["nombre"],
                "precio": float(fila["precio"]),
                "stock": int(fila["stock"]),
            })
    return tortas


def guardar_tortas(tortas):
    """Reescribe tortas.csv (usado al descontar stock)."""
    with open(ARCHIVO_TORTAS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COL_TORTAS)
        w.writeheader()
        w.writerows(tortas)


def get_cupo(fecha_iso, turno):
    """Lee cuantos pedidos tiene un turno (0 si no existe la fila). RN-06."""
    if not os.path.exists(ARCHIVO_TURNOS):
        return 0
    with open(ARCHIVO_TURNOS, "r", encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            if fila["fecha"] == fecha_iso and fila["turno"] == turno:
                return int(fila["pedidos_registrados"])
    return 0


def set_cupo(fecha_iso, turno, nuevo_valor):
    """Crea o actualiza la fila del turno con su nueva cantidad de pedidos."""
    filas = []
    encontrada = False
    if os.path.exists(ARCHIVO_TURNOS):
        with open(ARCHIVO_TURNOS, "r", encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f))
    for fila in filas:
        if fila["fecha"] == fecha_iso and fila["turno"] == turno:
            fila["pedidos_registrados"] = str(nuevo_valor)
            encontrada = True
    if not encontrada:
        filas.append({"fecha": fecha_iso, "turno": turno,
                      "pedidos_registrados": str(nuevo_valor)})
    with open(ARCHIVO_TURNOS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COL_TURNOS)
        w.writeheader()
        w.writerows(filas)


def guardar_pedido(pedido):
    """Agrega una fila a pedidos.csv (RN-13)."""
    with open(ARCHIVO_PEDIDOS, "a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=COL_PEDIDOS).writerow(pedido)


def guardar_detalles(detalles):
    """Agrega las lineas del carrito a detalle_pedidos.csv (RN-13)."""
    with open(ARCHIVO_DETALLE, "a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=COL_DETALLE).writerows(detalles)


# ===========================================================================
# VALIDACIONES (reglas de negocio sobre la entrada del usuario)
# ===========================================================================
def nombre_valido(texto):
    """RN-01: nombre y apellido, solo letras y al menos dos palabras."""
    partes = texto.split()
    if len(partes) < 2:
        return False
    return all(p.replace("-", "").isalpha() for p in partes)


def telefono_valido(texto):
    """RN-02: solo digitos, entre 6 y 15 caracteres."""
    return texto.isdigit() and 6 <= len(texto) <= 15


def generar_id_pedido():
    """RN-12: identificador unico de pedido (correlativo PED-XXXX)."""
    maximo = 0
    if os.path.exists(ARCHIVO_PEDIDOS):
        with open(ARCHIVO_PEDIDOS, "r", encoding="utf-8", newline="") as f:
            for fila in csv.DictReader(f):
                try:
                    numero = int(fila["id_pedido"].split("-")[1])
                    maximo = max(maximo, numero)
                except (IndexError, ValueError):
                    pass
    return f"PED-{maximo + 1:04d}"


def pedir_opcion(mensaje, cantidad):
    """Pide un numero entre 1 y 'cantidad'. Maneja E-01 y E-02."""
    while True:
        dato = leer(mensaje)
        if not dato:
            print("  > El campo no puede quedar vacio.")          # E-03
            continue
        if not dato.isdigit():
            print("  > Ingresa el numero de una opcion valida.")  # E-01
            continue
        numero = int(dato)
        if 1 <= numero <= cantidad:
            return numero
        print(f"  > Esa opcion no existe. Elegi entre 1 y {cantidad}.")  # E-02


def cantidad_en_carrito(carrito, id_torta):
    """Cuantas unidades de esa torta ya hay en el carrito (coherencia stock)."""
    return carrito.get(id_torta, 0)


def resumen_carrito(ctx):
    """Devuelve el carrito agrupado como '2 x Chocolate, 1 x Frutilla'."""
    partes = []
    for id_torta, cantidad in ctx["carrito"].items():
        nombre = next(t["nombre"] for t in ctx["tortas"]
                      if t["id_torta"] == id_torta)
        partes.append(f"{cantidad} x {nombre}")
    return ", ".join(partes) if partes else "(vacio)"


# ===========================================================================
# ESTADOS DE LA MAQUINA  (cada funcion devuelve el proximo estado)
# ===========================================================================
def estado_inicio(ctx):
    """INICIO: saludo y menu principal."""
    print("\n" + "=" * 60)
    print("   PASTELERIA LA BASICA - Pedidos de tortas (Take Away)")
    print("=" * 60)
    print("1. Realizar un pedido")
    print("2. Salir")
    opcion = pedir_opcion("Elegi una opcion: ", 2)
    if opcion == 1:
        print("\n(Podes escribir 'cancelar' en cualquier momento para abortar "
              "el pedido y volver al menu.)")
        ctx["carrito"] = {}      # id_torta -> cantidad
        ctx["tortas"] = cargar_tortas()
        return "SELECCION_TORTA"
    return "SALIR"


def estado_seleccion_torta(ctx):
    """SELECCION_TORTA: muestra el menu de tortas y toma una eleccion."""
    print("\n--- Menu de tortas ---")
    for i, t in enumerate(ctx["tortas"], start=1):
        disp = t["stock"] - cantidad_en_carrito(ctx["carrito"], t["id_torta"])
        estado_stock = f"{disp} disp." if disp > 0 else "SIN STOCK"
        print(f"{i}. {t['nombre']:<12} ${t['precio']:>8.0f}   ({estado_stock})")
    opcion = pedir_opcion("Elegi una torta: ", len(ctx["tortas"]))
    ctx["torta_elegida"] = ctx["tortas"][opcion - 1]
    return "VALIDACION_STOCK"


def estado_validacion_stock(ctx):
    """VALIDACION_STOCK / Gateway G1: hay stock? (RN-08/09)."""
    t = ctx["torta_elegida"]
    disponible = t["stock"] - cantidad_en_carrito(ctx["carrito"], t["id_torta"])
    if disponible > 0:
        return "CARRITO"
    print(f"  > No queda stock de {t['nombre']}. Elegi otra torta.")  # E-06
    return "SELECCION_TORTA"


def estado_carrito(ctx):
    """CARRITO / Gateway G2: agrega la torta y pregunta si sigue (RN-10)."""
    t = ctx["torta_elegida"]
    id_t = t["id_torta"]
    ctx["carrito"][id_t] = cantidad_en_carrito(ctx["carrito"], id_t) + 1
    print(f"  + Agregada: {t['nombre']}.")
    print("  Carrito actual: " + resumen_carrito(ctx))
    if pedir_si_no("Agregar otra torta? (s/n): "):
        return "SELECCION_TORTA"
    return "INGRESO_NOMBRE"


def estado_ingreso_nombre(ctx):
    """INGRESO_NOMBRE: pide nombre y apellido."""
    ctx["nombre_tmp"] = leer("Nombre y apellido: ")
    return "VALIDACION_NOMBRE"


def estado_validacion_nombre(ctx):
    """VALIDACION_NOMBRE / Gateway G3 (RN-01)."""
    if nombre_valido(ctx["nombre_tmp"]):
        ctx["cliente"] = ctx["nombre_tmp"].title()
        return "INGRESO_TELEFONO"
    print("  > Ingresa nombre y apellido (solo letras).")  # E-04
    return "INGRESO_NOMBRE"


def estado_ingreso_telefono(ctx):
    """INGRESO_TELEFONO: pide el telefono."""
    ctx["tel_tmp"] = leer("Telefono (solo numeros): ")
    return "VALIDACION_TELEFONO"


def estado_validacion_telefono(ctx):
    """VALIDACION_TELEFONO / Gateway G4 (RN-02)."""
    if telefono_valido(ctx["tel_tmp"]):
        ctx["telefono"] = ctx["tel_tmp"]
        return "SELECCION_FECHA"
    print("  > El telefono debe tener solo numeros (6 a 15).")  # E-05
    return "INGRESO_TELEFONO"


def estado_seleccion_fecha(ctx):
    """SELECCION_FECHA: ofrece 5 fechas desde manana (RN-03/04)."""
    print("\n--- Fechas de retiro disponibles ---")
    ctx["fechas"] = []
    hoy = date.today()
    for i in range(1, CANT_FECHAS + 1):
        f = hoy + timedelta(days=i)
        ctx["fechas"].append(f)
        print(f"{i}. {DIAS_ES[f.weekday()]} {f.strftime('%d/%m/%Y')}")
    opcion = pedir_opcion("Elegi una fecha: ", CANT_FECHAS)
    ctx["fecha_retiro"] = ctx["fechas"][opcion - 1]
    return "SELECCION_TURNO"


def estado_seleccion_turno(ctx):
    """SELECCION_TURNO / Gateway G5: valida cupo del turno (RN-05/06/07)."""
    print("\n--- Turnos disponibles ---")
    fecha_iso = ctx["fecha_retiro"].isoformat()
    for i, turno in enumerate(TURNOS_DISPONIBLES, start=1):
        ocupados = get_cupo(fecha_iso, turno)
        libres = CAPACIDAD_TURNO - ocupados
        print(f"{i}. {turno}   ({libres} lugares)")
    opcion = pedir_opcion("Elegi un turno: ", len(TURNOS_DISPONIBLES))
    turno = TURNOS_DISPONIBLES[opcion - 1]
    if get_cupo(fecha_iso, turno) < CAPACIDAD_TURNO:   # Gateway G5
        ctx["turno"] = turno
        return "SELECCION_PAGO"
    print("  > Ese turno esta completo. Elegi otro.")  # E-07 / RN-07
    return "SELECCION_TURNO"


def estado_seleccion_pago(ctx):
    """SELECCION_PAGO: toma la forma de pago (RN-11)."""
    print("\n--- Forma de pago ---")
    for i, fp in enumerate(FORMAS_PAGO, start=1):
        print(f"{i}. {fp}")
    opcion = pedir_opcion("Elegi forma de pago: ", len(FORMAS_PAGO))
    ctx["forma_pago"] = FORMAS_PAGO[opcion - 1]
    return "GENERAR_PEDIDO"


def estado_generar_pedido(ctx):
    """GENERAR_PEDIDO: ID, descuenta stock, suma cupo y persiste (RN-12/13)."""
    id_pedido = generar_id_pedido()
    fecha_iso = ctx["fecha_retiro"].isoformat()

    # Descuenta stock y arma el detalle.
    detalles = []
    total = 0.0
    tortas = ctx["tortas"]
    for id_torta, cantidad in ctx["carrito"].items():
        torta = next(t for t in tortas if t["id_torta"] == id_torta)
        torta["stock"] -= cantidad
        subtotal = torta["precio"] * cantidad
        total += subtotal
        detalles.append({"id_pedido": id_pedido, "id_torta": id_torta,
                         "cantidad": cantidad, "subtotal": subtotal})
    guardar_tortas(tortas)

    # Suma un pedido al cupo del turno (RN-06).
    set_cupo(fecha_iso, ctx["turno"], get_cupo(fecha_iso, ctx["turno"]) + 1)

    # Persiste el pedido y su detalle.
    pedido = {
        "id_pedido": id_pedido,
        "fecha_pedido": date.today().isoformat(),
        "cliente": ctx["cliente"],
        "telefono": ctx["telefono"],
        "fecha_retiro": fecha_iso,
        "turno": ctx["turno"],
        "forma_pago": ctx["forma_pago"],
        "total": total,
        "estado": "Confirmado",
    }
    guardar_pedido(pedido)
    guardar_detalles(detalles)
    ctx["pedido"] = pedido
    return "CONFIRMADO"


def estado_confirmado(ctx):
    """CONFIRMADO: emite el comprobante (RN-13)."""
    p = ctx["pedido"]
    print("\n" + "=" * 60)
    print("   COMPROBANTE DE PEDIDO")
    print("=" * 60)
    print(f"  N de pedido : {p['id_pedido']}")
    print(f"  Cliente     : {p['cliente']}  ({p['telefono']})")
    print(f"  Detalle     : {resumen_carrito(ctx)}")
    print(f"  Retiro      : {p['fecha_retiro']}  -  {p['turno']}")
    print(f"  Pago        : {p['forma_pago']}")
    print(f"  TOTAL       : ${p['total']:.0f}")
    print("=" * 60)
    print("  Gracias por tu compra! Guarda el numero de pedido.")
    return "FIN_OK"


# ===========================================================================
# DESPACHADOR DE LA MAQUINA DE ESTADOS
# ===========================================================================
ESTADOS = {
    "INICIO": estado_inicio,
    "SELECCION_TORTA": estado_seleccion_torta,
    "VALIDACION_STOCK": estado_validacion_stock,
    "CARRITO": estado_carrito,
    "INGRESO_NOMBRE": estado_ingreso_nombre,
    "VALIDACION_NOMBRE": estado_validacion_nombre,
    "INGRESO_TELEFONO": estado_ingreso_telefono,
    "VALIDACION_TELEFONO": estado_validacion_telefono,
    "SELECCION_FECHA": estado_seleccion_fecha,
    "SELECCION_TURNO": estado_seleccion_turno,
    "SELECCION_PAGO": estado_seleccion_pago,
    "GENERAR_PEDIDO": estado_generar_pedido,
    "CONFIRMADO": estado_confirmado,
}

ESTADOS_FINALES = ("FIN_OK", "SALIR")


def main():
    """Bucle principal: ejecuta la maquina de estados hasta un estado final."""
    while True:
        ctx = {}
        estado = "INICIO"
        while estado not in ESTADOS_FINALES:
            try:
                estado = ESTADOS[estado](ctx)
            except AbortarPedido:
                print("\n  Pedido abortado. Volviendo al menu principal...")
                estado = "INICIO"
        if estado == "SALIR":
            print("\nHasta luego!")
            break


if __name__ == "__main__":
    main()
