import os
import time
import random
import hashlib
import base64
import json
from github import Github
from github import GithubException

# GitHub仓库同步器
class GitHubSync:
    def __init__(self, config):
        """初始化GitHub同步器（基于配置字典）"""
        # 验证配置必填项
        required_keys = ['github_token', 'repo_full_name', 'local_repo_path']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"配置缺少必填项: {key}")

        # 基础配置
        self.github_token = config['github_token']
        self.repo_full_name = config['repo_full_name']  # 格式: "用户名/仓库名"
        self.local_repo_path = os.path.abspath(config['local_repo_path'])
        
        # 可选配置（带默认值）
        self.verbose = config.get('verbose', True)
        self.batch_size = config.get('batch_size', 30)
        self.large_delay = config.get('large_delay', 5)
        self.min_random_delay = config.get('min_random_delay', 0.5)
        self.max_random_delay = config.get('max_random_delay', 1.5)

        # 初始化GitHub连接
        self.github = Github(self.github_token)
        try:
            self.repo = self.github.get_repo(self.repo_full_name)
        except GithubException as e:
            raise Exception(f"无法访问仓库 {self.repo_full_name}: {str(e)}")

        # 状态变量
        self.request_count = 0  # 请求计数器

        # 确保本地目录存在
        if not os.path.exists(self.local_repo_path):
            os.makedirs(self.local_repo_path)
            self._log(f"创建本地仓库目录: {self.local_repo_path}")

    def _log(self, message):
        """打印日志（根据verbose配置）"""
        if self.verbose:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def _random_delay(self):
        """添加随机延迟，并在达到批量阈值时增加大间隔"""
        delay = random.uniform(self.min_random_delay, self.max_random_delay)
        time.sleep(delay)

        self.request_count += 1
        if self.request_count % self.batch_size == 0:
            self._log(f"已处理{self.request_count}个请求，触发{self.large_delay}秒批量间隔...")
            time.sleep(self.large_delay)

    def _is_binary_file(self, file_path):
        """判断文件是否为二进制文件（通过检测空字节）"""
        try:
            with open(file_path, 'rb') as f:
                return b'\x00' in f.read(1024)  # 读取前1024字节检测空字节
        except Exception as e:
            self._log(f"判断文件类型失败 {file_path}: {str(e)}")
            return False  # 默认为文本文件

    def _get_local_file_hash(self, file_path, is_binary):
        """计算本地文件的哈希值（二进制文件使用Git兼容的哈希方式）"""
        hash_obj = hashlib.sha1()  # Git使用SHA-1而非SHA-256
        try:
            with open(file_path, 'rb') as f:
                # 对于二进制文件，模拟Git的哈希计算方式（添加元数据前缀）
                if is_binary:
                    hash_obj.update(f"blob {os.path.getsize(file_path)}\0".encode('utf-8'))
                while chunk := f.read(4096):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            self._log(f"计算本地文件哈希失败 {file_path}: {str(e)}")
            return None

    def _get_local_files(self):
        """获取本地所有文件的相对路径（Unix风格）"""
        local_files = []
        for root, _, files in os.walk(self.local_repo_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.local_repo_path)
                local_files.append(rel_path.replace(os.sep, '/'))
        return local_files

    def _get_github_files(self):
        """获取GitHub仓库所有文件的路径列表"""
        github_files = []
        try:
            contents = self.repo.get_contents("")
            self._random_delay()

            while contents:
                item = contents.pop(0)
                if item.type == "dir":
                    try:
                        contents.extend(self.repo.get_contents(item.path))
                        self._random_delay()
                    except GithubException as e:
                        self._log(f"无法获取目录 {item.path} 内容: {str(e)}")
                else:
                    github_files.append(item.path)
        except GithubException as e:
            self._log(f"获取GitHub文件列表失败: {str(e)}")
        return github_files

    def _files_differ(self, local_rel_path):
        """比较本地文件与GitHub文件是否不同（核心优化点）"""
        local_full_path = os.path.join(self.local_repo_path, local_rel_path.replace('/', os.sep))
        if not os.path.exists(local_full_path):
            self._log(f"本地文件不存在: {local_full_path}")
            return False

        is_binary = self._is_binary_file(local_full_path)

        try:
            # 获取GitHub文件信息（包含sha属性）
            github_file = self.repo.get_contents(local_rel_path)
            self._random_delay()

            if is_binary:
                # 二进制文件：本地计算Git兼容哈希 vs GitHub返回的sha
                local_hash = self._get_local_file_hash(local_full_path, is_binary=True)
                if not local_hash:
                    return True  # 哈希计算失败时默认需要更新
                # 直接比较本地哈希与GitHub返回的sha（关键修复）
                return local_hash != github_file.sha
            else:
                # 文本文件：直接比较内容（UTF-8编码）
                with open(local_full_path, 'r', encoding='utf-8') as f:
                    local_content = f.read()
                github_content = github_file.decoded_content.decode('utf-8')
                return local_content != github_content

        except GithubException as e:
            self._log(f"GitHub API错误（比较文件）: {str(e)}")
            return True
        except UnicodeDecodeError:
            self._log(f"文本文件解码失败（可能是二进制文件）: {local_rel_path}")
            return True
        except Exception as e:
            self._log(f"比较文件失败 {local_rel_path}: {str(e)}")
            return True

    def _upload_file(self, local_rel_path):
        """上传本地新增文件到GitHub"""
        local_full_path = os.path.join(self.local_repo_path, local_rel_path.replace('/', os.sep))
        if not os.path.exists(local_full_path):
            self._log(f"跳过上传：文件不存在 {local_full_path}")
            return False

        is_binary = self._is_binary_file(local_full_path)

        try:
            with open(local_full_path, 'rb' if is_binary else 'r', encoding='utf-8' if not is_binary else None) as f:
                content = f.read()

            if not is_binary and isinstance(content, bytes):
                content = content.decode('utf-8')

            self.repo.create_file(
                path=local_rel_path,
                message=f"Add: {local_rel_path}",
                content=content
            )
            self._log(f"✅ 上传成功: {local_rel_path}")
            self._random_delay()
            return True
        except Exception as e:
            self._log(f"❌ 上传失败 {local_rel_path}: {str(e)}")
            return False

    def _update_file(self, local_rel_path):
        """更新GitHub上已存在的文件"""
        local_full_path = os.path.join(self.local_repo_path, local_rel_path.replace('/', os.sep))
        if not os.path.exists(local_full_path):
            self._log(f"跳过更新：文件不存在 {local_full_path}")
            return False

        is_binary = self._is_binary_file(local_full_path)

        try:
            github_file = self.repo.get_contents(local_rel_path)
            self._random_delay()

            with open(local_full_path, 'rb' if is_binary else 'r', encoding='utf-8' if not is_binary else None) as f:
                new_content = f.read()

            if not is_binary and isinstance(new_content, bytes):
                new_content = new_content.decode('utf-8')

            self.repo.update_file(
                path=local_rel_path,
                message=f"Update: {local_rel_path}",
                content=new_content,
                sha=github_file.sha
            )
            self._log(f"🔄 更新成功: {local_rel_path}")
            self._random_delay()
            return True
        except Exception as e:
            self._log(f"❌ 更新失败 {local_rel_path}: {str(e)}")
            return False

    def _delete_file(self, github_rel_path):
        """删除GitHub上本地不存在的文件"""
        try:
            github_file = self.repo.get_contents(github_rel_path)
            self._random_delay()

            self.repo.delete_file(
                path=github_rel_path,
                message=f"Delete: {github_rel_path}",
                sha=github_file.sha
            )
            self._log(f"🗑️ 删除成功: {github_rel_path}")
            self._random_delay()
            return True
        except Exception as e:
            self._log(f"❌ 删除失败 {github_rel_path}: {str(e)}")
            return False

    def sync(self):
        """执行本地到GitHub的同步（使云端与本地一致）"""
        self._log(f"开始同步 [{self.repo_full_name}] <- [{self.local_repo_path}]")

        local_files = self._get_local_files()
        github_files = self._get_github_files()

        self._log(f"本地文件: {len(local_files)} 个 | 云端文件: {len(github_files)} 个")

        to_delete = [f for f in github_files if f not in local_files]
        to_upload = [f for f in local_files if f not in github_files]
        to_update = [f for f in local_files if f in github_files and self._files_differ(f)]

        self._log(f"待删除: {len(to_delete)} 个 | 待上传: {len(to_upload)} 个 | 待更新: {len(to_update)} 个")

        # 执行删除
        for i, file in enumerate(to_delete, 1):
            self._log(f"删除 ({i}/{len(to_delete)})：{file}")
            self._delete_file(file)

        # 执行上传
        for i, file in enumerate(to_upload, 1):
            self._log(f"上传 ({i}/{len(to_upload)})：{file}")
            self._upload_file(file)

        # 执行更新
        for i, file in enumerate(to_update, 1):
            self._log(f"更新 ({i}/{len(to_update)})：{file}")
            self._update_file(file)

        self._log("同步完成！")


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


# --------------------------
# 配置区域（用户仅需修改这里）
# --------------------------
if __name__ == "__main__":

    github_token = get_github_key("github.json")
    sync_config = {
        # 必配项
        "github_token": github_token,  # GitHub个人访问令牌（需含repo权限）
        "repo_full_name": "yupianxian9/test",  # 云端仓库（格式：用户名/仓库名）
        "local_repo_path": r"D:\download",  # 本地仓库路径

        # 可选项
        "verbose": True,
        "batch_size": 25,    # 每"batch_size"次请求进行一次大延迟间隔
        "large_delay": 15,    # 大延迟间隔时间，秒
        "min_random_delay": 1,   # 每次请求的随即延迟最低时间，秒
        "max_random_delay": 3    # 每次请求的随即延迟最高时间，秒
    }

    try:
        sync_handler = GitHubSync(sync_config)
        sync_handler.sync()
    except Exception as e:
        print(f"同步失败: {str(e)}")

