from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="organizationinvite",
            name="canceled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
