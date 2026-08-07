 
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
 
 
class Migration(migrations.Migration):
 
    dependencies = [
        ('miniapp', '0004_student'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
 
    operations = [
        migrations.AddField(
            model_name='book',
            name='category',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='book',
            name='shelf_location',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.CreateModel(
            name='IssueRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('requested', 'Requested'),
                        ('reserved', 'Reserved'),
                        ('issued', 'Issued'),
                        ('returned', 'Returned'),
                        ('rejected', 'Rejected'),
                    ],
                    default='requested', max_length=10,
                )),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('issue_date', models.DateField(blank=True, null=True)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('return_date', models.DateField(blank=True, null=True)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issue_records', to='miniapp.book')),
                ('copy', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='issue_records', to='miniapp.bookcopy')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issue_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-requested_at'],
            },
        ),
    ]
 