from django.contrib import admin
from .models import Producto, Pedido, PedidoItem


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "categoria", "precio", "activo", "creado_en")
    list_filter = ("categoria", "activo")
    search_fields = ("nombre", "descripcion")
    list_editable = ("precio", "activo")
    ordering = ("-creado_en",)


class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0
    readonly_fields = ("nombre_producto", "precio_unitario", "cantidad", "subtotal")
    can_delete = False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "telefono", "estado", "total", "creado_en")
    list_filter = ("estado", "creado_en")
    search_fields = ("nombre", "telefono", "direccion_envio")
    ordering = ("-creado_en",)

    # ✅ seguridad: no lo mostramos en la tabla, pero sí lo puedes ver al abrir el pedido
    readonly_fields = ("token", "creado_en", "subtotal", "envio", "total")

    inlines = [PedidoItemInline]


@admin.register(PedidoItem)
class PedidoItemAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "nombre_producto", "cantidad", "precio_unitario", "subtotal")
    search_fields = ("nombre_producto",)
    list_filter = ("pedido",)