# Generated by Django 4.2.9 on 2024-11-11 17:17

from django.db import migrations, models
import django.db.models.deletion
import sde_collections.models.delta_patterns


class Migration(migrations.Migration):

    dependencies = [
        ("sde_collections", "0061_dumpurl_deltaurl_curatedurl"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeltaTitlePattern",
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
                    "title_pattern",
                    models.CharField(
                        help_text="This is the pattern for the new title. You can either write an exact replacement string (no quotes required) or you can write sinequa-valid code",
                        validators=[sde_collections.models.delta_patterns.validate_title_pattern],
                        verbose_name="Title Pattern",
                    ),
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
                (
                    "curated_urls",
                    models.ManyToManyField(related_name="%(class)s_curated_urls", to="sde_collections.curatedurl"),
                ),
                (
                    "delta_urls",
                    models.ManyToManyField(related_name="%(class)s_delta_urls", to="sde_collections.deltaurl"),
                ),
            ],
            options={
                "verbose_name": "Title Pattern",
                "verbose_name_plural": "Title Patterns",
                "unique_together": {("collection", "match_pattern")},
            },
        ),
        migrations.CreateModel(
            name="DeltaResolvedTitleError",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("error_string", models.TextField()),
                ("http_status_code", models.IntegerField(blank=True, null=True)),
                (
                    "delta_url",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="sde_collections.deltaurl"),
                ),
                (
                    "title_pattern",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sde_collections.deltatitlepattern"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="DeltaResolvedTitle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_title", models.CharField(blank=True, default="")),
                (
                    "delta_url",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="sde_collections.deltaurl"),
                ),
                (
                    "title_pattern",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sde_collections.deltatitlepattern"
                    ),
                ),
            ],
            options={
                "verbose_name": "Resolved Title",
                "verbose_name_plural": "Resolved Titles",
            },
        ),
        migrations.CreateModel(
            name="DeltaIncludePattern",
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
                    "collection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)s",
                        related_query_name="%(class)ss",
                        to="sde_collections.collection",
                    ),
                ),
                (
                    "curated_urls",
                    models.ManyToManyField(related_name="%(class)s_curated_urls", to="sde_collections.curatedurl"),
                ),
                (
                    "delta_urls",
                    models.ManyToManyField(related_name="%(class)s_delta_urls", to="sde_collections.deltaurl"),
                ),
            ],
            options={
                "verbose_name": "Include Pattern",
                "verbose_name_plural": "Include Patterns",
                "unique_together": {("collection", "match_pattern")},
            },
        ),
        migrations.CreateModel(
            name="DeltaExcludePattern",
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
                ("reason", models.TextField(blank=True, default="", verbose_name="Reason for excluding")),
                (
                    "collection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)s",
                        related_query_name="%(class)ss",
                        to="sde_collections.collection",
                    ),
                ),
                (
                    "curated_urls",
                    models.ManyToManyField(related_name="%(class)s_curated_urls", to="sde_collections.curatedurl"),
                ),
                (
                    "delta_urls",
                    models.ManyToManyField(related_name="%(class)s_delta_urls", to="sde_collections.deltaurl"),
                ),
            ],
            options={
                "verbose_name": "Exclude Pattern",
                "verbose_name_plural": "Exclude Patterns",
                "unique_together": {("collection", "match_pattern")},
            },
        ),
        migrations.CreateModel(
            name="DeltaDocumentTypePattern",
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
                    "document_type",
                    models.IntegerField(
                        choices=[
                            (1, "Images"),
                            (2, "Data"),
                            (3, "Documentation"),
                            (4, "Software and Tools"),
                            (5, "Missions and Instruments"),
                        ]
                    ),
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
                (
                    "curated_urls",
                    models.ManyToManyField(related_name="%(class)s_curated_urls", to="sde_collections.curatedurl"),
                ),
                (
                    "delta_urls",
                    models.ManyToManyField(related_name="%(class)s_delta_urls", to="sde_collections.deltaurl"),
                ),
            ],
            options={
                "verbose_name": "Document Type Pattern",
                "verbose_name_plural": "Document Type Patterns",
                "unique_together": {("collection", "match_pattern")},
            },
        ),
        migrations.CreateModel(
            name="DeltaDivisionPattern",
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
                    "collection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(class)s",
                        related_query_name="%(class)ss",
                        to="sde_collections.collection",
                    ),
                ),
                (
                    "curated_urls",
                    models.ManyToManyField(related_name="%(class)s_curated_urls", to="sde_collections.curatedurl"),
                ),
                (
                    "delta_urls",
                    models.ManyToManyField(related_name="%(class)s_delta_urls", to="sde_collections.deltaurl"),
                ),
            ],
            options={
                "verbose_name": "Division Pattern",
                "verbose_name_plural": "Division Patterns",
                "unique_together": {("collection", "match_pattern")},
            },
        ),
    ]
