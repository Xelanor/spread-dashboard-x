# Generated by Django 3.2.9 on 2024-09-12 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spread', '0003_finderscore'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricSpread',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exchange', models.CharField(max_length=255)),
                ('ticker', models.CharField(max_length=255)),
                ('spread', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
