# Generated by Django 4.0.10 on 2023-03-28 02:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sde_collections', '0002_division_collection_config_folder_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateURL',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('excluded', models.BooleanField(default=False)),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sde_collections.collection')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='children', to='sde_collections.candidateurl')),
            ],
        ),
    ]
