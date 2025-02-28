# Generated by Django 4.2.9 on 2024-11-07 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sde_collections", "0059_candidateurl_scraped_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="candidateurl",
            name="scraped_text",
            field=models.TextField(
                blank=True,
                default="",
                help_text="This is the text scraped by Sinequa",
                null=True,
                verbose_name="Scraped Text",
            ),
        ),
    ]
