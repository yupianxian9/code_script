import os
import time
import json
import urllib.parse
from pathlib import Path
from github import Github, GithubException
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

def batch_upload_to_folder(token, repo_name, local_dir, 
                           target_folder="", branch="main", 
                           delay=1.5, timeout=30):
    """
    批量上传本地目录到 GitHub 仓库指定文件夹（优化版：解决编码、网络、异常问题）
    
    :param token: GitHub 个人访问令牌（需 repo 权限）
    :param repo_name: 仓库名（格式：username/repo）
    :param local_dir: 本地目录绝对路径
    :param target_folder: 仓库目标文件夹（空则上传到根目录）
    :param branch: 目标分支
    :param delay: 请求间隔（秒），避免触发 API 速率限制
    :param timeout: GitHub API 请求超时时间（秒）
    """
    # 配置 GitHub 实例，增加超时设置（解决连接等待过久问题）
    # 若使用代理，添加 proxies 参数（示例：proxies={"https": "http://127.0.0.1:7890"}）
    g = Github(
        token,
        timeout=timeout,
        # proxies={"https": "http://127.0.0.1:7890"}  # 替换为你的代理地址和端口，按需启用
    )
    
    try:
        # 前置校验：验证仓库是否存在
        repo = g.get_repo(repo_name)
        print(f"✅ 成功连接到仓库：{repo_name}")
    except GithubException as e:
        print(f"❌ 无法访问仓库 {repo_name}：{str(e)}")
        return
    except Exception as e:
        print(f"❌ 仓库连接失败：{str(e)}")
        return
    
    # 校验本地目录是否存在
    local_dir_path = Path(local_dir)
    if not local_dir_path.exists() or not local_dir_path.is_dir():
        print(f"❌ 本地目录不存在或不是有效目录：{local_dir}")
        return
    
    for root, _, files in os.walk(local_dir):
        for file in files:
            local_file_path = Path(root) / file
            
            try:
                # 1. 构建兼容 GitHub 的仓库路径（优化中文编码、跨平台分隔符）
                relative_path = local_file_path.relative_to(local_dir_path)
                # 拼接目标路径，自动处理目录分隔符，无需手动替换
                repo_file_path = Path(target_folder) / relative_path
                # 转换为字符串，确保 GitHub 识别的 '/' 分隔符（兼容 Windows）
                repo_file_path_str = str(repo_file_path).replace("\\", "/")
                # 手动编码中文路径（增强兼容性，避免 PyGitHub 内部编码遗漏）
                repo_file_path_encoded = urllib.parse.quote(repo_file_path_str, safe="/")
                
                # 2. 读取文件内容（二进制模式，支持所有文件类型）
                with open(local_file_path, "rb") as f:
                    content = f.read()
                
                # 3. 检查文件大小（提前规避 100MB 限制）
                file_size = len(content) / (1024 * 1024)  # 转换为 MB
                if file_size > 100:
                    print(f"⚠️  文件过大（{file_size:.2f} MB > 100 MB），无法直接上传：{repo_file_path_str}")
                    continue
                
                # 4. 尝试更新现有文件
                try:
                    existing_file = repo.get_contents(repo_file_path_str, ref=branch)
                    repo.update_file(
                        path=repo_file_path_str,
                        message=f"Update {repo_file_path_str} [batch-upload]",
                        content=content,
                        sha=existing_file.sha,
                        branch=branch
                    )
                    print(f"🔄 已更新: {repo_file_path_str}")
                except GithubException as e:
                    if e.status == 404:  # 文件不存在，创建新文件
                        repo.create_file(
                            path=repo_file_path_str,
                            message=f"Add {repo_file_path_str} [batch-upload]",
                            content=content,
                            branch=branch
                        )
                        print(f"✅ 已创建: {repo_file_path_str}")
                    else:
                        print(f"❌ 操作文件失败 {repo_file_path_str}：{str(e)}")
                        continue
                
                # 5. 间隔延迟，避免触发 API 速率限制
                time.sleep(delay)
                
            except ConnectionError as e:
                print(f"❌ 网络连接中断：{local_file_path.name} | {str(e)}")
                time.sleep(5)  # 网络中断后，延长等待时间再继续
                continue
            except Timeout as e:
                print(f"❌ 请求超时：{local_file_path.name} | {str(e)}")
                time.sleep(5)
                continue
            except Exception as e:
                print(f"❌ 未知错误处理文件 {local_file_path.name}：{str(e)}")
                continue

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

if __name__ == "__main__":
    # 配置参数
    github_token = get_github_key("github.json")
    if not github_token:
        print("❌ 未能获取有效的 GitHub Token，程序退出")
        exit(1)
    
    REPO_NAME = "yupianxian9/Favorite_Articles"  # github仓库：用户名/仓库名
    LOCAL_DIR = r"D:\download"  # 本地目录
    TARGET_FOLDER = "落落的穿搭笔记"   # 指定仓库所在文件夹，空则根目录
    BRANCH = "main"  # 指定仓库分支,一般为main

    # 上传文件
    batch_upload_to_folder(
        token=github_token,
        repo_name=REPO_NAME,
        local_dir=LOCAL_DIR,
        target_folder=TARGET_FOLDER,
        branch=BRANCH,
        delay=1.5,
        timeout=30
    )
