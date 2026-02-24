from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import CharField, TextField

from .models import Producto, Pedido, PedidoItem


# =========================
# Helpers (carrito en sesión)
# =========================
def _get_cart(session):
    """
    Estructura del carrito en sesión:
    session["cart"] = {
      "1": {"qty": 2},
      "8": {"qty": 1},
    }
    """
    cart = session.get("cart")
    if cart is None:
        cart = {}
        session["cart"] = cart
    return cart


def _cart_items_and_total(cart):
    """
    Devuelve:
    - items: [{producto, qty, subtotal}, ...]
    - subtotal: Decimal
    """
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


# =========================
# Helper: cálculo de envío
# =========================
def calcular_envio(subtotal: Decimal, tiene_items: bool) -> Decimal:
    """
    Regla:
    - Sin items → envío 0
    - Subtotal >= 20 → envío 3
    - Subtotal < 20 → envío 6
    """
    if not tiene_items:
        return Decimal("0.00")

    if subtotal >= Decimal("20.00"):
        return Decimal("3.00")

    return Decimal("6.00")


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
    agua = _filter_by_categoria("Agua")
    leche = _filter_by_categoria("Leche")

    return render(request, "productos/catalogo.html", {
        "agua": agua,
        "leche": leche,
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

    if pid not in cart:
        cart[pid] = {"qty": 1}
    else:
        cart[pid]["qty"] = int(cart[pid].get("qty", 0)) + 1

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart_detail")


def cart_detail(request):
    cart = _get_cart(request.session)
    items, subtotal = _cart_items_and_total(cart)

    envio = calcular_envio(subtotal, bool(items))
    total_con_envio = subtotal + envio

    mensaje_envio = ""
    if subtotal < Decimal("20.00"):
        faltante = (Decimal("20.00") - subtotal).quantize(Decimal("0.01"))
        mensaje_envio = f"Te faltan ${faltante} para pagar solo $3 de envío"

    return render(request, "productos/carrito.html", {
        "items": items,
        "total": subtotal,
        "envio": envio,
        "total_con_envio": total_con_envio,
        "mensaje_envio": mensaje_envio,
    })


def cart_update(request, producto_id):
    if request.method != "POST":
        return redirect("cart_detail")

    cart = _get_cart(request.session)
    pid = str(producto_id)

    try:
        qty = int(request.POST.get("qty", "1"))
    except ValueError:
        qty = 1

    if qty <= 0:
        cart.pop(pid, None)
    else:
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

    envio = calcular_envio(subtotal, bool(items))
    total = subtotal + envio

    mensaje_envio = ""
    if subtotal < Decimal("20.00"):
        faltante = (Decimal("20.00") - subtotal).quantize(Decimal("0.01"))
        mensaje_envio = f"Te faltan ${faltante} para pagar solo $3 de envío"

    horarios = {
        "lv": "Lunes a viernes: 4:00 pm a 7:30 pm",
        "sd": "Sábado y domingo: 11:00 am a 3:00 pm",
    }

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        mensaje = request.POST.get("mensaje", "").strip()

        if not (nombre and telefono and direccion):
            return render(request, "productos/checkout.html", {
                "items": items,
                "subtotal": subtotal,
                "envio": envio,
                "total": total,
                "horarios": horarios,
                "mensaje_envio": mensaje_envio,
                "error": "Por favor llena nombre, teléfono y dirección.",
            })

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

        for it in items:
            p = it["producto"]
            PedidoItem.objects.create(
                pedido=pedido,
                producto=p,
                nombre_producto=p.nombre,
                precio_unitario=p.precio,
                cantidad=it["qty"],
                subtotal=it["subtotal"],
            )

        request.session.pop("cart", None)
        request.session.modified = True

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
        "mensaje_envio": mensaje_envio,
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