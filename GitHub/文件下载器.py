#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量下载器 - 使用 urllib 下载多个文件（支持加速前缀、断点续传、代理）
所有配置集中在脚本开头的“参数配置区域”中修改
"""

import os
import sys
import time
import urllib.request
import urllib.error

# ======================== 参数配置区域（请根据需要修改） ========================

# 1. 原始下载链接列表（必填）
URLS = [
    "https://github.com/Spring691/dawn/releases/download/v1.1.1/Futamata.Ren.ai.part1.rar",
    "https://github.com/Spring691/dawn/releases/download/v1.1.1/Futamata.Ren.ai.part2.rar",
]

# 2. 加速链接前缀（例如 https://mirror.ghproxy.com/）
ACCELERATE_PREFIX = "https://ghf.xn--eqrr82bzpe.top/"

# 3. 是否启用加速
ENABLE_ACCELERATE = True

# 4. 文件保存目录
OUTPUT_DIR = r"D:\download"

# 5. 下载失败时的重试次数
MAX_RETRIES = 3

# 6. 代理设置（不需要代理则留空字符串）
PROXY = ""   # 例如 "http://127.0.0.1:7890"

# 7. 下载时的缓冲区大小（字节，建议 1MB = 1048576）
BUFFER_SIZE = 16777216


# 8. 进度更新间隔（秒）
PROGRESS_INTERVAL = 0.5

# ======================== 以下为脚本逻辑，无需修改 ========================

def get_download_url(original_url):
    """根据配置返回实际下载 URL"""
    if ENABLE_ACCELERATE and ACCELERATE_PREFIX:
        if original_url.startswith(ACCELERATE_PREFIX):
            return original_url
        else:
            return ACCELERATE_PREFIX + original_url
    return original_url

def get_filename_from_url(url):
    """从 URL 中提取文件名"""
    return url.split('/')[-1] or "unknown_file"

def create_opener(proxy=None):
    """创建带有代理的 opener"""
    handlers = []
    if proxy:
        proxy_handler = urllib.request.ProxyHandler({
            'http': proxy,
            'https': proxy,
        })
        handlers.append(proxy_handler)
    return urllib.request.build_opener(*handlers)

def format_size(size_bytes):
    """将字节数格式化为人类可读的字符串"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.2f} GB"

def format_speed(speed_bps):
    """格式化下载速度"""
    if speed_bps < 1024:
        return f"{speed_bps:.0f} B/s"
    elif speed_bps < 1024**2:
        return f"{speed_bps/1024:.1f} KB/s"
    else:
        return f"{speed_bps/1024**2:.1f} MB/s"

