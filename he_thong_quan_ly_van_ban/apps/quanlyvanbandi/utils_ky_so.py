import os


def _clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def sign_pdf_with_ratio(
    input_pdf_path,
    output_pdf_path,
    signature_image_path,
    x_ratio,
    y_ratio,
    pfx_path=None,
    pfx_password=None,
):
    """Chèn ảnh chữ ký lên trang cuối của PDF theo tỷ lệ tọa độ người dùng chọn."""
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("Thiếu thư viện PyMuPDF để xử lý PDF.") from exc

    if not input_pdf_path or not str(input_pdf_path).lower().endswith(".pdf"):
        raise ValueError("Chỉ hỗ trợ ký số trên file PDF.")
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Không tìm thấy file PDF đầu vào: {input_pdf_path}")
    if not os.path.exists(signature_image_path):
        raise FileNotFoundError(f"Không tìm thấy file ảnh chữ ký: {signature_image_path}")
    if pfx_path and not os.path.exists(pfx_path):
        raise FileNotFoundError(f"Không tìm thấy chứng thư số: {pfx_path}")

    os.makedirs(os.path.dirname(output_pdf_path) or ".", exist_ok=True)

    try:
        x_ratio = float(x_ratio)
        y_ratio = float(y_ratio)
    except (TypeError, ValueError) as exc:
        raise ValueError("Tọa độ chữ ký không hợp lệ.") from exc

    doc = None
    try:
        try:
            doc = fitz.open(input_pdf_path)
        except Exception as exc:
            raise ValueError("File PDF bị hỏng hoặc không đọc được.") from exc

        if doc.page_count <= 0:
            raise ValueError("File PDF không có trang nào.")

        page = doc[-1]
        page_rect = page.rect
        pdf_width = float(page_rect.width)
        pdf_height = float(page_rect.height)

        sign_width = min(150.0, pdf_width)
        sign_height = min(80.0, pdf_height)
        max_x = max(0.0, pdf_width - sign_width)
        max_y = max(0.0, pdf_height - sign_height)
        x0 = _clamp(x_ratio, 0.0, 1.0) * pdf_width
        y0 = _clamp(y_ratio, 0.0, 1.0) * pdf_height
        x0 = _clamp(x0, 0.0, max_x)
        y0 = _clamp(y0, 0.0, max_y)

        rect = fitz.Rect(x0, y0, x0 + sign_width, y0 + sign_height)

        try:
            page.insert_image(rect, filename=signature_image_path)
        except Exception as exc:
            raise ValueError("File ảnh chữ ký bị hỏng hoặc không đọc được.") from exc

        try:
            doc.save(output_pdf_path, garbage=4, deflate=True)
        except Exception as exc:
            raise RuntimeError("Không thể lưu file PDF đã ký.") from exc
    finally:
        if doc is not None:
            doc.close()
