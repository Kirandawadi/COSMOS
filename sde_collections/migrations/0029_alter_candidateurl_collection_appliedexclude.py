# Generated by Django 4.2 on 2023-04-27 13:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("sde_collections", "0028_candidateurl_level"),
    ]

    operations = [
        migrations.AlterField(
            model_name="candidateurl",
            name="collection",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="candidate_urls",
                to="sde_collections.collection",
            ),
        ),
        migrations.CreateModel(
            name="AppliedExclude",
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
                (
                    "candidate_url",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sde_collections.candidateurl",
                    ),
                ),
                (
                    "exclude_pattern",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sde_collections.excludepattern",
                    ),
                ),
            ],
            options={
                "verbose_name": "Applied Exclude",
                "verbose_name_plural": "Applied Excludes",
            },
        ),
    ]
