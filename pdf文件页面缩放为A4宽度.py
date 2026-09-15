from pypdf import PdfReader, PdfWriter

# ========== 在这里设置文件路径 ==========
INPUT_PDF = ""      # 待处理的 PDF
OUTPUT_PDF = "整理后.pdf"      # 输出的 PDF
# ========================================

A4_WIDTH_PT = 595.0            # A4 宽度 (210mm 对应的点数)

def scale_pdf_to_a4_width(input_path, output_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        # 考虑旋转后的真实显示宽度
        if page.rotation in (90, 270):
            orig_width = float(page.mediabox.height)
            orig_height = float(page.mediabox.width)
        else:
            orig_width = float(page.mediabox.width)
            orig_height = float(page.mediabox.height)

        scale = A4_WIDTH_PT / orig_width
        page.scale(sx=scale, sy=scale)   # 等比缩放

        writer.add_page(page)

    with open(output_path, "wb") as f_out:
        writer.write(f_out)
    print(f"已完成，输出文件: {output_path}")

if __name__ == "__main__":
    scale_pdf_to_a4_width(INPUT_PDF, OUTPUT_PDF)