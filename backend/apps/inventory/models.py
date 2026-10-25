from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Category(models.Model):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["organization", "slug"], name="unique_category_slug_per_organization")]
        indexes = [models.Index(fields=["organization", "name"])]

    def __str__(self):
        return self.name


class Product(models.Model):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    name = models.CharField(max_length=180)
    sku = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    unit_of_measure = models.CharField(max_length=32, default="unit")
    image_path = models.CharField(max_length=512, blank=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    reorder_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    target_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["organization", "sku"], name="unique_product_sku_per_organization"),
            models.CheckConstraint(condition=Q(cost_price__gte=0), name="product_cost_non_negative"),
            models.CheckConstraint(condition=Q(reorder_threshold__gte=0), name="product_reorder_non_negative"),
            models.CheckConstraint(condition=Q(target_stock_level__gte=0), name="product_target_non_negative"),
        ]
        indexes = [models.Index(fields=["organization", "is_active", "name"]), models.Index(fields=["organization", "sku"])]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class InventoryBalance(models.Model):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="inventory_balances")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="balances")
    hub = models.ForeignKey("hubs.Hub", on_delete=models.CASCADE, related_name="inventory_balances")
    on_hand = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    reserved = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "product", "hub"], name="unique_product_hub_balance"),
            models.CheckConstraint(condition=Q(on_hand__gte=0), name="balance_on_hand_non_negative"),
            models.CheckConstraint(condition=Q(reserved__gte=0), name="balance_reserved_non_negative"),
            models.CheckConstraint(condition=Q(reserved__lte=models.F("on_hand")), name="balance_reserved_not_above_on_hand"),
        ]
        indexes = [models.Index(fields=["organization", "hub", "product"]), models.Index(fields=["organization", "product"])]

    @property
    def available(self):
        return self.on_hand - self.reserved

    def __str__(self):
        return f"{self.product} @ {self.hub}: {self.on_hand}"
