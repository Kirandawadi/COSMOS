# Generated by Django 4.2.9 on 2024-11-16 00:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sde_collections", "0064_alter_curatedurl_options_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="deltaurl",
            old_name="delete",
            new_name="to_delete",
        ),
        migrations.AlterField(
            model_name="curatedurl",
            name="collection",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="curated_urls",
                to="sde_collections.collection",
            ),
        ),
        migrations.AlterField(
            model_name="deltaurl",
            name="collection",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="delta_urls", to="sde_collections.collection"
            ),
        ),
        migrations.AlterField(
            model_name="dumpurl",
            name="collection",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="dump_urls", to="sde_collections.collection"
            ),
        ),
    ]
