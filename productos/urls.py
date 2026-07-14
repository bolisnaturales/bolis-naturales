from django.urls import path
from .views import (
    catalogo,
    add_to_cart,
    cart_detail,
    cart_remove,
    cart_update,
    checkout,
    pedido_detalle,
    imprimir_pedido,
)

urlpatterns = [
    path("", catalogo, name="catalogo"),

    path("carrito/", cart_detail, name="cart_detail"),
    path("carrito/agregar/<int:producto_id>/", add_to_cart, name="add_to_cart"),
    path("carrito/quitar/<int:producto_id>/", cart_remove, name="cart_remove"),
    path("carrito/actualizar/<int:producto_id>/", cart_update, name="cart_update"),

    path("checkout/", checkout, name="checkout"),

    path("pedido/<int:pedido_id>/", pedido_detalle, name="pedido_detalle"),

    # 👇 Agrega esta ruta
    path(
        "pedido/<int:pedido_id>/imprimir/",
        imprimir_pedido,
        name="imprimir_pedido",
    ),
]