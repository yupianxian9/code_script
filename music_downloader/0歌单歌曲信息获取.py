import os
import sys
import csv
from typing import Dict, Any, List

# 确保 yt-dlp 已安装
try:
    import yt_dlp
except ImportError:
    print("错误：yt-dlp 库未安装。")
    print("请使用 'pip install yt-dlp' 命令进行安装。")
    sys.exit(1)


# ========================== 参数配置区 ==========================

# 1. 歌单链接: 请将这里的链接替换为您想解析的 QQ 音乐歌单链接
PLAYLIST_URL: str = "https://y.qq.com/n/ryqq/playlist/7708953611"

# 2. Cookie 文件路径: QQ 音乐需要登录才能获取完整信息，请提供 Netscape 格式的 Cookie 文件
COOKIE_FILE: str = "y.qq.com_cookies.txt"

# 3. 输出 CSV 文件名
OUTPUT_CSV: str = "qqmusic_playlist.csv"

# ===============================================================


def check_cookie_file() -> None:
    """检查 Cookie 文件是否存在，若不存在则创建并提示"""
    if not os.path.exists(COOKIE_FILE):
        print(f"警告：Cookie 文件 '{COOKIE_FILE}' 不存在。")
        print("已为您创建一个空白文件，请从浏览器导出 y.qq.com 的 Cookie 并粘贴到文件中。")
        print("否则可能无法获取完整歌单信息。")
        with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# http://www.netscape.com/newsref/std/cookie_spec.html\n")
            f.write("# This is a generated file! Do not edit.\n")


def extract_playlist_info() -> List[Dict[str, Any]]:
    """
    使用 yt-dlp 提取 QQ 音乐歌单信息
    
    Returns:
        包含歌曲信息的字典列表
    """
    # yt-dlp 配置 - 仅提取信息，不下载
    ydl_opts: Dict[str, Any] = {
        'verbose': False,
        'ignoreerrors': True,
        'cookiefile': COOKIE_FILE,
        'extract_flat': False,  # 确保提取详细信息
        'skip_download': True,  # 跳过下载
    }
    
    playlist_info = []
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 提取歌单信息
            info = ydl.extract_info(PLAYLIST_URL, download=False)
            
            if 'entries' in info:
                # 这是一个播放列表
                print(f"[*] 发现 {len(info['entries'])} 首歌曲")
                
                for entry in info['entries']:
                    if entry is None:
                        continue
                        
                    # 格式化时长
                    duration = entry.get('duration', 0)
                    if duration:
                        minutes = duration // 60
                        seconds = duration % 60
                        duration_formatted = f"{minutes}:{seconds:02d}"
                    else:
                        duration_formatted = '未知'
                    
                    # 提取所需字段的歌曲信息
                    song_info = {
                        'title': entry.get('title', '未知标题'),
                        'album': entry.get('album', '未知专辑'),
                        'duration': duration_formatted,
                        'url': entry.get('webpage_url', ''),
                    }
                    
                    playlist_info.append(song_info)
                    
                    # 显示进度
                    print(f"[*] 已解析: {song_info['title']} - {song_info['album']}")
            
            else:
                # 单曲
                print("[*] 发现 1 首歌曲")
                
                # 格式化时长
                duration = info.get('duration', 0)
                if duration:
                    minutes = duration // 60
                    seconds = duration % 60
                    duration_formatted = f"{minutes}:{seconds:02d}"
                else:
                    duration_formatted = '未知'
                
                song_info = {
                    'title': info.get('title', '未知标题'),
                    'album': info.get('album', '未知专辑'),
                    'duration': duration_formatted,
                    'url': info.get('webpage_url', ''),
                }
                
                playlist_info.append(song_info)
                print(f"[*] 已解析: {song_info['title']} - {song_info['album']}")
                
    except Exception as e:
        print(f"[!] 解析歌单时出错: {e}")
    
    return playlist_info


def save_to_csv(playlist_info: List[Dict[str, Any]]) -> None:
    """
    将歌单信息保存为 CSV 文件
    
    Args:
        playlist_info: 歌曲信息列表
    """
    if not playlist_info:
        print("[!] 没有找到可保存的歌曲信息")
        return
    
    # CSV 文件字段 - 只保留所需字段
    fieldnames = ['序号', '歌名', '专辑', '时长', '链接']
    
    try:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, song in enumerate(playlist_info, 1):
                writer.writerow({
                    '序号': i,
                    '歌名': song['title'],
                    '专辑': song['album'],
                    '时长': song['duration'],
                    '链接': song['url']
                })
        
        print(f"[*] 歌单信息已保存至: {os.path.abspath(OUTPUT_CSV)}")
        print(f"[*] 共保存 {len(playlist_info)} 首歌曲信息")
        
    except Exception as e:
        print(f"[!] 保存 CSV 文件时出错: {e}")


def main() -> None:
    """
    主函数 - 解析 QQ 音乐歌单并生成 CSV 文件
    """
    print("=" * 60)
    print("QQ 音乐歌单解析器")
    print("=" * 60)
    
    # 检查 Cookie 文件
    check_cookie_file()
    
    # 解析歌单
    print(f"[*] 开始解析歌单: {PLAYLIST_URL}")
    playlist_info = extract_playlist_info()
    
    if not playlist_info:
        print("[!] 未能解析到任何歌曲信息，请检查:")
        print("    1. 歌单链接是否正确")
        print("    2. Cookie 文件是否有效")
        print("    3. 网络连接是否正常")
        return
    
    # 保存为 CSV
    save_to_csv(playlist_info)
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print("[*] 解析完成!")
    print(f"[*] 输出文件: {OUTPUT_CSV}")
    print(f"[*] 歌曲总数: {len(playlist_info)}")
    print("=" * 60)


if __name__ == "__main__":
    main()