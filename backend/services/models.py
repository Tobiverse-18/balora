from django.core.validators import MinValueValidator
from django.db import models


class Service(models.Model):
    class ServiceType(models.TextChoices):
        AIRTIME = "AIRTIME", "Airtime"
        DATA = "DATA", "Data"
        CABLE = "CABLE", "Cable TV"
        ELECTRICITY = "ELECTRICITY", "Electricity"
        TRANSFER = "TRANSFER", "Transfer"

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices,
        unique=True,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.name


class ServiceProduct(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="products",
    )

    name = models.CharField(
        max_length=150,
    )

    code = models.CharField(
        max_length=100,
    )

    amount = models.BigIntegerField(
        validators=[
            MinValueValidator(1),
        ],
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["service", "code"],
                name="unique_service_product_code",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.service.name} - {self.name}"