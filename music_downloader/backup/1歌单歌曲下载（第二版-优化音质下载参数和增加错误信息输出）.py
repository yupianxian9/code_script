import os
import sys
import csv
import time
import random
from typing import Dict, Any, List
from datetime import datetime

# 确保 yt-dlp 已安装
try:
    import yt_dlp
except ImportError:
    print("错误：yt-dlp 库未安装。")
    print("请使用 'pip install yt-dlp' 命令进行安装。")
    sys.exit(1)


# ========================== 参数配置区 ==========================

# 1. CSV 文件路径: 包含歌名和链接的 CSV 文件
CSV_FILE: str = "qqmusic_playlist.csv"

# 2. Cookie 文件路径: QQ 音乐需要登录才能获取高品质音源，请提供 Netscape 格式的 Cookie 文件
COOKIE_FILE: str = "y.qq.com_cookies.txt"

# 3. 输出目录: 所有下载的歌曲和歌词文件都将保存在此目录下
OUTPUT_DIR: str = "QQ_Music_Downloads"

# 4. 错误记录文件路径
ERROR_CSV_FILE: str = "download_errors.csv"

# ===============================================================


def check_files() -> None:
    """
    检查必要的文件是否存在
    """
    # 检查 Cookie 文件是否存在，若不存在则创建并提示
    if not os.path.exists(COOKIE_FILE):
        print(f"警告：Cookie 文件 '{COOKIE_FILE}' 不存在。")
        print("已为您创建一个空白文件，请从浏览器导出 y.qq.com 的 Cookie 并粘贴到文件中。")
        print("否则可能无法下载高音质歌曲或VIP歌曲。")
        with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# http://www.netscape.com/newsref/std/cookie_spec.html\n")
            f.write("# This is a generated file! Do not edit.\n")
    
    # 检查 CSV 文件是否存在
    if not os.path.exists(CSV_FILE):
        print(f"错误：CSV 文件 '{CSV_FILE}' 不存在。")
        print("请先运行解析脚本生成 CSV 文件。")
        sys.exit(1)


def read_csv_file() -> tuple:
    """
    读取 CSV 文件，提取歌名和链接
    
    Returns:
        tuple: (包含歌曲信息的列表, 原CSV的字段名列表)
    """
    songs = []
    fieldnames = []
    try:
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                # 确保有歌名和链接
                if '歌名' in row and '链接' in row and row['歌名'] and row['链接']:
                    songs.append({
                        'title': row['歌名'],
                        'url': row['链接'],
                        'original_data': row  # 保存原始数据
                    })
        
        print(f"[*] 从 CSV 文件中读取了 {len(songs)} 首歌曲")
        return songs, fieldnames
    except Exception as e:
        print(f"[!] 读取 CSV 文件时出错: {e}")
        return [], []


def clean_file_names(output_dir: str) -> None:
    """
    清理文件名：添加音乐文件后缀，修复歌词文件名
    
    Args:
        output_dir: 输出目录路径
    """
    if not os.path.exists(output_dir):
        return
        
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        
        # 如果是目录，跳过
        if os.path.isdir(file_path):
            continue
            
        # 修复歌词文件名：移除 .origin
        if filename.endswith('.origin.lrc'):
            new_name = filename.replace('.origin.lrc', '.lrc')
            new_path = os.path.join(output_dir, new_name)
            try:
                os.rename(file_path, new_path)
                print(f"[*] 重命名歌词文件: {filename} -> {new_name}")
            except Exception as e:
                print(f"[!] 重命名歌词文件失败: {filename} - {e}")
        
        # 为没有扩展名的音乐文件添加 .mp3 扩展名
        elif '.' not in filename and not filename.endswith('.lrc'):
            # 检查文件类型
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(20)
                    # 简单的 MP3 文件头检测
                    if header.startswith(b'ID3') or header[0:2] == b'\xff\xfb':
                        new_name = filename + '.mp3'
                        new_path = os.path.join(output_dir, new_name)
                        os.rename(file_path, new_path)
                        print(f"[*] 添加扩展名: {filename} -> {new_name}")
            except Exception as e:
                print(f"[!] 处理文件 {filename} 时出错: {e}")


