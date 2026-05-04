from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_vanbanduyet_ghi_chu_vanbanhoantra_han_xu_ly_hoan_tra"),
    ]

    operations = [
        migrations.AddField(
            model_name="noinhanvanban",
            name="trang_thai_nguoi_nhan",
            field=models.CharField(default="Xem Để Biết", max_length=50),
        ),
    ]
