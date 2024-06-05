# Generated by Django 4.2.9 on 2024-05-03 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sde_collections", "0044_alter_collection_document_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="collection",
            name="workflow_status",
            field=models.IntegerField(
                choices=[
                    (1, "Research in Progress"),
                    (2, "Ready for Engineering"),
                    (3, "Engineering in Progress"),
                    (4, "Ready for Curation"),
                    (5, "Curation in Progress"),
                    (6, "Curated"),
                    (7, "Quality Fixed"),
                    (8, "Secret Deployment Started"),
                    (9, "Secret Deployment Failed"),
                    (10, "Ready for LRM Quality Check"),
                    (11, "Ready for Quality Check"),
                    (12, "Quality Check Failed"),
                    (13, "Ready for Public Production"),
                    (14, "Perfect and on Production"),
                    (15, "Low Priority Problems on Production"),
                    (16, "High Priority Problems on Production, only for old sources"),
                    (17, "Code Merge Pending"),
                ],
                default=1,
            ),
        ),
    ]
