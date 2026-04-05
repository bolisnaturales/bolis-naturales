from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import CharField, TextField

from .models import Producto, Pedido, PedidoItem


# =========================
# Helpers (carrito en sesión)
# =========================
def _get_cart(session):
    cart = session.get("cart")
    if cart is None:
        cart = {}
        session["cart"] = cart
    return cart


def _cart_count(cart) -> int:
    total = 0
    for _, data in cart.items():
        try:
            total += int(data.get("qty", 0))
        except (TypeError, ValueError):
            pass
    return total


def _cart_items_and_total(cart):
    ids = []
    for pid in cart.keys():
        try:
            ids.append(int(pid))
        except ValueError:
            pass

    productos = Producto.objects.filter(id__in=ids, activo=True)

    items = []
    subtotal = Decimal("0.00")

    for p in productos:
        pid = str(p.id)
        qty = int(cart.get(pid, {}).get("qty", 0))
        if qty <= 0:
            continue

        item_subtotal = p.precio * qty
        subtotal += item_subtotal

        items.append({
            "producto": p,
            "qty": qty,
            "subtotal": item_subtotal,
        })

    items.sort(key=lambda x: x["producto"].nombre.lower())

    return items, subtotal


def _calcular_envio_por_subtotal(items, subtotal: Decimal) -> Decimal:
    if not items:
        return Decimal("0.00")

    return Decimal("3.00") if subtotal >= Decimal("20.00") else Decimal("6.00")


def _mensaje_envio_por_subtotal(items, subtotal: Decimal) -> str:
    if not items:
        return ""

    meta = Decimal("20.00")

    if subtotal < meta:
        falta = (meta - subtotal).quantize(Decimal("0.01"))
        return f"💡 Agrega ${falta} más y tu envío baja a solo $3"

    return "🎉 ¡Ya tienes envío por solo $3!"


# =========================
# Catálogo
# =========================
def _filter_by_categoria(nombre_categoria: str):
    field = Producto._meta.get_field("categoria")

    if isinstance(field, (CharField, TextField)):
        return Producto.objects.filter(
            categoria__iexact=nombre_categoria,
            activo=True
        ).order_by("id")

    return Producto.objects.filter(
        categoria__nombre__iexact=nombre_categoria,
        activo=True
    ).order_by("id")


def catalogo(request):
    cart = _get_cart(request.session)
    cart_count = _cart_count(cart)

    agua = _filter_by_categoria("Agua")
    leche = _filter_by_categoria("Leche")

    return render(request, "productos/catalogo.html", {
        "agua": agua,
        "leche": leche,
        "cart_count": cart_count,
    })


# =========================
# Carrito
# =========================
def add_to_cart(request, producto_id):
    if request.method != "POST":
        return redirect("catalogo")

    producto = get_object_or_404(Producto, id=producto_id, activo=True)

    cart = _get_cart(request.session)
    pid = str(producto.id)

    qty_actual = int(cart.get(pid, {}).get("qty", 0))

    # No permitir agregar más de lo disponible
    if qty_actual >= producto.stock:
        request.session["cart_msg"] = (
            f"Solo hay {producto.stock} unidades disponibles de {producto.nombre}."
        )
        return redirect("cart_detail")

    if pid not in cart:
        cart[pid] = {"qty": 1}
    else:
        cart[pid]["qty"] = qty_actual + 1

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart_detail")


def cart_detail(request):
    cart = _get_cart(request.session)
    items, subtotal = _cart_items_and_total(cart)

    envio = _calcular_envio_por_subtotal(items, subtotal)
    total_con_envio = subtotal + envio

    mensaje_envio = _mensaje_envio_por_subtotal(items, subtotal)

    mensaje_envio_tipo = ""
    if items and subtotal < Decimal("20.00"):
        mensaje_envio_tipo = "falta"
    elif items:
        mensaje_envio_tipo = "ok"

    meta = Decimal("20.00")
    progreso_pct = 0
    falta = Decimal("0.00")

    if items:
        if subtotal < meta:
            falta = (meta - subtotal).quantize(Decimal("0.01"))
            progreso_pct = int((subtotal / meta) * 100)
        else:
            progreso_pct = 100

    # ✅ mensaje temporal del carrito
    cart_msg = request.session.pop("cart_msg", "")

    return render(request, "productos/carrito.html", {
        "items": items,
        "total": subtotal,
        "envio": envio,
        "total_con_envio": total_con_envio,
        "mensaje_envio": mensaje_envio,
        "mensaje_envio_tipo": mensaje_envio_tipo,
        "progreso_pct": progreso_pct,
        "falta": falta,
        "cart_msg": cart_msg,
    })