def format_time(seconds):
    """格式化剩余时间"""
    if seconds < 0:
        return "???"
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def download_file(original_url):
    """使用 urllib 下载单个文件，支持断点续传，显示自定义进度条"""
    download_url = get_download_url(original_url)
    filename = get_filename_from_url(original_url)
    output_path = os.path.join(OUTPUT_DIR, filename)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 检查本地是否已有部分下载的文件
    local_size = 0
    if os.path.exists(output_path):
        local_size = os.path.getsize(output_path)

    # 创建 opener（带代理）
    opener = create_opener(PROXY if PROXY else None)

    # 准备请求头（支持断点续传）
    headers = {}
    if local_size > 0:
        headers['Range'] = f'bytes={local_size}-'

    req = urllib.request.Request(download_url, headers=headers)

    try:
        # 发送请求
        with opener.open(req) as response:
            # 获取文件总大小（优先从 Content-Range 获取，否则从 Content-Length）
            total_size = None
            content_range = response.headers.get('Content-Range')
            if content_range:
                # Content-Range: bytes 1196032-1999999/2000000
                total_size = int(content_range.split('/')[-1])
            else:
                total_size = int(response.headers.get('Content-Length', 0))
                # 如果没有 Content-Length，可能是分块编码，无法显示总大小
                if total_size == 0:
                    total_size = None

            # 断点续传时，总大小可能大于本地已有的部分
            if total_size is not None and local_size > total_size:
                # 本地文件比服务器还大？删除重新下载
                os.remove(output_path)
                local_size = 0
                total_size = None
                # 重新发送请求（不带 Range）
                req = urllib.request.Request(download_url)
                with opener.open(req) as response2:
                    total_size = int(response2.headers.get('Content-Length', 0)) or None
                    # 重新打开写入模式
                    with open(output_path, 'wb') as f:
                        downloaded = 0
                        last_update = time.time()
                        last_dl = 0
                        start_time = time.time()
                        while True:
                            chunk = response2.read(BUFFER_SIZE)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            # 进度更新
                            now = time.time()
                            if now - last_update >= PROGRESS_INTERVAL:
                                elapsed = now - start_time
                                speed = (downloaded - last_dl) / (now - last_update) if (now - last_update) > 0 else 0
                                print_progress(downloaded, total_size, speed, elapsed)
                                last_dl = downloaded
                                last_update = now
                        # 最终进度
                        print_progress(downloaded, total_size, 0, time.time() - start_time, final=True)
                return True

            # 打开文件（追加模式）
            mode = 'ab' if local_size > 0 else 'wb'
            with open(output_path, mode) as f:
                downloaded = local_size
                last_update = time.time()
                last_dl = local_size
                start_time = time.time()

                while True:
                    chunk = response.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    if now - last_update >= PROGRESS_INTERVAL:
                        elapsed = now - start_time
                        speed = (downloaded - last_dl) / (now - last_update) if (now - last_update) > 0 else 0
                        print_progress(downloaded, total_size, speed, elapsed)
                        last_dl = downloaded
                        last_update = now

                # 下载完成，打印最终进度
                print_progress(downloaded, total_size, 0, time.time() - start_time, final=True)
        return True

    except urllib.error.HTTPError as e:
        # 416 表示服务器不支持断点续传，尝试重新下载（不带 Range）
        if e.code == 416 and local_size > 0:
            print(f"\n⚠️ 服务器不支持断点续传，将重新下载 {filename}")
            os.remove(output_path)
            return download_file(original_url)   # 递归调用，重新下载
        print(f"\n❌ HTTP 错误 {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"\n❌ 下载失败: {str(e)}")
        return False

def print_progress(downloaded, total, speed, elapsed, final=False):
    """输出进度条信息（单行刷新）"""
    if total and total > 0:
        percent = downloaded / total * 100
        bar_len = 40
        filled = int(bar_len * downloaded / total)
        bar = '█' * filled + '░' * (bar_len - filled)
        # 已下载大小 / 总大小
        size_str = f"{format_size(downloaded)} / {format_size(total)}"
        speed_str = format_speed(speed) if speed > 0 else "0 B/s"
        eta = (total - downloaded) / speed if speed > 0 else 0
        eta_str = format_time(eta) if not final else "0s"
        # 输出
        sys.stdout.write(f"\r{bar} {percent:.1f}% | {size_str} | {speed_str} | ETA {eta_str}")
    else:
        # 服务器未返回总大小时，只显示已下载和速度
        size_str = format_size(downloaded)
        speed_str = format_speed(speed) if speed > 0 else "???"
        sys.stdout.write(f"\r下载中: {size_str} @ {speed_str}")

    if final:
        sys.stdout.write("\n")
    sys.stdout.flush()

def main():
    if not URLS:
        print("错误：URLS 列表为空，请在配置区域中填写至少一个链接。")
        sys.exit(1)

    print("=" * 60)
    print("批量下载器启动 (urllib 版本)")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"加速前缀: {ACCELERATE_PREFIX if ENABLE_ACCELERATE else '未启用'}")
    print(f"重试次数: {MAX_RETRIES}")
    print(f"代理: {PROXY if PROXY else '无'}")
    print("=" * 60)

    success_count = 0
    for idx, url in enumerate(URLS, 1):
        print(f"\n--- 进度: [{idx}/{len(URLS)}] ---")
        # 带重试逻辑
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"尝试第 {attempt} 次...")
            if download_file(url):
                success_count += 1
                break
            else:
                if attempt < MAX_RETRIES:
                    print(f"将在 2 秒后重试...")
                    time.sleep(2)
                else:
                    print(f"文件 {get_filename_from_url(url)} 下载失败，已达到最大重试次数。")

    print("\n" + "=" * 60)
    print(f"全部完成！成功: {success_count} / 总数: {len(URLS)}")
    if success_count < len(URLS):
        print("部分文件下载失败，请检查网络或链接有效性。")
    else:
        print("所有文件均已成功下载。")
    print("=" * 60)

if __name__ == "__main__":
    main()