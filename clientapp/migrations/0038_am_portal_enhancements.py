# Generated migration for Account Manager portal enhancements
# Adds preferred_client_type to Lead, is_locked and preferred_production_lead to Quote

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clientapp', '0037_remove_vendorspecialty_vendors_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='preferred_client_type',
            field=models.CharField(
                choices=[('B2B', 'B2B Business'), ('B2C', 'B2C Retail')],
                default='B2B',
                help_text='Client type lead will convert to (B2B/B2C)',
                max_length=10
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='is_locked',
            field=models.BooleanField(
                default=False,
                help_text='When True (after Approval), quote is read-only. Changes require revision.'
            ),
        ),
        migrations.AddField(
            model_name='quote',
            name='preferred_production_lead',
            field=models.ForeignKey(
                blank=True,
                help_text='Production Team member to assign job to when quote is approved',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='preferred_production_quotes',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
