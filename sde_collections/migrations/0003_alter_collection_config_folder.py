# Generated by Django 4.2 on 2023-05-10 03:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sde_collections", "0002_remove_collection_machine_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="collection",
            name="config_folder",
            field=models.CharField(
                max_length=2048, unique=True, verbose_name="Config Folder"
            ),
        ),
    ]
