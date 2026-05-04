from django.db.models.functions import Trim

from apps.core.models import VanBan


DUPLICATE_SO_KY_HIEU_TRICH_YEU_MESSAGE = (
    "Số ký hiệu và trích yếu này đã tồn tại. Vui lòng kiểm tra lại."
)


def normalize_document_text(value):
    return (value or "").strip()


def document_pair_exists(*, phan_loai, so_ky_hieu, trich_yeu, exclude_pk=None):
    so_ky_hieu = normalize_document_text(so_ky_hieu)
    trich_yeu = normalize_document_text(trich_yeu)
    if not so_ky_hieu or not trich_yeu:
        return False

    qs = (
        VanBan.objects.filter(phan_loai=phan_loai)
        .annotate(
            so_ky_hieu_clean=Trim("so_ky_hieu"),
            trich_yeu_clean=Trim("trich_yeu"),
        )
        .filter(
            so_ky_hieu_clean__iexact=so_ky_hieu,
            trich_yeu_clean__iexact=trich_yeu,
        )
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    return qs.exists()
