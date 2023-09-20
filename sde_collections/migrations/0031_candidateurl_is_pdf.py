# Generated by Django 4.2.3 on 2023-09-19 14:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sde_collections", "0030_candidateurl_inference_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidateurl",
            name="is_pdf",
            field=models.BooleanField(
                default=False,
                help_text="This keeps track of whether the given url is pdf or not",
                verbose_name="Is PDF",
            ),
        ),
    ]