def export_errors_to_csv(error_records: List[dict], original_fieldnames: List[str]) -> None:
    """
    将下载失败的记录导出到CSV文件
    
    Args:
        error_records: 错误记录列表，每个元素包含原始数据和错误信息
        original_fieldnames: 原CSV文件的字段名列表
    """
    if not error_records:
        return
        
    # 添加新的字段名
    new_fieldnames = original_fieldnames + ['报错内容']
    
    try:
        with open(ERROR_CSV_FILE, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            for record in error_records:
                writer.writerow(record)
        
        print(f"[*] 已将 {len(error_records)} 条失败记录导出到: {ERROR_CSV_FILE}")
    except Exception as e:
        print(f"[!] 导出错误记录到CSV文件失败: {e}")


def download_songs(songs: list, original_fieldnames: List[str]) -> None:
    """
    逐个下载歌曲
    
    Args:
        songs: 歌曲信息列表
        original_fieldnames: 原CSV文件的字段名列表
    """
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("="*50)
    print(f"[*] 开始下载 {len(songs)} 首歌曲")
    print(f"[*] 音频质量: 320kbps MP3")
    print(f"[*] 歌词格式: LRC")
    print(f"[*] 输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print("="*50)
    
    success_count = 0
    fail_count = 0
    error_records = []  # 存储失败记录
    
    for i, song in enumerate(songs, 1):
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 清理歌名中的非法字符
        safe_title = "".join(c for c in song['title'] if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        
        # 构建输出模板 - 包含扩展名
        output_template = os.path.join(OUTPUT_DIR, f"{timestamp}-{safe_title}.%(ext)s")
        
        print(f"\n[*] 正在下载第 {i}/{len(songs)} 首: {song['title']}")
        
        # yt-dlp 选项配置
        ydl_opts: Dict[str, Any] = {
            # -- 详细输出与错误处理 --
            'verbose': False,  # 设置为 False 减少输出噪音
            'ignoreerrors': True,

            # -- 格式选择 --
            # 'format': 'bestaudio/best',  #最佳音质音频
            'format': 'ba[ext=mp3][abr=320]/ba[ext=mp3][abr>=256]/ba[ext=mp3][abr>=192]/ba[ext=mp3]/b[ext=mp3]',

            # -- 文件系统选项 --
            'outtmpl': output_template,
            'cookiefile': COOKIE_FILE,

            # -- 字幕 (歌词) 选项 --
            'writesubtitles': True,
            'writeautomaticsub': False,
            'subtitlesformat': 'lrc',
            'skip_download': False,

            # -- 元数据与封面嵌入选项 --
            'embedmetadata': True,
            'embedthumbnail': True,
            
            # -- 后处理选项 --
            'postprocessors': [
                # 添加元数据
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                },
                # 嵌入封面
                {
                    'key': 'EmbedThumbnail',
                    'already_have_thumbnail': False,
                },
            ],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([song['url']])
            print(f"[✓] 成功下载: {song['title']}")
            success_count += 1
        except Exception as e:
            error_msg = str(e)
            print(f"[!] 下载失败: {song['title']} - 错误: {error_msg}")
            fail_count += 1
            
            # 记录失败信息
            error_record = song['original_data'].copy()
            error_record['报错内容'] = error_msg
            error_records.append(error_record)
        
        # 每次下载后立即清理文件名
        clean_file_names(OUTPUT_DIR)
        
        # 随机延迟 1-3 秒
        if i < len(songs):  # 最后一首不需要延迟
            delay = random.uniform(1, 3)
            print(f"[*] 等待 {delay:.1f} 秒后继续...")
            time.sleep(delay)
    
    # 最终清理一次确保所有文件都被正确处理
    clean_file_names(OUTPUT_DIR)
    
    # 导出错误记录到CSV文件
    if error_records:
        export_errors_to_csv(error_records, original_fieldnames)
    
    print("\n" + "="*50)
    print(f"[*] 下载完成!")
    print(f"[*] 成功: {success_count} 首, 失败: {fail_count} 首")
    if fail_count > 0:
        print(f"[*] 失败记录已导出到: {ERROR_CSV_FILE}")
    print(f"[*] 文件已保存至: {os.path.abspath(OUTPUT_DIR)}")
    print("="*50)


def main() -> None:
    """
    主函数 - 从 CSV 文件读取歌曲信息并逐个下载
    """
    # 检查必要文件
    check_files()
    
    # 读取 CSV 文件
    songs, original_fieldnames = read_csv_file()
    
    if not songs:
        print("[!] 没有找到可下载的歌曲")
        return
    
    # 下载歌曲
    download_songs(songs, original_fieldnames)


if __name__ == "__main__":
    main()