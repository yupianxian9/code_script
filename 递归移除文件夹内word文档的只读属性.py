import os
import stat

def remove_readonly_attr(file_path):
    """移除文件系统层面的只读属性"""
    if os.path.exists(file_path):
        try:
            # 获取文件当前权限
            file_attr = os.stat(file_path).st_mode
            # 移除只读属性（保留其他属性）
            os.chmod(file_path, file_attr | stat.S_IWRITE)
            print(f"✅ 已移除只读属性：{file_path}")
        except Exception as e:
            print(f"❌ 处理失败：{file_path} | 错误：{str(e)}")

def traverse_remove_readonly(folder_path):
    """遍历文件夹（含子文件夹）移除所有Word文档的只读属性"""
    # 支持的Word后缀（可根据需要扩展，如保留所有文件则注释此行）
    word_suffixes = (".doc", ".docx")
    
    # 遍历所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 过滤出Word文档（排除临时文件~$开头），如需处理所有文件则删除if判断
            if file.lower().endswith(word_suffixes) and not file.startswith("~$"):
                file_path = os.path.join(root, file)
                remove_readonly_attr(file_path)

if __name__ == "__main__":
    # 输入文件夹路径（建议使用绝对路径，如：C:/test/人工智能金融002班实验报告2）
    input_folder = "./人工智能金融002班实验报告2"
    
    # 检查文件夹是否存在
    if not os.path.exists(input_folder):
        print(f"错误：输入文件夹不存在！路径：{input_folder}")
    else:
        print(f"开始处理文件夹：{input_folder}")
        print("="*50)
        traverse_remove_readonly(input_folder)
        print("="*50)
        print("\n所有文件只读属性移除完成！")