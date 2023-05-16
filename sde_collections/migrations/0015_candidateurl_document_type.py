# Generated by Django 4.2 on 2023-05-16 03:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sde_collections", "0014_alter_documenttypepattern_unique_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidateurl",
            name="document_type",
            field=models.IntegerField(
                choices=[
                    (1, "Images"),
                    (2, "Data"),
                    (3, "Documentation"),
                    (4, "Software and Tools"),
                    (5, "Missions and Instruments"),
                ],
                null=True,
            ),
        ),
    ]