def cart_update(request, producto_id):
    if request.method != "POST":
        return redirect("cart_detail")

    cart = _get_cart(request.session)
    pid = str(producto_id)

    producto = get_object_or_404(Producto, id=producto_id, activo=True)

    try:
        qty = int(request.POST.get("qty", "1"))
    except ValueError:
        qty = 1

    if qty <= 0:
        cart.pop(pid, None)
    else:
        # ✅ No permitir más de lo disponible
        if qty > producto.stock:
            qty = producto.stock
            request.session["cart_msg"] = (
                f"Solo hay {producto.stock} unidades disponibles de {producto.nombre}. "
                f"Ajustamos tu carrito."
            )

        if pid in cart:
            cart[pid]["qty"] = qty
        else:
            cart[pid] = {"qty": qty}

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart_detail")


def cart_remove(request, producto_id):
    if request.method != "POST":
        return redirect("cart_detail")

    cart = _get_cart(request.session)
    pid = str(producto_id)

    cart.pop(pid, None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart_detail")


# =========================
# Checkout
# =========================
def checkout(request):
    cart = _get_cart(request.session)
    items, subtotal = _cart_items_and_total(cart)

    if not items:
        return redirect("catalogo")

    envio = _calcular_envio_por_subtotal(items, subtotal)
    total = subtotal + envio

    horarios = {
    "lv": "Lunes a viernes: 4:00 pm a 6:30 pm",
    "sd": "Sábado y domingo: 2:00 am a 4:00 pm",
}

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        telefono_raw = request.POST.get("telefono", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        mensaje = request.POST.get("mensaje", "").strip()

        # Campos obligatorios
        if not nombre or not telefono_raw or not direccion:
            return render(request, "productos/checkout.html", {
                "items": items,
                "subtotal": subtotal,
                "envio": envio,
                "total": total,
                "horarios": horarios,
                "error": "Por favor llena nombre, teléfono y dirección.",
            })

        telefono = "".join(ch for ch in telefono_raw if ch.isdigit())

        if len(telefono) != 10:
            return render(request, "productos/checkout.html", {
                "items": items,
                "subtotal": subtotal,
                "envio": envio,
                "total": total,
                "horarios": horarios,
                "error": "El teléfono debe tener exactamente 10 dígitos.",
            })

        # ✅ Validar stock antes de confirmar
        for it in items:
            p = it["producto"]
            qty = it["qty"]

            if p.stock < qty:
                return render(request, "productos/checkout.html", {
                    "items": items,
                    "subtotal": subtotal,
                    "envio": envio,
                    "total": total,
                    "horarios": horarios,
                    "error": f"No hay suficiente stock de {p.nombre}. Disponible: {p.stock}.",
                })

        # 1️⃣ Crear pedido
        pedido = Pedido.objects.create(
            nombre=nombre,
            telefono=telefono,
            direccion_envio=direccion,
            mensaje=mensaje,
            subtotal=subtotal,
            envio=envio,
            total=total,
            estado="CONFIRMADO",
        )

        # 2️⃣ Crear items y descontar stock
        for it in items:
            p = it["producto"]
            qty = it["qty"]
            sub = it["subtotal"]

            PedidoItem.objects.create(
                pedido=pedido,
                producto=p,
                nombre_producto=p.nombre,
                precio_unitario=p.precio,
                cantidad=qty,
                subtotal=sub,
            )

            p.stock -= qty
            p.save()

        # 3️⃣ Limpiar carrito
        request.session.pop("cart", None)
        request.session.modified = True

        # 4️⃣ Confirmación
        return render(request, "productos/confirmacion.html", {
            "pedido": pedido,
            "horarios": horarios,
        })

    return render(request, "productos/checkout.html", {
        "items": items,
        "subtotal": subtotal,
        "envio": envio,
        "total": total,
        "horarios": horarios,
        "error": "",
    })


# =========================
# Estado del pedido
# =========================
def pedido_detalle(request, pedido_id):
    token = request.GET.get("t", "").strip()

    pedido = get_object_or_404(Pedido, id=pedido_id, token=token)
    items = PedidoItem.objects.filter(pedido=pedido).order_by("id")

    return render(request, "productos/estado_pedido.html", {
        "pedido": pedido,
        "items": items,
    })