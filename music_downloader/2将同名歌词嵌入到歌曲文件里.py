import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, USLT
from mutagen.flac import FLAC

# ====================== 用户可配置区域 ======================
# 在这里设置要处理的文件夹路径
FOLDER_PATH = r"./QQ_Music_Downloads"  # Windows路径示例
# FOLDER_PATH = "/home/user/Music"  # Linux/macOS路径示例
# ===========================================================

def read_lrc_file(lrc_path):
    """读取LRC歌词文件内容"""
    try:
        with open(lrc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"警告: 歌词文件未找到: {lrc_path}")
        return None
    except Exception as e:
        print(f"读取歌词文件失败 {lrc_path}: {str(e)}")
        return None

def embed_lyrics_to_mp3(mp3_path, lyrics_text):
    """将歌词嵌入MP3文件的ID3标签"""
    try:
        # 加载音频文件并确保ID3标签存在
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        
        # 清除可能存在的旧歌词标签
        audio.tags.delall("USLT::eng")
        
        # 创建USLT帧（未同步歌词，但可存储LRC内容）
        uslt_frame = USLT(encoding=3, lang='eng', desc='Lyrics', text=lyrics_text)
        audio.tags.add(uslt_frame)
        
        # 保存更改
        audio.save()
        print(f"成功嵌入歌词到MP3: {os.path.basename(mp3_path)}")
        return True
    except Exception as e:
        print(f"处理MP3文件失败 {os.path.basename(mp3_path)}: {str(e)}")
        return False

def embed_lyrics_to_flac(flac_path, lyrics_text):
    """将歌词嵌入FLAC文件的Vorbis注释"""
    try:
        audio = FLAC(flac_path)
        
        # 使用LYRICS字段存储歌词（Vorbis注释标准）
        audio["LYRICS"] = lyrics_text
        
        # 保存更改
        audio.save()
        print(f"成功嵌入歌词到FLAC: {os.path.basename(flac_path)}")
        return True
    except Exception as e:
        print(f"处理FLAC文件失败 {os.path.basename(flac_path)}: {str(e)}")
        return False

def process_folder(folder_path):
    """处理指定文件夹中的所有音频文件"""
    supported_audio_ext = ('.mp3', '.flac')
    
    # 获取文件夹中的所有文件
    all_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # 筛选出支持的音频文件
    audio_files = [f for f in all_files if f.lower().endswith(supported_audio_ext)]
    
    if not audio_files:
        print(f"在文件夹 '{folder_path}' 中未找到支持的音频文件（MP3或FLAC）")
        return

    processed_count = 0
    skipped_count = 0
    
    for audio_file in audio_files:
        # 获取不带扩展名的文件名
        base_name = os.path.splitext(audio_file)[0]
        lrc_file = base_name + '.lrc'
        lrc_path = os.path.join(folder_path, lrc_file)
        audio_path = os.path.join(folder_path, audio_file)
        
        # 检查同名LRC文件是否存在
        if not os.path.exists(lrc_path):
            print(f"未找到匹配的歌词文件: {lrc_file} (对应音频: {audio_file})")
            skipped_count += 1
            continue
        
        # 读取歌词内容
        lyrics_text = read_lrc_file(lrc_path)
        if lyrics_text is None:
            skipped_count += 1
            continue
        
        # 根据音频格式调用对应的处理函数
        if audio_file.lower().endswith('.mp3'):
            success = embed_lyrics_to_mp3(audio_path, lyrics_text)
        elif audio_file.lower().endswith('.flac'):
            success = embed_lyrics_to_flac(audio_path, lyrics_text)
        else:
            success = False
        
        if success:
            processed_count += 1
        else:
            skipped_count += 1

    print(f"\n处理完成！")
    print(f"文件夹: {folder_path}")
    print(f"成功嵌入: {processed_count} 个文件")
    print(f"跳过处理: {skipped_count} 个文件")

def main():
    """主函数：处理指定的文件夹"""
    folder_path = FOLDER_PATH
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误: 指定的文件夹不存在: {folder_path}")
        return
    
    if not os.path.isdir(folder_path):
        print(f"错误: 指定的路径不是文件夹: {folder_path}")
        return
    
    print(f"开始处理文件夹: {folder_path}")
    process_folder(folder_path)

if __name__ == "__main__":
    main()