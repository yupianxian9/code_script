# 导入仓库所需的模块
from github import Github, GithubException
import json
import os
import requests
from typing import List, Dict, Any, Optional

# 定义类
class GitHubRepoInfo:
    def __init__(self, token: str):
        self.token = token
        self.github = Github(self.token)

    # 方法1：获取所有仓库的基本信息
    def get_all_repos_info(self) -> List[Dict[str, Any]]:
        """获取用户的所有仓库信息"""
        try:
            repos_info = []
            for repo in self.github.get_user().get_repos():
                repo_info = {
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'clone_url': repo.clone_url,
                    'html_url': repo.html_url,
                    'created_at': repo.created_at.isoformat() if repo.created_at else None,
                    'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
                    'pushed_at': repo.pushed_at.isoformat() if repo.pushed_at else None,
                    'size': repo.size,
                    'stargazers_count': repo.stargazers_count,
                    'watchers_count': repo.watchers_count,
                    'forks_count': repo.forks_count,
                    'language': repo.language,
                    'private': repo.private
                }
                repos_info.append(repo_info)
            return repos_info
        except GithubException as e:
            print(f"获取仓库信息时出错: {e}")
            return []
        except Exception as e:
            print(f"发生未知错误: {e}")
            return []

    # 方法2：获取特定仓库的目录树结构
    def get_repo_tree(self, repo_name: str) -> Dict[str, Any]:
        """获取仓库的目录树结构"""
        try:
            repo = self.github.get_repo(repo_name)
            contents = repo.get_contents("")
            tree_structure = self._build_tree_structure(contents, repo)
            return {
                'repo_name': repo_name,
                'tree': tree_structure
            }
        except GithubException as e:
            print(f"获取仓库目录树时出错: {e}")
            return {'repo_name': repo_name, 'tree': {}, 'error': str(e)}
        except Exception as e:
            print(f"发生未知错误: {e}")
            return {'repo_name': repo_name, 'tree': {}, 'error': str(e)}

    def _build_tree_structure(self, contents, repo, path="") -> Dict[str, Any]:
        """递归构建目录树结构"""
        tree = {}
        for content in contents:
            if content.type == "dir":
                # 递归获取子目录内容
                try:
                    sub_contents = repo.get_contents(content.path)
                    tree[content.name] = {
                        'type': 'directory',
                        'path': content.path,
                        'children': self._build_tree_structure(sub_contents, repo, content.path)
                    }
                except GithubException:
                    tree[content.name] = {
                        'type': 'directory',
                        'path': content.path,
                        'children': {},
                        'error': '无法访问此目录'
                    }
            else:
                tree[content.name] = {
                    'type': 'file',
                    'path': content.path,
                    'size': content.size,
                    'download_url': content.download_url
                }
        return tree

    # 方法3：获取特定仓库的release信息
    def get_repo_releases(self, repo_name: str) -> List[Dict[str, Any]]:
        """获取仓库的所有release信息"""
        try:
            repo = self.github.get_repo(repo_name)
            releases = []
            for release in repo.get_releases():
                release_info = {
                    'tag_name': release.tag_name,
                    'name': release.title,
                    'body': release.body,
                    'created_at': release.created_at.isoformat() if release.created_at else None,
                    'published_at': release.published_at.isoformat() if release.published_at else None,
                    'prerelease': release.prerelease,
                    'draft': release.draft,
                    'assets': []
                }
                
                # 获取release中的资源文件
                for asset in release.get_assets():
                    asset_info = {
                        'name': asset.name,
                        'size': asset.size,
                        'download_url': asset.browser_download_url,
                        'content_type': asset.content_type
                    }
                    release_info['assets'].append(asset_info)
                
                releases.append(release_info)
            return releases
        except GithubException as e:
            print(f"获取release信息时出错: {e}")
            return []
        except Exception as e:
            print(f"发生未知错误: {e}")
            return []

    # 方法4：下载特定仓库的特定文件
    def download_repo_files(self, repo_name: str, file_paths: List[str], download_dir: str) -> Dict[str, str]:
        """下载仓库中的特定文件"""
        results = {}
        try:
            repo = self.github.get_repo(repo_name)
            
            # 确保下载目录存在
            os.makedirs(download_dir, exist_ok=True)
            
            for file_path in file_paths:
                try:
                    content = repo.get_contents(file_path)
                    if content.type != "file":
                        results[file_path] = f"错误: {file_path} 不是文件"
                        continue
                    
                    # 下载文件
                    download_url = content.download_url
                    if download_url:
                        response = requests.get(download_url)
                        if response.status_code == 200:
                            # 创建子目录（如果需要）
                            file_dir = os.path.join(download_dir, os.path.dirname(file_path))
                            os.makedirs(file_dir, exist_ok=True)
                            
                            # 保存文件
                            file_full_path = os.path.join(download_dir, file_path)
                            with open(file_full_path, 'wb') as f:
                                f.write(response.content)
                            results[file_path] = f"成功: 已下载到 {file_full_path}"
                        else:
                            results[file_path] = f"错误: 下载失败，状态码 {response.status_code}"
                    else:
                        results[file_path] = f"错误: 无法获取下载链接"
                        
                except GithubException as e:
                    results[file_path] = f"错误: {str(e)}"
                except Exception as e:
                    results[file_path] = f"错误: {str(e)}"
                    
        except GithubException as e:
            print(f"访问仓库时出错: {e}")
            return {'error': f"访问仓库时出错: {str(e)}"}
        except Exception as e:
            print(f"发生未知错误: {e}")
            return {'error': f"发生未知错误: {str(e)}"}
        
        return results

    @staticmethod
    def print_tree_structure(tree: Dict[str, Any], indent: int = 0):
        """递归打印目录树结构"""
        for name, info in tree.items():
            if info['type'] == 'directory':
                print("  " * indent + f"📁 {name}/")
                if 'children' in info:
                    GitHubRepoInfo.print_tree_structure(info['children'], indent + 1)
            else:
                print("  " * indent + f"📄 {name}")

