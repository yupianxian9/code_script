import os
import re
from pathlib import Path
from tinytag import TinyTag

def sanitize_filename(text):
    """清理非法字符并格式化字符串[3,10](@ref)"""
    return re.sub(r'[\\/*?:"<>|]', "_", str(text).strip())

def get_audio_metadata(file_path):
    """提取音频元数据（支持MP3/FLAC）[3,6,10](@ref)"""
    try:
        tag = TinyTag.get(file_path)
        artist = tag.artist or "UnknownArtist"
        title = tag.title or Path(file_path).stem
        return sanitize_filename(artist), sanitize_filename(title)
    except Exception as e:
        print(f"元数据读取失败：{file_path} - {str(e)}")
        return None, None

def batch_rename(directory, pattern="artist-title"):
    """批量重命名主函数[1,3](@ref)"""
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.lower().endswith(('.mp3', '.flac')):
                continue
            
            file_path = os.path.join(root, file)
            artist, title = get_audio_metadata(file_path)
            
            if artist and title:
                new_name = f"{artist} - {title}{os.path.splitext(file)[1]}"
                new_path = os.path.join(root, new_name)
                
                if not os.path.exists(new_path):
                    os.rename(file_path, new_path)
                    print(f"已重命名：{file} -> {new_name}")
                else:
                    print(f"文件已存在，跳过：{new_name}")
            else:
                print(f"元数据缺失：{file}")

if __name__ == "__main__":
    target_dir = r"D:\music"  #目标路径
    batch_rename(target_dir)