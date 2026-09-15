#!/usr/bin/env python3
from pathlib import Path
import shutil

# 修改成你要整理的文件夹路径
TARGET_DIR = Path(r"音乐")

BATCH_SIZE = 200

def main():
    root = TARGET_DIR.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"不是有效文件夹: {root}")

    # 如果脚本放在目标文件夹内，避免把脚本自己也移动了
    script_path = Path(__file__).resolve() if "__file__" in globals() else None

    files = []
    for p in root.iterdir():
        if p.is_file():
            if script_path and p.resolve() == script_path:
                continue
            files.append(p)

    # 按文件名排序，保证分组稳定
    files.sort(key=lambda p: p.name)

    for i, file_path in enumerate(files, start=1):
        subdir_name = str((i - 1) // BATCH_SIZE + 1)
        subdir = root / subdir_name
        subdir.mkdir(exist_ok=True)

        dest = subdir / file_path.name
        if dest.exists():
            raise SystemExit(f"目标已存在，停止，避免覆盖：{dest}")

        shutil.move(str(file_path), str(dest))

    total_dirs = (len(files) - 1) // BATCH_SIZE + 1 if files else 0
    print(f"完成：移动 {len(files)} 个文件，生成 {total_dirs} 个子文件夹。")

if __name__ == "__main__":
    main()