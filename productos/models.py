from django.db import models
from decimal import Decimal
import secrets


class Producto(models.Model):
    CATEGORIA_CHOICES = [
        ("AGUA", "Agua"),
        ("LECHE", "Leche"),
    ]

    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    categoria = models.CharField(max_length=10, choices=CATEGORIA_CHOICES, default="AGUA")
    activo = models.BooleanField(default=True)

    # (opcional) si tienes imágenes, puedes descomentar esto:
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)

    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    ESTADO_CHOICES = [
        ("CONFIRMADO", "Confirmado"),
        ("EN_PREPARACION", "En preparación"),
        ("EN_CAMINO", "En camino"),
        ("ENTREGADO", "Entregado"),
        ("CANCELADO", "Cancelado"),
    ]

    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=40)
    direccion_envio = models.CharField(max_length=255)
    mensaje = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    envio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("6.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="CONFIRMADO")
    creado_en = models.DateTimeField(auto_now_add=True)

    # 🔐 Token secreto (versión final)
    token = models.CharField(max_length=32, unique=True, db_index=True, blank=True)

    def save(self, *args, **kwargs):
        # genera token automáticamente si no existe
        if not self.token:
            self.token = secrets.token_hex(16)  # 32 caracteres
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido #{self.id} - {self.nombre} - {self.total}"


class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)

    nombre_producto = models.CharField(max_length=120)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    def save(self, *args, **kwargs):
        # asegura campos calculados
        if not self.nombre_producto and self.producto_id:
            self.nombre_producto = self.producto.nombre
        if (self.precio_unitario in [None, Decimal("0.00")]) and self.producto_id:
            self.precio_unitario = self.producto.precio
        self.subtotal = (self.precio_unitario or Decimal("0.00")) * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto} (Pedido #{self.pedido_id})"