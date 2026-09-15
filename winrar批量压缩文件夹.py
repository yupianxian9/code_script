import os
import subprocess
import sys
import glob

def find_winrar_executable():
    """查找WinRAR或RAR命令行工具的路径"""
    # 首先检查环境变量PATH中是否有rar.exe或winrar.exe
    for exe in ['Rar.exe', 'WinRAR.exe']:
        for path in os.environ['PATH'].split(os.pathsep):
            full_path = os.path.join(path, exe)
            if os.path.isfile(full_path):
                return full_path
    # 如果PATH中找不到，尝试常见安装目录
    common_paths = [
        r'D:\program\WinRAR\Rar.exe',
        r'D:\program\WinRAR\WinRAR.exe'
    ]
    for path in common_paths:
        if os.path.isfile(path):
            return path
    return None

def compress_folder(folder_path, rar_exe):
    """压缩单个文件夹"""
    folder_name = os.path.basename(folder_path)
    archive_name = f"{folder_name}.rar"
    
    # 构建命令参数
    cmd = [
        rar_exe,
        'a',                      # 添加压缩
        '-m5',                     # 最大压缩
        '-md128m',                  # 字典大小128MB
        '-v1900m',                  # 分卷大小1.9GB
        '-s',                       # 固态压缩
        '-rr',                      # 添加恢复记录
        '-t',                       # 压缩后测试
        '-p桜小路ルナ',               # 密码：aaa（注意-p后无空格）
        '-o+',                      # 覆盖已存在文件
        '-df',                      # 压缩后删除源文件夹
        archive_name,               # 压缩包名称
        folder_name                 # 要压缩的文件夹（相对路径）
    ]
    
    print(f"正在压缩: {folder_name}")
    try:
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"成功: {folder_name} 压缩完成")
            # 可选：打印详细输出（用于调试）
            # print(result.stdout)
        else:
            print(f"失败: {folder_name} 压缩出错，错误码 {result.returncode}")
            print(result.stderr)
    except Exception as e:
        print(f"异常: {folder_name} 压缩时发生异常: {e}")

def main():
    # 查找WinRAR可执行文件
    rar_exe = find_winrar_executable()
    if not rar_exe:
        print("错误: 未找到WinRAR或RAR命令行工具。请确保已安装WinRAR并将其添加到PATH，或修改脚本中的路径。")
        sys.exit(1)
    
    print(f"使用WinRAR: {rar_exe}")
    
    # 获取当前目录
    current_dir = os.getcwd()
    print(f"当前目录: {current_dir}")
    
    # 列出所有直接子文件夹
    items = os.listdir(current_dir)
    folders = [item for item in items if os.path.isdir(os.path.join(current_dir, item))]
    
    if not folders:
        print("当前目录下没有文件夹需要压缩。")
        return
    
    print(f"发现 {len(folders)} 个文件夹，开始压缩...")
    for folder in folders:
        compress_folder(os.path.join(current_dir, folder), rar_exe)
    
    print("所有任务完成。")

if __name__ == "__main__":
    main()
