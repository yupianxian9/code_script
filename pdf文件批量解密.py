import os
import pikepdf

def batch_decrypt_pdfs(input_folder, output_folder, password):
    """
    批量解密PDF文件
    
    Args:
        input_folder: 加密PDF所在文件夹路径
        output_folder: 解密后PDF保存路径
        password: 解密密码
    """
    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 遍历输入文件夹中的所有PDF文件
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.pdf'):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            
            try:
                # 使用密码打开并解密PDF
                with pikepdf.open(input_path, password=password) as pdf:
                    pdf.save(output_path)
                print(f"成功解密: {filename}")
            except Exception as e:
                print(f"解密失败 {filename}: {str(e)}")

# 使用示例
if __name__ == "__main__":
    input_folder = "1"  # 加密PDF文件夹
    output_folder = "2"  # 解密后PDF文件夹
    password = ""  # 解密密码
    
    batch_decrypt_pdfs(input_folder, output_folder, password)