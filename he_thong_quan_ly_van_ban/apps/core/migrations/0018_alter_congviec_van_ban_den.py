from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_merge_20260430_1530"),
    ]

    operations = [
        migrations.AlterField(
            model_name="congviec",
            name="van_ban_den",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cong_viec_lien_quan",
                to="core.vanban",
            ),
        ),
    ]
