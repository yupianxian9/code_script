import os
import sys
from typing import Dict, Any

# 确保 yt-dlp 已安装
try:
    import yt_dlp
except ImportError:
    print("错误：yt-dlp 库未安装。")
    print("请使用 'pip install yt-dlp' 命令进行安装。")
    sys.exit(1)


# ========================== 参数配置区 ==========================

# 1. 歌单链接: 请将这里的链接替换为您想下载的 QQ 音乐歌单链接
PLAYLIST_URL: str = "https://y.qq.com/n/ryqq/playlist/7708953611"

# 2. Cookie 文件路径: QQ 音乐需要登录才能获取高品质音源，请提供 Netscape 格式的 Cookie 文件
#    脚本会检查此文件是否存在，如果不存在，会创建一个空白文件并提示您填入 Cookie
COOKIE_FILE: str = "y.qq.com_cookies.txt"

# 3. 输出目录: 所有下载的歌曲和歌词文件都将保存在此目录下
OUTPUT_DIR: str = "QQ_Music_Downloads"

# ===============================================================


def download_playlist() -> None:
    """
    使用 yt-dlp 下载并处理 QQ 音乐歌单。
    """
    # --- 准备工作 ---
    # 检查 Cookie 文件是否存在，若不存在则创建并提示
    if not os.path.exists(COOKIE_FILE):
        print(f"警告：Cookie 文件 '{COOKIE_FILE}' 不存在。")
        print("已为您创建一个空白文件，请从浏览器导出 y.qq.com 的 Cookie 并粘贴到文件中。")
        print("否则可能无法下载高音质歌曲或VIP歌曲。")
        with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# http://www.netscape.com/newsref/std/cookie_spec.html\n")
            f.write("# This is a generated file! Do not edit.\n")

    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # --- yt-dlp 选项配置 (修正版) ---
    # 使用高级便捷选项替代 'postprocessors' 列表，更稳定且易于理解
    ydl_opts: Dict[str, Any] = {
        # -- 详细输出与错误处理 --
        'verbose': True,           # 打印详细的调试信息
        'ignoreerrors': True,      # 忽略个别歌曲的下载错误

        # -- 格式选择 --
        'format': 'bestaudio/best', # 选择最佳音质的音频

        # -- 下载选项 --
        'sleep_interval': 3,       # 最小随机延迟1秒
        'max_sleep_interval': 9,   # 最大随机延迟3秒

        # -- 文件系统选项 --
        'outtmpl': os.path.join(OUTPUT_DIR, '%(playlist)s/%(title)s.%(ext)s'),
        'cookiefile': COOKIE_FILE,

        # -- 字幕 (歌词) 选项 --
        'writesubtitles': True,      # 对应 --write-subs，下载歌词
        'convertsubtitles': 'lrc',   # 对应 --convert-subs lrc，将歌词转换为lrc格式

        # -- 音频提取与转换选项 --
        'extract_audio': True,       # 对应 -x 或 --extract-audio，提取音频
        'audio_format': 'mp3',       # 对应 --audio-format mp3，设置输出音频格式
        'audio_quality': '320K',     # 对应 --audio-quality 320K，设置音频比特率为320kbps

        # -- 元数据与封面嵌入选项 --
        'embedmetadata': True,       # 对应 --embed-metadata，嵌入元数据
        'embedthumbnail': True,      # 对应 --embed-thumbnail，嵌入封面
    }

    print("="*50)
    print(f"[*] 开始下载歌单: {PLAYLIST_URL}")
    print(f"[*] 音频质量: 320kbps MP3")
    print(f"[*] 歌词格式: LRC")
    print(f"[*] 输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print("="*50)

    # --- 执行下载 ---
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([PLAYLIST_URL])
        print("\n" + "="*50)
        print("[*] 歌单下载处理完成！")
        print(f"[*] 文件已保存至: {os.path.abspath(OUTPUT_DIR)}")
        print("="*50)
    except yt_dlp.utils.DownloadError as e:
        print(f"\n下载过程中发生严重错误: {e}")
    except Exception as e:
        print(f"\n发生未知错误: {e}")


if __name__ == "__main__":
    download_playlist()