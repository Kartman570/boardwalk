from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0004_card_revision'),
    ]

    operations = [
        migrations.AddField(
            model_name='column',
            name='limit',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
