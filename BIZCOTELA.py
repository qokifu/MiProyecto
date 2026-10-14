"""
Sistema de gestión de pedidos - Bizcotela Cakes
Python + Tkinter (solo librería estándar, no necesita instalar nada)

Requerimientos cubiertos:
RF01 registrar clientes      RF02 registrar productos
RF03 registrar pedidos       RF04 personalizar pedido
RF05 calcular pedido         RF06 validar información
RF07 consultar pedidos       RF08 actualizar estado
RF09 generar comprobante     RF10 consultar historial
"""

import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, filedialog

# ---------------------------------------------------------------------------
# configuración y datos base
# ---------------------------------------------------------------------------
ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bizcotela_datos.json")

ESTADOS = ["Pendiente", "Confirmado", "En preparación", "Listo", "Entregado"]
METODOS_PAGO = ["Yape", "Efectivo"]

# nombre de la opción -> monto adicional (S/) o multiplicador (tamaño)
SABORES = {"Vainilla": 0, "Chocolate": 0, "Naranja": 0, "Zanahoria": 3, "Red velvet": 5}
TAMANOS = {"Pequeño (8 porciones)": 1.0, "Mediano (15 porciones)": 1.6, "Grande (25 porciones)": 2.4}
RELLENOS = {"Manjar": 0, "Crema pastelera": 4, "Fudge": 5, "Fresa": 5, "Lúcuma": 6}
DECORACIONES = {"Sencilla": 0, "Flores de crema": 15, "Fondant": 25, "Personalizada": 35}

datos = {"clientes": [], "productos": [], "pedidos": [], "contador_pedidos": 0}


