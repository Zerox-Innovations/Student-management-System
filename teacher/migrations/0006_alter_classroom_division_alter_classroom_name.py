# Generated by Django 5.0.4 on 2024-07-20 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("teacher", "0005_classroom_division_alter_classroom_unique_together_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="classroom",
            name="division",
            field=models.CharField(max_length=1, unique=True),
        ),
        migrations.AlterField(
            model_name="classroom",
            name="name",
            field=models.CharField(max_length=150),
        ),
    ]
