import os
import shutil

def split_files_into_folders(source_folder, files_per_folder=100, folder_prefix="music"):
    """
    将源文件夹中的文件按指定数量分割到多个子文件夹中
    
    Parameters:
    source_folder (str): 源文件夹路径
    files_per_folder (int): 每个子文件夹存放的文件数量，默认为100
    folder_prefix (str): 子文件夹名称前缀，默认为"music"
    """
    
    # 获取源文件夹中的所有文件（排除子文件夹）
    all_files = [f for f in os.listdir(source_folder) 
                if os.path.isfile(os.path.join(source_folder, f))]
    
    if not all_files:
        print("源文件夹中没有文件")
        return
    
    total_files = len(all_files)
    print(f"找到 {total_files} 个文件")
    
    # 计算需要创建的子文件夹数量[1,5](@ref)
    if total_files % files_per_folder == 0:
        num_folders = total_files // files_per_folder
    else:
        num_folders = total_files // files_per_folder + 1
    
    print(f"需要创建 {num_folders} 个子文件夹")
    
    # 创建并填充子文件夹
    for folder_index in range(1, num_folders + 1):
        # 创建子文件夹名称[6,8](@ref)
        folder_name = f"{folder_prefix}{folder_index}"
        folder_path = os.path.join(source_folder, folder_name)
        
        # 如果文件夹已存在，提示并跳过[5](@ref)
        if os.path.exists(folder_path):
            print(f"警告：文件夹 {folder_name} 已存在，跳过")
            continue
            
        os.makedirs(folder_path)
        print(f"创建文件夹: {folder_name}")
        
        # 计算当前文件夹应包含的文件范围[1](@ref)
        start_index = (folder_index - 1) * files_per_folder
        end_index = min(folder_index * files_per_folder, total_files)
        
        # 将文件移动到子文件夹中[1,4](@ref)
        files_for_this_folder = all_files[start_index:end_index]
        for file_name in files_for_this_folder:
            source_path = os.path.join(source_folder, file_name)
            destination_path = os.path.join(folder_path, file_name)
            shutil.move(source_path, destination_path)  
        
        print(f"  已将 {len(files_for_this_folder)} 个文件移动到 {folder_name}")
    
    print("文件分割完成！")

# 使用示例
if __name__ == "__main__":
    # 设置源文件夹路径（请修改为实际路径）
    source_directory = r"./music"  # 例如: "C:\\Users\\YourName\\Music"
    
    # 调用函数，每100个文件一个文件夹
    split_files_into_folders(source_directory, files_per_folder=100, folder_prefix="music")