from github import Github
import json
import os
import glob
import time
import random
from datetime import datetime

def upload_to_release(repo_name, token, folder_path=None, files=None, tag_name='', release_name='', 
                     overwrite=False, draft=False, prerelease=False):
    """
    将本地文件/文件夹上传到GitHub Release
    
    参数：
    repo_name: 仓库名（格式：owner/repo）
    token: GitHub个人访问令牌
    folder_path: 要上传的文件夹路径（与files参数二选一）
    files: 要上传的单个文件路径列表（与folder_path参数二选一）
    tag_name: 关联的Git标签（如v1.0.0）
    release_name: Release显示名称
    overwrite: 是否覆盖同名文件
    draft: 是否作为草稿发布
    prerelease: 是否标记为预发布
    """
    try:
        # 初始化GitHub连接
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        # 处理文件列表
        file_list = []
        if folder_path:
            if not os.path.exists(folder_path):
                raise FileNotFoundError(f"文件夹不存在: {folder_path}")
            file_list = glob.glob(os.path.join(folder_path, '**'), recursive=True)
            file_list = [f for f in file_list if os.path.isfile(f)]
        elif files:
            file_list = [f for f in files if os.path.isfile(f)]
        else:
            raise ValueError("必须指定folder_path或files参数")

        total_files = len(file_list)
        print(f"找到 {total_files} 个文件准备上传")
        
        # 检查/创建Release
        try:
            release = repo.get_release(tag_name)
            print(f"找到已有Release：{tag_name}")
        except:
            print(f"创建新Release：{tag_name}")
            release = repo.create_git_release(
                tag=tag_name,
                name=release_name or tag_name,
                message=release_name or tag_name,
                draft=draft,
                prerelease=prerelease
            )

        # 上传文件
        uploaded_count = 0
        skipped_count = 0
        start_time = time.time()
        
        for index, local_path in enumerate(file_list, 1):
            file_name = os.path.basename(local_path)
            
            # 显示进度信息
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"[{current_time}] 处理文件 {index}/{total_files}: {file_name}")
            
            # 检查文件是否已存在
            existing_assets = [asset for asset in release.get_assets() if asset.name == file_name]
            if existing_assets:
                if overwrite:
                    print(f"  删除已存在的文件: {file_name}")
                    existing_assets[0].delete_asset()
                else:
                    print(f"  跳过已存在文件: {file_name}")
                    skipped_count += 1
                    continue

            # 上传文件
            try:
                with open(local_path, 'rb') as f:
                    release.upload_asset(
                        path=local_path,
                        content_type='application/octet-stream',
                        name=file_name,
                        label=file_name
                    )
                print(f"  成功上传: {file_name}")
                uploaded_count += 1
            except Exception as e:
                print(f"  上传失败 {file_name}: {str(e)}")
                continue

            # 如果不是最后一个文件，则等待随机时间间隔
            if index < total_files:
                wait_time = random.randint(30, 50)
                print(f"  等待 {wait_time} 秒后继续...")
                
                # 显示倒计时
                for remaining in range(wait_time, 0, -1):
                    # 每15秒显示一次进度，最后1秒每秒显示
                    if remaining % 15 == 0 or remaining <= 1:
                        print(f"    剩余等待时间: {remaining} 秒")
                    time.sleep(1)
                
                print("  继续上传下一个文件")

        # 上传完成统计
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\n上传完成!")
        print(f"总文件数: {total_files}")
        print(f"成功上传: {uploaded_count}")
        print(f"跳过文件: {skipped_count}")
        print(f"失败文件: {total_files - uploaded_count - skipped_count}")
        print(f"总耗时: {total_time:.2f} 秒 ({total_time/60:.2f} 分钟)")

        return True

    except Exception as e:
        print(f"操作失败：{str(e)}")
        return False

# 读取json文件中的GitHub的token
def get_github_key(file_path):
    try:
        # 打开并加载JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)  # 解析为字典
        
        # 获取"githubkey"的值（使用get避免键不存在时报错）
        github_key = json_data.get("githubkey")
        
        if github_key is None:
            print("JSON文件中未找到githubkey键")
        return github_key
    
    except FileNotFoundError:
        print(f"错误：文件 {file_path} 不存在")
        return None
    except json.JSONDecodeError:
        print(f"错误：文件 {file_path} 不是有效的JSON格式")
        return None
    except Exception as e:
        print(f"发生未知错误：{str(e)}")
        return None

# 使用示例
if __name__ == "__main__":
    # 配置参数
    github_token = get_github_key("github.json")
    CONFIG = {
        'repo_name': 'yupianxian9/WinBox',  # 替换为实际仓库名
        'token': github_token,   # 替换为GitHub Token
        'tag_name': '0.1.3',                    # Release关联的标签
        'folder_path': r'D:\download\1',  # 要上传的文件夹路径（与files参数二选一）
        # 'files': ['授课安排.md'],    # 或指定单独文件列表
        'release_name': 'software',
        'overwrite': True,
        'prerelease': False
    }

    # 执行上传
    upload_to_release(**CONFIG)
