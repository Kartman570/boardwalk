from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0003_membership_membership_unique_membership'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='revision',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
