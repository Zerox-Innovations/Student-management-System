# Generated by Django 5.0.4 on 2024-06-06 17:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("student", "0002_buspayment"),
    ]

    operations = [
        migrations.AddField(
            model_name="buspayment",
            name="payment_type",
            field=models.CharField(
                blank=True, choices=[("UPI", "UPI"), ("CASH", "CASH")], null=True
            ),
        ),
    ]
