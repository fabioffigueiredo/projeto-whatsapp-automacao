# Generated manually to add Transfer models
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_client_created_at_client_is_registered_and_more"),
    ]

    operations = [
        # First, update existing Client records to have proper created_at values
        migrations.RunSQL(
            "UPDATE core_client SET created_at = '{}' WHERE created_at IS NULL;".format(
                timezone.now().isoformat()
            ),
            reverse_sql="",
        ),
        
        # Then alter the field to be non-nullable
        migrations.AlterField(
            model_name="client",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        
        # Create Transfer model
        migrations.CreateModel(
            name="Transfer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("transfer_id", models.CharField(editable=False, max_length=20, unique=True)),
                ("beneficiary_name", models.CharField(max_length=120)),
                ("beneficiary_cpf", models.CharField(max_length=14)),
                ("pix_key", models.CharField(max_length=120)),
                ("beneficiary_address", models.TextField(blank=True)),
                ("amount_usd", models.DecimalField(decimal_places=2, max_digits=12)),
                ("exchange_rate", models.DecimalField(decimal_places=6, max_digits=12)),
                ("service_fee", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_amount_usd", models.DecimalField(decimal_places=2, max_digits=12)),
                ("amount_brl_estimated", models.DecimalField(decimal_places=2, max_digits=12)),
                ("amount_brl_final", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Rascunho"),
                            ("pending_payment", "Aguardando Pagamento"),
                            ("payment_confirmed", "Pagamento Confirmado"),
                            ("processing", "Processando"),
                            ("completed", "Concluída"),
                            ("failed", "Falhou"),
                            ("cancelled", "Cancelada"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("payment_method", models.CharField(blank=True, max_length=50)),
                ("payment_reference", models.CharField(blank=True, max_length=120)),
                ("payment_link", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("payment_confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("external_reference", models.CharField(blank=True, max_length=120)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transfers",
                        to="core.client",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        
        # Create TransferStatusHistory model
        migrations.CreateModel(
            name="TransferStatusHistory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("previous_status", models.CharField(blank=True, max_length=20)),
                ("new_status", models.CharField(max_length=20)),
                ("changed_by", models.CharField(default="system", max_length=50)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "transfer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="core.transfer",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        
        # Create ExchangeRateSnapshot model
        migrations.CreateModel(
            name="ExchangeRateSnapshot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("usd_to_brl_rate", models.DecimalField(decimal_places=6, max_digits=12)),
                ("rate_source", models.CharField(max_length=50)),
                ("rate_timestamp", models.DateTimeField()),
                ("spread_percentage", models.DecimalField(decimal_places=4, default=0, max_digits=5)),
                ("final_rate", models.DecimalField(decimal_places=6, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "transfer",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rate_snapshot",
                        to="core.transfer",
                    ),
                ),
            ],
        ),
        
        # Add indexes for Transfer model
        migrations.AddIndex(
            model_name="transfer",
            index=models.Index(fields=["client", "status"], name="core_transfer_client_status_idx"),
        ),
        migrations.AddIndex(
            model_name="transfer",
            index=models.Index(fields=["transfer_id"], name="core_transfer_transfer_id_idx"),
        ),
        migrations.AddIndex(
            model_name="transfer",
            index=models.Index(fields=["created_at"], name="core_transfer_created_at_idx"),
        ),
    ]