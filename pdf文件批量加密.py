import os
from PyPDF2 import PdfReader, PdfWriter
from typing import List, Optional

def get_all_pdf_files(folder_path: str) -> List[str]:
    """遍历指定文件夹（含子文件夹），获取所有PDF文件路径"""
    pdf_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.abspath(os.path.join(root, file)))
    return pdf_files

def encrypt_pdf(input_path: str, output_path: str, password: str) -> bool:
    """单个PDF文件加密"""
    try:
        reader = PdfReader(input_path)
        
        # 跳过已加密文件
        if reader.is_encrypted:
            print(f"⚠️  {os.path.basename(input_path)} 已加密，跳过")
            return False
        
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        
        # 128位AES加密（高兼容性+安全性）
        writer.encrypt(user_password=password, use_128bit=True)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        print(f"✅ 成功加密：{os.path.basename(input_path)}")
        return True
    
    except Exception as e:
        print(f"❌ 加密失败 {os.path.basename(input_path)}：{str(e)}")
        return False

def batch_encrypt_pdfs(
    folder_path: str,
    password: str,
    overwrite: bool = False,
    output_folder: Optional[str] = None
) -> None:
    """批量加密核心函数"""
    # 验证文件夹有效性
    if not os.path.isdir(folder_path):
        print(f"❌ 错误：{folder_path} 不是有效的文件夹！")
        return
    
    # 获取所有PDF文件
    pdf_files = get_all_pdf_files(folder_path)
    if not pdf_files:
        print("ℹ️  未找到任何PDF文件！")
        return
    
    print(f"ℹ️  找到 {len(pdf_files)} 个PDF文件，开始加密...\n")
    
    # 处理输出文件夹
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        print(f"ℹ️  加密文件将保存到：{output_folder}\n")
    
    # 批量处理
    success_count = 0
    for pdf_file in pdf_files:
        # 构建输出路径
        if overwrite:
            output_path = pdf_file
        else:
            file_name = os.path.basename(pdf_file)
            name_without_ext = os.path.splitext(file_name)[0]
            encrypted_name = f"{name_without_ext}_encrypted.pdf"
            
            # 确定输出文件夹
            if output_folder:
                output_path = os.path.join(output_folder, encrypted_name)
            else:
                output_path = os.path.join(os.path.dirname(pdf_file), encrypted_name)
        
        # 跳过已存在的文件（避免覆盖）
        if not overwrite and os.path.exists(output_path):
            print(f"⚠️  {encrypted_name} 已存在，跳过\n")
            continue
        
        # 执行加密
        if encrypt_pdf(pdf_file, output_path, password):
            success_count += 1
        print("-" * 40)
    
    # 输出统计结果
    print("\n" + "="*50)
    print(f"📊 加密完成！")
    print(f"总计文件：{len(pdf_files)}")
    print(f"成功加密：{success_count}")
    print(f"失败/跳过：{len(pdf_files) - success_count}")
    print("="*50)

def main():
    # --------------------------
    # 👇 在这里修改你的配置参数 👇
    # --------------------------
    FOLDER_PATH = r""  # PDF文件所在文件夹（必填）
    ENCRYPT_PASSWORD = ""      # 加密密码（必填，建议复杂密码）
    OVERWRITE = True                # 是否覆盖原文件（True=覆盖，False=保留原文件）
    OUTPUT_FOLDER = None             # 自定义输出文件夹（None=使用原文件夹，例：r"D:\加密后的PDF"）
    # --------------------------

    # 调用批量加密函数
    batch_encrypt_pdfs(
        folder_path=FOLDER_PATH,
        password=ENCRYPT_PASSWORD,
        overwrite=OVERWRITE,
        output_folder=OUTPUT_FOLDER
    )

if __name__ == "__main__":
    main()