def cargar_datos():
    global datos
    if os.path.exists(ARCHIVO):
        try:
            with open(ARCHIVO, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except (json.JSONDecodeError, OSError):
            messagebox.showwarning("Aviso", "No se pudo leer el archivo de datos. Se iniciará vacío.")


def guardar_datos():
    try:
        with open(ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except OSError:
        messagebox.showerror("Error", "No se pudo guardar la información en el archivo.")


# ---------------------------------------------------------------------------
# funciones de lógica (cálculos, búsquedas, comprobante)
# ---------------------------------------------------------------------------
def calcular_item(precio_base, sabor, tamano, relleno, decoracion, cantidad):
    """Devuelve (precio_unitario, subtotal)."""
    unitario = precio_base * TAMANOS[tamano] + SABORES[sabor] + RELLENOS[relleno] + DECORACIONES[decoracion]
    unitario = round(unitario, 2)
    return unitario, round(unitario * cantidad, 2)


def buscar_producto(nombre):
    for p in datos["productos"]:
        if p["nombre"] == nombre:
            return p
    return None


def buscar_pedido(codigo):
    codigo = codigo.strip().upper()
    for p in datos["pedidos"]:
        if p["codigo"] == codigo:
            return p
    return None


def texto_comprobante(p):
    linea = "=" * 52
    t = [linea,
         "        BIZCOTELA CAKES - Pastelería y Sangucheria",
         "              Carmen de la Legua Reynoso, Callao",
         linea,
         f"Comprobante / Pedido : {p['codigo']}",
         f"Fecha de registro    : {p['fecha_registro']}",
         f"Fecha de entrega     : {p['fecha_entrega']}",
         "-" * 52,
         f"Cliente  : {p['cliente']}",
         f"DNI      : {p['dni']}",
         f"Celular  : {p['celular']}",
         "-" * 52,
         "DETALLE DEL PEDIDO"]
    for i, it in enumerate(p["items"], 1):
        t.append(f"{i}. {it['producto']}  x{it['cantidad']}")
        t.append(f"   Sabor: {it['sabor']} | Tamaño: {it['tamano']}")
        t.append(f"   Relleno: {it['relleno']} | Decoración: {it['decoracion']}")
        t.append(f"   P. unitario: S/ {it['unitario']:.2f}   Subtotal: S/ {it['subtotal']:.2f}")
    t.append("-" * 52)
    t.append(f"Dedicatoria : {p['dedicatoria'] if p['dedicatoria'] else '(sin dedicatoria)'}")
    t.append(f"Método pago : {p['metodo_pago']}")
    t.append(f"Estado      : {p['estado']}")
    t.append(linea)
    t.append(f"TOTAL A PAGAR: S/ {p['total']:.2f}")
    t.append(linea)
    return "\n".join(t)


# ---------------------------------------------------------------------------
# utilidades de interfaz
# ---------------------------------------------------------------------------
COLOR_FONDO = "#f6fbfa"
COLOR_MARRON = "#4a2423"
COLOR_MENTA = "#b5e8dc"


def nueva_ventana(raiz, titulo, ancho, alto):
    v = tk.Toplevel(raiz)
    v.title(titulo)
    v.configure(bg=COLOR_FONDO, padx=15, pady=15)
    x = (v.winfo_screenwidth() - ancho) // 2
    y = (v.winfo_screenheight() - alto) // 2
    v.geometry(f"{ancho}x{alto}+{x}+{y}")
    v.transient(raiz)
    v.grab_set()
    return v


def etiqueta(parent, texto, fila, col=0):
    tk.Label(parent, text=texto, bg=COLOR_FONDO, anchor="w").grid(row=fila, column=col, sticky="w", pady=4, padx=(0, 8))


def mostrar_texto(raiz, titulo, texto, guardable=False, nombre_archivo="comprobante.txt"):
    v = nueva_ventana(raiz, titulo, 520, 560)
    txt = tk.Text(v, font=("Consolas", 10), wrap="none", height=26)
    txt.insert("1.0", texto)
    txt.config(state="disabled")
    txt.pack(fill="both", expand=True)
    barra = tk.Frame(v, bg=COLOR_FONDO)
    barra.pack(pady=(10, 0))
    if guardable:
        def guardar():
            ruta = filedialog.asksaveasfilename(parent=v, defaultextension=".txt", initialfile=nombre_archivo,
                                                filetypes=[("Texto", "*.txt")])
            if ruta:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(texto)
                messagebox.showinfo("Listo", "Comprobante guardado correctamente.", parent=v)
        ttk.Button(barra, text="Guardar como .txt", command=guardar).pack(side="left", padx=5)
    ttk.Button(barra, text="Cerrar", command=v.destroy).pack(side="left", padx=5)


# ---------------------------------------------------------------------------
# opción 1: registrar cliente (RF01, RF06)
# ---------------------------------------------------------------------------
def registrar_cliente(raiz):
    v = nueva_ventana(raiz, "Registrar cliente", 380, 260)
    etiqueta(v, "Nombre completo:", 0)
    etiqueta(v, "DNI (8 dígitos):", 1)
    etiqueta(v, "Celular (9 dígitos):", 2)
    e_nombre, e_dni, e_cel = ttk.Entry(v, width=28), ttk.Entry(v, width=28), ttk.Entry(v, width=28)
    e_nombre.grid(row=0, column=1)
    e_dni.grid(row=1, column=1)
    e_cel.grid(row=2, column=1)

    def guardar():
        nombre, dni, cel = e_nombre.get().strip(), e_dni.get().strip(), e_cel.get().strip()
        if not nombre or not dni or not cel:
            messagebox.showerror("Campo obligatorio", "Debe completar todos los campos.", parent=v)
            return
        if not dni.isdigit() or len(dni) != 8:
            messagebox.showerror("DNI inválido", "El DNI debe tener 8 dígitos numéricos.", parent=v)
            return
        if not cel.isdigit() or len(cel) != 9:
            messagebox.showerror("Celular inválido", "El celular debe tener 9 dígitos numéricos.", parent=v)
            return
        if any(c["dni"] == dni for c in datos["clientes"]):
            messagebox.showerror("Cliente repetido", "Ya existe un cliente con ese DNI.", parent=v)
            return
        datos["clientes"].append({"nombre": nombre, "dni": dni, "celular": cel})
        guardar_datos()
        messagebox.showinfo("Éxito", "Cliente registrado correctamente.", parent=v)
        v.destroy()

    f = tk.Frame(v, bg=COLOR_FONDO)
    f.grid(row=3, column=0, columnspan=2, pady=20)
    ttk.Button(f, text="Guardar", command=guardar).pack(side="left", padx=5)
    ttk.Button(f, text="Cancelar", command=v.destroy).pack(side="left", padx=5)


# ---------------------------------------------------------------------------
# opción 2: registrar producto (RF02, RF06)
# ---------------------------------------------------------------------------
def registrar_producto(raiz):
    v = nueva_ventana(raiz, "Registrar producto", 380, 300)
    etiqueta(v, "Nombre del producto:", 0)
    etiqueta(v, "Categoría:", 1)
    etiqueta(v, "Precio base (S/):", 2)
    etiqueta(v, "Stock:", 3)
    e_nombre = ttk.Entry(v, width=28)
    cb_cat = ttk.Combobox(v, width=25, state="readonly", values=["Torta", "Postre", "Cupcakes", "Sanguchería", "Otro"])
    cb_cat.current(0)
    e_precio, e_stock = ttk.Entry(v, width=28), ttk.Entry(v, width=28)
    e_nombre.grid(row=0, column=1)
    cb_cat.grid(row=1, column=1)
    e_precio.grid(row=2, column=1)
    e_stock.grid(row=3, column=1)

    def guardar():
        nombre = e_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Campo obligatorio", "Debe ingresar el nombre del producto.", parent=v)
            return
        try:
            precio = float(e_precio.get().strip().replace(",", "."))
            if precio <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Precio inválido", "Ingrese un precio numérico mayor a 0.", parent=v)
            return
        try:
            stock = int(e_stock.get().strip())
            if stock < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Stock inválido", "Ingrese un stock entero mayor o igual a 0.", parent=v)
            return
        if buscar_producto(nombre):
            messagebox.showerror("Producto repetido", "Ya existe un producto con ese nombre.", parent=v)
            return
        datos["productos"].append({"nombre": nombre, "categoria": cb_cat.get(), "precio": round(precio, 2), "stock": stock})
        guardar_datos()
        messagebox.showinfo("Éxito", "Producto registrado correctamente.", parent=v)
        v.destroy()

    f = tk.Frame(v, bg=COLOR_FONDO)
    f.grid(row=4, column=0, columnspan=2, pady=20)
    ttk.Button(f, text="Guardar", command=guardar).pack(side="left", padx=5)
    ttk.Button(f, text="Cancelar", command=v.destroy).pack(side="left", padx=5)


# ---------------------------------------------------------------------------
# opción 3: registrar pedido (RF03, RF04, RF05, RF06)
# ---------------------------------------------------------------------------
def registrar_pedido(raiz):
    if not datos["clientes"]:
        messagebox.showwarning("Sin clientes", "Primero debe registrar al menos un cliente.")
        return
    if not datos["productos"]:
        messagebox.showwarning("Sin productos", "Primero debe registrar al menos un producto.")
        return

    v = nueva_ventana(raiz, "Registrar pedido", 760, 700)
    items = []

    # --- cliente ---
    etiqueta(v, "Cliente:", 0)
    lista_clientes = [f"{c['nombre']} - {c['dni']}" for c in datos["clientes"]]
    cb_cliente = ttk.Combobox(v, width=40, state="readonly", values=lista_clientes)
    cb_cliente.grid(row=0, column=1, columnspan=3, sticky="w")

    # --- personalización ---
    etiqueta(v, "Producto:", 1)
    cb_prod = ttk.Combobox(v, width=28, state="readonly", values=[p["nombre"] for p in datos["productos"]])
    cb_prod.grid(row=1, column=1, sticky="w")
    etiqueta(v, "Cantidad:", 1, 2)
    e_cant = ttk.Entry(v, width=8)
    e_cant.insert(0, "1")
    e_cant.grid(row=1, column=3, sticky="w")

    etiqueta(v, "Sabor:", 2)
    cb_sabor = ttk.Combobox(v, width=28, state="readonly", values=list(SABORES))
    cb_sabor.current(0)
    cb_sabor.grid(row=2, column=1, sticky="w")
    etiqueta(v, "Tamaño:", 2, 2)
    cb_tam = ttk.Combobox(v, width=22, state="readonly", values=list(TAMANOS))
    cb_tam.current(0)
    cb_tam.grid(row=2, column=3, sticky="w")

    etiqueta(v, "Relleno:", 3)
    cb_rell = ttk.Combobox(v, width=28, state="readonly", values=list(RELLENOS))
    cb_rell.current(0)
    cb_rell.grid(row=3, column=1, sticky="w")
    etiqueta(v, "Decoración:", 3, 2)
    cb_deco = ttk.Combobox(v, width=22, state="readonly", values=list(DECORACIONES))
    cb_deco.current(0)
    cb_deco.grid(row=3, column=3, sticky="w")

    lbl_preview = tk.Label(v, text="Subtotal del ítem: S/ 0.00", bg=COLOR_FONDO, fg=COLOR_MARRON, font=("Segoe UI", 10, "bold"))
    lbl_preview.grid(row=4, column=0, columnspan=3, sticky="w", pady=6)

    def leer_cantidad():
        try:
            c = int(e_cant.get().strip())
            return c if c > 0 else None
        except ValueError:
            return None

    def actualizar_preview(_evento=None):
        prod = buscar_producto(cb_prod.get())
        cant = leer_cantidad()
        if prod and cant:
            _, sub = calcular_item(prod["precio"], cb_sabor.get(), cb_tam.get(), cb_rell.get(), cb_deco.get(), cant)
            lbl_preview.config(text=f"Subtotal del ítem: S/ {sub:.2f}")
        else:
            lbl_preview.config(text="Subtotal del ítem: S/ 0.00")

    for cb in (cb_prod, cb_sabor, cb_tam, cb_rell, cb_deco):
        cb.bind("<<ComboboxSelected>>", actualizar_preview)
    e_cant.bind("<KeyRelease>", actualizar_preview)

    # --- tabla de ítems ---
    columnas = ("producto", "sabor", "tamano", "relleno", "decoracion", "cant", "subtotal")
    tabla = ttk.Treeview(v, columns=columnas, show="headings", height=7)
    for col, ancho, txt in [("producto", 130, "Producto"), ("sabor", 85, "Sabor"), ("tamano", 130, "Tamaño"),
                            ("relleno", 90, "Relleno"), ("decoracion", 100, "Decoración"),
                            ("cant", 45, "Cant."), ("subtotal", 75, "Subtotal")]:
        tabla.heading(col, text=txt)
        tabla.column(col, width=ancho, anchor="center")
    tabla.grid(row=6, column=0, columnspan=4, sticky="we", pady=(5, 0))

    lbl_total = tk.Label(v, text="TOTAL: S/ 0.00", bg=COLOR_FONDO, fg=COLOR_MARRON, font=("Segoe UI", 13, "bold"))
    lbl_total.grid(row=7, column=0, columnspan=4, sticky="e", pady=6)

    def refrescar_tabla():
        tabla.delete(*tabla.get_children())
        for it in items:
            tabla.insert("", "end", values=(it["producto"], it["sabor"], it["tamano"], it["relleno"],
                                            it["decoracion"], it["cantidad"], f"S/ {it['subtotal']:.2f}"))
        total = sum(it["subtotal"] for it in items)
        lbl_total.config(text=f"TOTAL: S/ {total:.2f}")

    def agregar_item():
        prod = buscar_producto(cb_prod.get())
        if not prod:
            messagebox.showerror("Producto", "Seleccione un producto.", parent=v)
            return
        cant = leer_cantidad()
        if cant is None:
            messagebox.showerror("Cantidad inválida", "Ingrese una cantidad entera mayor a 0.", parent=v)
            return
        ya_pedido = sum(i["cantidad"] for i in items if i["producto"] == prod["nombre"])
        if cant + ya_pedido > prod["stock"]:
            messagebox.showerror("Stock insuficiente",
                                 f"Solo hay {prod['stock']} unidades de '{prod['nombre']}' disponibles.", parent=v)
            return
        unit, sub = calcular_item(prod["precio"], cb_sabor.get(), cb_tam.get(), cb_rell.get(), cb_deco.get(), cant)
        items.append({"producto": prod["nombre"], "sabor": cb_sabor.get(), "tamano": cb_tam.get(),
                      "relleno": cb_rell.get(), "decoracion": cb_deco.get(), "cantidad": cant,
                      "unitario": unit, "subtotal": sub})
        refrescar_tabla()

    def quitar_item():
        sel = tabla.selection()
        if not sel:
            messagebox.showinfo("Quitar", "Seleccione un ítem de la tabla.", parent=v)
            return
        del items[tabla.index(sel[0])]
        refrescar_tabla()

    barra_items = tk.Frame(v, bg=COLOR_FONDO)
    barra_items.grid(row=5, column=0, columnspan=4, sticky="w")
    ttk.Button(barra_items, text="Agregar al pedido", command=agregar_item).pack(side="left", padx=(0, 6))
    ttk.Button(barra_items, text="Quitar ítem seleccionado", command=quitar_item).pack(side="left")

    # --- datos finales ---
    etiqueta(v, "Dedicatoria:", 8)
    e_dedic = ttk.Entry(v, width=60)
    e_dedic.grid(row=8, column=1, columnspan=3, sticky="w")
    etiqueta(v, "Fecha de entrega (dd/mm/aaaa):", 9)
    e_fecha = ttk.Entry(v, width=15)
    e_fecha.grid(row=9, column=1, sticky="w")
    etiqueta(v, "Método de pago:", 9, 2)
    cb_pago = ttk.Combobox(v, width=15, state="readonly", values=METODOS_PAGO)
    cb_pago.current(0)
    cb_pago.grid(row=9, column=3, sticky="w")

    def confirmar():
        if not cb_cliente.get():
            messagebox.showerror("Cliente", "Debe seleccionar un cliente.", parent=v)
            return
        if not items:
            messagebox.showerror("Pedido vacío", "Agregue al menos un producto al pedido.", parent=v)
            return
        try:
            fecha = datetime.strptime(e_fecha.get().strip(), "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Fecha inválida", "Ingrese la fecha con el formato dd/mm/aaaa.", parent=v)
            return
        if fecha.date() < datetime.now().date():
            messagebox.showerror("Fecha inválida", "La fecha de entrega no puede ser anterior a hoy.", parent=v)
            return

        cliente = datos["clientes"][cb_cliente.current()]
        total = round(sum(i["subtotal"] for i in items), 2)
        pedido = {
            "codigo": f"PED-{datos['contador_pedidos'] + 1:04d}",
            "cliente": cliente["nombre"], "dni": cliente["dni"], "celular": cliente["celular"],
            "items": [dict(i) for i in items],
            "dedicatoria": e_dedic.get().strip(),
            "fecha_entrega": fecha.strftime("%d/%m/%Y"),
            "fecha_registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "metodo_pago": cb_pago.get(),
            "total": total,
            "estado": ESTADOS[0],
        }
        resumen = texto_comprobante(pedido)
        if messagebox.askyesno("Confirmar pedido", resumen + "\n\n¿Desea registrar este pedido?", parent=v):
            datos["contador_pedidos"] += 1
            for i in items:  # descontar stock
                buscar_producto(i["producto"])["stock"] -= i["cantidad"]
            datos["pedidos"].append(pedido)
            guardar_datos()
            messagebox.showinfo("Éxito", f"Pedido {pedido['codigo']} registrado correctamente.", parent=v)
            v.destroy()
        else:
            messagebox.showinfo("Cancelado", "Se canceló el registro del pedido.", parent=v)

    f = tk.Frame(v, bg=COLOR_FONDO)
    f.grid(row=10, column=0, columnspan=4, pady=15)
    ttk.Button(f, text="Registrar pedido", command=confirmar).pack(side="left", padx=5)
    ttk.Button(f, text="Cancelar", command=v.destroy).pack(side="left", padx=5)


# ---------------------------------------------------------------------------
# opción 4: consultar pedido (RF07)
# ---------------------------------------------------------------------------
def consultar_pedido(raiz):
    v = nueva_ventana(raiz, "Consultar pedido", 360, 160)
    etiqueta(v, "Código del pedido (ej. PED-0001):", 0)
    e_cod = ttk.Entry(v, width=20)
    e_cod.grid(row=1, column=0, sticky="w")

    def buscar():
        codigo = e_cod.get().strip()
        if not codigo:
            messagebox.showerror("Campo obligatorio", "Ingrese el código del pedido.", parent=v)
            return
        p = buscar_pedido(codigo)
        if p:
            mostrar_texto(raiz, f"Pedido {p['codigo']}", texto_comprobante(p))
        else:
            messagebox.showinfo("Sin resultados", "Pedido no encontrado.", parent=v)

    ttk.Button(v, text="Buscar", command=buscar).grid(row=2, column=0, sticky="w", pady=15)


# ---------------------------------------------------------------------------
# opción 5: actualizar estado (RF08)
# ---------------------------------------------------------------------------
def actualizar_estado(raiz):
    if not datos["pedidos"]:
        messagebox.showinfo("Sin pedidos", "No existen pedidos registrados.")
        return
    v = nueva_ventana(raiz, "Actualizar estado del pedido", 420, 230)
    etiqueta(v, "Pedido:", 0)
    cb_ped = ttk.Combobox(v, width=36, state="readonly",
                          values=[f"{p['codigo']} - {p['cliente']}" for p in datos["pedidos"]])
    cb_ped.grid(row=0, column=1)
    etiqueta(v, "Estado actual:", 1)
    lbl_actual = tk.Label(v, text="-", bg=COLOR_FONDO, font=("Segoe UI", 10, "bold"))
    lbl_actual.grid(row=1, column=1, sticky="w")
    etiqueta(v, "Nuevo estado:", 2)
    cb_est = ttk.Combobox(v, width=20, state="readonly", values=ESTADOS)
    cb_est.grid(row=2, column=1, sticky="w")

    def al_elegir(_e=None):
        p = datos["pedidos"][cb_ped.current()]
        lbl_actual.config(text=p["estado"])
        cb_est.set(p["estado"])

    cb_ped.bind("<<ComboboxSelected>>", al_elegir)

    def actualizar():
        if cb_ped.current() < 0:
            messagebox.showerror("Pedido", "Seleccione un pedido.", parent=v)
            return
        nuevo = cb_est.get()
        if nuevo not in ESTADOS:
            messagebox.showerror("Estado inválido", "Seleccione un estado válido.", parent=v)
            return
        p = datos["pedidos"][cb_ped.current()]
        p["estado"] = nuevo
        guardar_datos()
        messagebox.showinfo("Éxito", f"El pedido {p['codigo']} ahora está '{nuevo}'.", parent=v)
        v.destroy()

    f = tk.Frame(v, bg=COLOR_FONDO)
    f.grid(row=3, column=0, columnspan=2, pady=20)
    ttk.Button(f, text="Actualizar", command=actualizar).pack(side="left", padx=5)
    ttk.Button(f, text="Cancelar", command=v.destroy).pack(side="left", padx=5)


# ---------------------------------------------------------------------------
# opción 6: generar comprobante (RF09)
# ---------------------------------------------------------------------------
def generar_comprobante(raiz):
    if not datos["pedidos"]:
        messagebox.showinfo("Sin pedidos", "No existen pedidos registrados.")
        return
    v = nueva_ventana(raiz, "Generar comprobante", 420, 160)
    etiqueta(v, "Seleccione el pedido:", 0)
    cb_ped = ttk.Combobox(v, width=40, state="readonly",
                          values=[f"{p['codigo']} - {p['cliente']}" for p in datos["pedidos"]])
    cb_ped.grid(row=1, column=0, sticky="w")

    def generar():
        if cb_ped.current() < 0:
            messagebox.showerror("Pedido", "Seleccione un pedido.", parent=v)
            return
        p = datos["pedidos"][cb_ped.current()]
        mostrar_texto(raiz, f"Comprobante {p['codigo']}", texto_comprobante(p),
                      guardable=True, nombre_archivo=f"comprobante_{p['codigo']}.txt")

    ttk.Button(v, text="Generar", command=generar).grid(row=2, column=0, sticky="w", pady=15)


# ---------------------------------------------------------------------------
# opción 7: ver historial (RF10)
# ---------------------------------------------------------------------------
def ver_historial(raiz):
    if not datos["pedidos"]:
        messagebox.showinfo("Historial", "No existen pedidos registrados.")
        return
    v = nueva_ventana(raiz, "Historial de pedidos", 700, 430)
    cols = ("codigo", "cliente", "entrega", "total", "estado")
    tabla = ttk.Treeview(v, columns=cols, show="headings", height=14)
    for col, ancho, txt in [("codigo", 90, "Código"), ("cliente", 220, "Cliente"), ("entrega", 100, "Entrega"),
                            ("total", 90, "Total"), ("estado", 120, "Estado")]:
        tabla.heading(col, text=txt)
        tabla.column(col, width=ancho, anchor="center")
    for p in reversed(datos["pedidos"]):
        tabla.insert("", "end", iid=p["codigo"],
                     values=(p["codigo"], p["cliente"], p["fecha_entrega"], f"S/ {p['total']:.2f}", p["estado"]))
    tabla.pack(fill="both", expand=True)

    def detalle(_e=None):
        sel = tabla.selection()
        if not sel:
            messagebox.showinfo("Historial", "Seleccione un pedido de la lista.", parent=v)
            return
        mostrar_texto(raiz, f"Pedido {sel[0]}", texto_comprobante(buscar_pedido(sel[0])))

    tabla.bind("<Double-1>", detalle)
    f = tk.Frame(v, bg=COLOR_FONDO)
    f.pack(pady=10)
    ttk.Button(f, text="Ver detalle", command=detalle).pack(side="left", padx=5)
    ttk.Button(f, text="Cerrar", command=v.destroy).pack(side="left", padx=5)


# ---------------------------------------------------------------------------
# opción 8: salir
# ---------------------------------------------------------------------------
def salir(raiz):
    if messagebox.askyesno("Salir", "¿Desea cerrar el sistema?"):
        guardar_datos()
        raiz.destroy()


# ---------------------------------------------------------------------------
# ventana principal / menú
# ---------------------------------------------------------------------------
def main():
    cargar_datos()
    raiz = tk.Tk()
    raiz.title("Bizcotela Cakes - Sistema de gestión de pedidos")
    raiz.configure(bg=COLOR_FONDO)
    raiz.geometry("420x560")
    raiz.resizable(False, False)

    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("Menu.TButton", font=("Segoe UI", 11), padding=8)

    cab = tk.Frame(raiz, bg=COLOR_MARRON)
    cab.pack(fill="x")
    tk.Label(cab, text="Bizcotela Cakes", bg=COLOR_MARRON, fg="white", font=("Segoe Script", 24, "bold")).pack(pady=(15, 0))
    tk.Label(cab, text="Pastelería · Desde 2017", bg=COLOR_MARRON, fg=COLOR_MENTA, font=("Segoe UI", 10)).pack(pady=(0, 15))

    tk.Label(raiz, text="Menú principal", bg=COLOR_FONDO, fg=COLOR_MARRON, font=("Segoe UI", 13, "bold")).pack(pady=12)

    opciones = [
        ("1. Registrar cliente", registrar_cliente),
        ("2. Registrar producto", registrar_producto),
        ("3. Registrar pedido", registrar_pedido),
        ("4. Consultar pedido", consultar_pedido),
        ("5. Actualizar estado del pedido", actualizar_estado),
        ("6. Generar comprobante", generar_comprobante),
        ("7. Ver historial", ver_historial),
    ]
    for texto, funcion in opciones:
        ttk.Button(raiz, text=texto, style="Menu.TButton", width=34,
                   command=lambda f=funcion: f(raiz)).pack(pady=3)
    ttk.Button(raiz, text="8. Salir", style="Menu.TButton", width=34,
               command=lambda: salir(raiz)).pack(pady=(10, 3))

    raiz.protocol("WM_DELETE_WINDOW", lambda: salir(raiz))
    raiz.mainloop()


if __name__ == "__main__":
    main()
