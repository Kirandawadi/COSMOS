# Generated by Django 5.0.1 on 2024-02-02 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EnvironmentalJusticeRow",
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
                ("dataset", models.CharField(verbose_name="Dataset")),
                ("description", models.CharField(verbose_name="Description")),
                (
                    "description_simplified",
                    models.CharField(verbose_name="Description Simplified"),
                ),
                ("indicators", models.CharField(verbose_name="Indicators")),
                ("intended_use", models.CharField(verbose_name="Intended Use")),
                ("latency", models.CharField(verbose_name="Latency")),
                ("limitations", models.CharField(verbose_name="Limitations")),
                ("project", models.CharField(verbose_name="Project")),
                ("source_link", models.CharField(verbose_name="Source Link")),
                ("strengths", models.CharField(verbose_name="Strengths")),
                ("format", models.CharField(verbose_name="Format")),
                (
                    "geographic_coverage",
                    models.CharField(verbose_name="Geographic Coverage"),
                ),
                (
                    "data_visualization",
                    models.CharField(verbose_name="Data Visualization"),
                ),
                (
                    "spatial_resolution",
                    models.CharField(verbose_name="Spatial Resolution"),
                ),
                ("temporal_extent", models.CharField(verbose_name="Temporal Extent")),
                (
                    "temporal_resolution",
                    models.CharField(verbose_name="Temporal Resolution"),
                ),
            ],
            options={
                "verbose_name": "Environmental Justice Row",
                "verbose_name_plural": "Environmental Justice Rows",
            },
        ),
    ]
