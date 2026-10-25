from django.db import models


class Supplier(models.Model):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="suppliers")
    name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=64, blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["organization", "name"], name="unique_supplier_name_per_organization")]
        indexes = [models.Index(fields=["organization", "is_active", "name"])]

    def __str__(self):
        return self.name


class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE, related_name="supplier_links")
    supplier_sku = models.CharField(max_length=80, blank=True)
    lead_time_days = models.PositiveIntegerField(default=0)
    last_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_preferred = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["supplier", "product"], name="unique_supplier_product_link")]

    def __str__(self):
        return f"{self.supplier} / {self.product}"
