# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='author_name',
        ),
        migrations.AlterField(
            model_name='comment',
            name='author_email',
            field=models.EmailField(blank=True, null=True, verbose_name='Email autora'),
        ),
    ]
