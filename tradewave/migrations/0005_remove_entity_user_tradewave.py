# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-15 05:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tradewave', '0004_entity_user_tradewave'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entity',
            name='user_tradewave',
        ),
    ]
