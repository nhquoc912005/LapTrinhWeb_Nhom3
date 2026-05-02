import os
import sys
import subprocess

def sign_pdf_with_ratio(input_pdf_path, output_pdf_path, signature_image_path, x_ratio, y_ratio, pfx_path=None, pfx_password=None):
    """
    Thực hiện dán ảnh chữ ký lên trang cuối cùng của PDF sử dụng PyMuPDF.
    Tự động cài đặt PyMuPDF nếu chưa có.
    """
    try:
        import fitz
    except ImportError:
        print("Đang cài đặt PyMuPDF...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF"])
        import fitz
    
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Không tìm thấy file PDF đầu vào: {input_pdf_path}")
        
    if not os.path.exists(signature_image_path):
        raise FileNotFoundError(f"Không tìm thấy file ảnh chữ ký: {signature_image_path}")

    # Cấu hình kích thước chữ ký cứng
    SIGN_WIDTH = 150
    SIGN_HEIGHT = 80

    # Mở tài liệu PDF
    doc = fitz.open(input_pdf_path)
    
    # Lấy trang cuối cùng
    page = doc[-1]
    
    # Tính toán tọa độ hiển thị
    page_rect = page.rect
    pdf_width = page_rect.width
    pdf_height = page_rect.height
    
    # Góc trên bên trái của ảnh
    x0 = x_ratio * pdf_width
    y0 = y_ratio * pdf_height
    
    # Tạo hình chữ nhật cho ảnh
    rect = fitz.Rect(x0, y0, x0 + SIGN_WIDTH, y0 + SIGN_HEIGHT)
    
    # Chèn ảnh vào trang
    page.insert_image(rect, filename=signature_image_path)
    
    # Lưu file đã chỉnh sửa
    doc.save(output_pdf_path)
    doc.close()
