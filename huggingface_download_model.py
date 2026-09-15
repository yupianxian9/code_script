import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 核心配置

from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="BAAI/bge-large-zh-v1.5",
    local_dir="./models",  # 自定义路径避免权限问题
    local_dir_use_symlinks=False,  # 禁用符号链接
    resume_download=True,  # 启用断点续传
    max_workers=8
)