# 读取github.json文件获取token
def read_github_token_from_json(file_path: str) -> str:
    """从JSON文件中读取GitHub token"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        token = data.get("githubkey", "")
        if not token:
            print(f"警告: 在 {file_path} 中未找到 githubkey")
        return token
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在")
        return ""
    except json.JSONDecodeError:
        print(f"错误: {file_path} 不是有效的JSON文件")
        return ""
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return ""

# 定义一个函数，能够选择性地调用类中的方法
def main(token_file: str = "github.json", action: Optional[str] = None, 
         repo_name: Optional[str] = None, file_paths: Optional[List[str]] = None, 
         download_dir: Optional[str] = None) -> Any:
    """
    主函数，支持通过参数控制GitHub仓库操作
    
    Args:
        token_file: GitHub token存储的JSON文件路径
        action: 操作类型 ("1", "2", "3", "4")
        repo_name: 仓库名称（操作2,3,4需要）
        file_paths: 文件路径列表（操作4需要）
        download_dir: 下载目录（操作4需要）
    """
    token = read_github_token_from_json(token_file)
    if not token:
        print(f"无法获取有效的GitHub token，请检查 {token_file} 文件")
        return None

    try:
        github_info = GitHubRepoInfo(token)
        
        # 测试token有效性
        user = github_info.github.get_user()
        print(f"成功连接到GitHub，用户: {user.login}")

        # 如果未提供action参数，则通过输入获取
        if action is None:
            action = input("选择操作：1-获取所有仓库信息, 2-获取仓库目录树, 3-获取仓库release信息, 4-下载仓库文件: ")
        
        if action == "1":
            print("正在获取所有仓库信息...")
            repos_info = github_info.get_all_repos_info()
            print(f"\n找到 {len(repos_info)} 个仓库:\n")
            
            for i, repo in enumerate(repos_info, 1):
                print(f"{i}. 名称: {repo['name']}")
                print(f"   全名: {repo['full_name']}")
                print(f"   描述: {repo['description'] or '无描述'}")
                print(f"   语言: {repo['language'] or '未知'}")
                print(f"   星标: {repo['stargazers_count']}, 复刻: {repo['forks_count']}")
                print(f"   克隆URL: {repo['clone_url']}")
                print(f"   私有: {'是' if repo['private'] else '否'}")
                print(f"   创建时间: {repo['created_at']}")
                print("-" * 50)
            
            return repos_info

        elif action == "2":
            if repo_name is None:
                repo_name = input("输入仓库名称 (格式: 用户名/仓库名): ")
            
            print(f"正在获取仓库 {repo_name} 的目录树...")
            tree_info = github_info.get_repo_tree(repo_name)
            
            if 'error' in tree_info:
                print(f"错误: {tree_info['error']}")
                return tree_info
            
            print(f"\n仓库 {repo_name} 的目录结构:\n")
            GitHubRepoInfo.print_tree_structure(tree_info['tree'])
            return tree_info
        
        elif action == "3":
            if repo_name is None:
                repo_name = input("输入仓库名称 (格式: 用户名/仓库名): ")
            
            print(f"正在获取仓库 {repo_name} 的release信息...")
            releases = github_info.get_repo_releases(repo_name)
            
            if not releases:
                print(f"仓库 {repo_name} 没有release信息或无法访问")
                return []
            
            print(f"\n仓库 {repo_name} 的release信息:\n")
            for i, release in enumerate(releases, 1):
                print(f"{i}. 版本: {release['tag_name']}")
                print(f"   名称: {release['name']}")
                print(f"   发布时间: {release['published_at']}")
                print(f"   预发布: {'是' if release['prerelease'] else '否'}")
                print(f"   草稿: {'是' if release['draft'] else '否'}")
                print(f"   资源文件: {len(release['assets'])} 个")
                if release['assets']:
                    for asset in release['assets']:
                        print(f"     - {asset['name']} ({asset['size']} 字节)")
                print("-" * 50)
            
            return releases

        elif action == "4":
            if repo_name is None:
                repo_name = input("输入仓库名称 (格式: 用户名/仓库名): ")
            if file_paths is None:
                file_paths_input = input("输入文件路径列表（逗号分隔）: ")
                file_paths = [path.strip() for path in file_paths_input.split(',') if path.strip()]
            if download_dir is None:
                download_dir = input("输入下载目录: ")
            
            if not file_paths:
                print("错误: 未提供要下载的文件路径")
                return None
            
            print(f"正在从仓库 {repo_name} 下载文件...")
            results = github_info.download_repo_files(repo_name, file_paths, download_dir)
            
            print("\n下载结果:")
            for file_path, result in results.items():
                print(f"{file_path}: {result}")
            
            return results
        
        else:
            print("无效的操作选择")
            return None
            
    except GithubException as e:
        print(f"GitHub API错误: {e}")
        return None
    except Exception as e:
        print(f"程序执行出错: {e}")
        return None

# 使用示例：
if __name__ == "__main__":
    # 参数配置区域，字典形式
    params = {
        "token_file": "github.json",
        "action": "4",  # 可选值：1-获取所有仓库信息, 2-获取仓库目录树, 3-获取仓库release信息, 4-下载仓库文件
        "repo_name": None,  # 仅当action为"2","3","4"时需要，默认为None
        "file_paths": None,  # 仓库文件路径，仅当action为"4"时需要，默认为None
        "download_dir": None,  # 下载路径，仅当action为"4"时需要，默认为None
    }
    # "file_paths"参数示例：["README.md", "src/main.py"]

    main(**params)