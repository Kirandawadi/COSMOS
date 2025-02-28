# Generated by Django 4.2.9 on 2024-08-26 02:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sde_collections", "0057_alter_collection_workflow_status_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidateurl",
            name="division",
            field=models.IntegerField(
                choices=[
                    (1, "Astrophysics"),
                    (2, "Biological and Physical Sciences"),
                    (3, "Earth Science"),
                    (4, "Heliophysics"),
                    (5, "Planetary Science"),
                    (6, "General"),
                ],
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="collection",
            name="is_multi_division",
            field=models.BooleanField(default=False, verbose_name="Is Multi-Division?"),
        ),
        migrations.CreateModel(
            name="DivisionPattern",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "match_pattern",
                    models.CharField(
                        help_text="This pattern is compared against the URL of all the documents in the collection and matching documents will be returned",
                        verbose_name="Pattern",
                    ),
                ),
                (
                    "match_pattern_type",
                    models.IntegerField(choices=[(1, "Individual URL Pattern"), (2, "Multi-URL Pattern")], default=1),
                ),
                (
                    "division",
                    models.IntegerField(
                        choices=[
                            (1, "Astrophysics"),
                            (2, "Biological and Physical Sciences"),
                            (3, "Earth Science"),
                            (4, "Heliophysics"),
                            (5, "Planetary Science"),
                            (6, "General"),
                        ]
                    ),
                ),
                (
                    "candidate_urls",
                    models.ManyToManyField(related_name="%(class)s_urls", to="sde_collections.candidateurl"),
                ),
                (
                    "collection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)s",
                        related_query_name="%(class)ss",
                        to="sde_collections.collection",
                    ),
                ),
            ],
            options={
                "verbose_name": "Division Pattern",
                "verbose_name_plural": "Division Patterns",
                "unique_together": {("collection", "match_pattern")},
            },
        ),
    ]
