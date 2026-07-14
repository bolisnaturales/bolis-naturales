from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Producto, Pedido, PedidoItem


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "categoria", "precio", "stock", "activo")
    list_filter = ("categoria", "activo")
    search_fields = ("nombre", "descripcion")
    list_editable = ("precio", "stock", "activo")
    ordering = ("-id",)


class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0
    readonly_fields = (
        "nombre_producto",
        "precio_unitario",
        "cantidad",
        "subtotal",
    )
    can_delete = False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "boton_imprimir",
        "estado",
        "telefono",
        "total",
        "creado_en",
    )
    list_filter = ("estado", "creado_en")
    search_fields = ("nombre", "telefono", "direccion_envio")
    ordering = ("-creado_en",)

    readonly_fields = (
        "token",
        "creado_en",
        "subtotal",
        "envio",
        "total",
    )

    inlines = [PedidoItemInline]

    def boton_imprimir(self, obj):
        url = reverse("imprimir_pedido", args=[obj.id])

        return format_html(
            '<a class="button" href="{}" target="_blank">🖨 Imprimir</a>',
            url,
        )

    boton_imprimir.short_description = "Imprimir"


@admin.register(PedidoItem)
class PedidoItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "pedido",
        "nombre_producto",
        "cantidad",
        "precio_unitario",
        "subtotal",
    )
    search_fields = ("nombre_producto",)
    list_filter = ("pedido",)