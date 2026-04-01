from django.db import models

class ChiNhanh(models.Model):
    ten_chi_nhanh = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Chi nhánh"
        verbose_name_plural = "Chi nhánh"

    def __str__(self):
        return self.ten_chi_nhanh


class PhongBan(models.Model):
    ten_phong_ban = models.CharField(max_length=255)
    chi_nhanh = models.ForeignKey("core.ChiNhanh", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Phòng ban"
        verbose_name_plural = "Phòng ban"

    def __str__(self):
        return self.ten_phong_ban