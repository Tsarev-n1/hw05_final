# Generated by Django 2.2.9 on 2022-02-10 14:57

from django.db import migrations, models
import enum


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20220210_1755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(verbose_name=enum.unique),
        ),
    ]