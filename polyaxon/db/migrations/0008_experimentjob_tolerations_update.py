# Generated by Django 2.0.8 on 2018-08-29 09:35

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0007_auto_20180827_1833'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='experimentjob',
            name='tolerations',
        ),
        migrations.AddField(
            model_name='experimentjob',
            name='tolerations',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
