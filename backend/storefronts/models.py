from django.db import models


class Storefront(models.Model):
    agent = models.OneToOneField(
        "agents.Agent",
        on_delete=models.PROTECT,
        related_name="storefront",
    )

    name = models.CharField(
        max_length=150,
    )

    slug = models.SlugField(
        max_length=150,
        unique=True,
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
        return f"{self.name} - {self.slug}"