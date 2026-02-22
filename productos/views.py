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

    # orden opcional por nombre (solo para que se vea bonito)
    items.sort(key=lambda x: x["producto"].nombre.lower())

    return items, subtotal


# =========================
# Catálogo
# =========================
def _filter_by_categoria(nombre_categoria: str):
    """
    Filtra productos por categoría SIN romperse,
    funcione si Producto.categoria es:
    - ForeignKey (categoria__nombre)
    - CharField/TextField (categoria)
    """
    field = Producto._meta.get_field("categoria")

    # Si es texto (CharField/TextField), filtra por el campo directo
    if isinstance(field, (CharField, TextField)):
        return Producto.objects.filter(categoria__iexact=nombre_categoria, activo=True).order_by("id")

    # Si NO es texto, asumimos relación (ForeignKey) con atributo "nombre"
    return Producto.objects.filter(categoria__nombre__iexact=nombre_categoria, activo=True).order_by("id")


def catalogo(request):
    agua = _filter_by_categoria("Agua")
    leche = _filter_by_categoria("Leche")

    return render(request, "productos/catalogo.html", {
        "agua": agua,
        "leche": leche,
    })


# =========================
# Carrito (agregar / ver / actualizar / quitar)
# =========================
def add_to_cart(request, producto_id):
    """
    POST -> agrega 1 unidad al carrito y redirige al carrito.
    """
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

    envio = Decimal("6.00") if items else Decimal("0.00")
    total_con_envio = subtotal + envio

    return render(request, "productos/carrito.html", {
        "items": items,
        "total": subtotal,  # tu template carrito.html usa "total" como subtotal
        "envio": envio,
        "total_con_envio": total_con_envio,
    })


def cart_update(request, producto_id):
    """
    POST -> actualiza cantidad.
    """
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
    """
    POST -> quita producto del carrito.
    """
    if request.method != "POST":
        return redirect("cart_detail")

    cart = _get_cart(request.session)
    pid = str(producto_id)

    cart.pop(pid, None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart_detail")


# =========================
# Checkout (guardar pedido real)
# =========================
def checkout(request):
    cart = _get_cart(request.session)
    items, subtotal = _cart_items_and_total(cart)

    if not items:
        return redirect("catalogo")

    envio = Decimal("6.00")
    total = subtotal + envio

    horarios = {
        "lv": "Lunes a viernes: 4:00 pm a 7:30 pm",
        "sd": "Sábado y domingo: 11:00 am a 3:00 pm",
    }

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        mensaje = request.POST.get("mensaje", "").strip()

        # Validación mínima MVP
        if not (nombre and telefono and direccion):
            return render(request, "productos/checkout.html", {
                "items": items,
                "subtotal": subtotal,
                "envio": envio,
                "total": total,
                "horarios": horarios,
                "error": "Por favor llena nombre, teléfono y dirección.",
            })

        # 1) Crear Pedido (token se genera solo en models.py con save())
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

        # 2) Crear PedidoItems (snapshot)
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

        # 3) Limpiar carrito
        request.session.pop("cart", None)
        request.session.modified = True

        # 4) Confirmación
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
# Estado del pedido (privado con token)
# =========================
def pedido_detalle(request, pedido_id):
    token = request.GET.get("t", "").strip()
    pedido = get_object_or_404(Pedido, id=pedido_id, token=token)
    items = PedidoItem.objects.filter(pedido=pedido).order_by("id")

    return render(request, "productos/estado_pedido.html", {
        "pedido": pedido,
        "items": items,
    })