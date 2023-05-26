from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=160)),
                ('description', models.TextField(blank=True)),
                ('position', models.PositiveIntegerField(default=0)),
                ('column', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to='boards.column')),
            ],
            options={
                'ordering': ['position', 'id'],
            },
        ),
    ]
