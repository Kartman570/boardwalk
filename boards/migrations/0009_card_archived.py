from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0008_label_card_labels_label_unique_board_label'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
