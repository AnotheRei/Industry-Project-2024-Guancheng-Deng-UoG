# Generated by Django 4.1 on 2024-07-28 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_alter_financialdata_fee_rate_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financialdata',
            name='fee_rate',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='financialdata',
            name='penalty_rate',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='financialdata',
            name='rent_scaling_rate',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
