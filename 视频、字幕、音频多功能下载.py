import yt_dlp
from typing import Optional, Dict, List, Union
import os


class YTDLPDownloader:
    """
    增强版yt-dlp下载器，支持多种下载模式及独立参数配置
    模式包括：仅视频、仅音频、音视频合并、仅字幕、音视频+字幕
    """
    # 模式常量定义
    MODE_VIDEO_ONLY = 'video_only'
    MODE_AUDIO_ONLY = 'audio_only'
    MODE_BOTH = 'both'
    MODE_SUBTITLES_ONLY = 'subtitles_only'
    MODE_BOTH_WITH_SUBTITLES = 'both_with_subtitles'

    def __init__(self, global_options: Optional[Dict] = None):
        """
        初始化下载器
        
        :param global_options: 全局配置（适用于所有模式的公共参数）
        """
        # 全局默认配置
        self.global_defaults = {
            'quiet': False,
            'no_warnings': False,
            'ignore_errors': True,
            'merge_output_format': 'mp4',
            'outtmpl': './downloads/%(title)s.%(ext)s',
            'nooverwrites': True,
        }
        self.global_options = {**self.global_defaults,** (global_options or {})}
        
        # 各模式独立参数配置区域
        self.mode_configs = {
            # 仅下载视频
            self.MODE_VIDEO_ONLY: {
                'format': 'bestvideo[ext=mp4]+none',  # 仅视频流
                'writesubtitles': False,
                'writeautomaticsub': False,
                'skip_download': False,
            },
            # 仅下载音频
            self.MODE_AUDIO_ONLY: {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'writesubtitles': False,
                'writeautomaticsub': False,
                'skip_download': False,
            },
            # 音视频一起下载
            self.MODE_BOTH: {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'writesubtitles': False,
                'writeautomaticsub': False,
                'skip_download': False,
            },
            # 仅下载字幕
            self.MODE_SUBTITLES_ONLY: {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['all'],
                'skip_download': True,  # 跳过视频/音频下载
                'postprocessors': [{
                    'key': 'FFmpegSubtitlesConvertor',
                    'format': 'srt',
                }],
            },
            # 音视频及字幕一起下载
            self.MODE_BOTH_WITH_SUBTITLES: {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['all'],
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }, {
                    'key': 'FFmpegSubtitlesConvertor',
                    'format': 'srt',
                }],
                'skip_download': False,
            }
        }
        
        self.current_mode = None
        self.downloader = self._create_downloader(self.global_options)

    def _create_downloader(self, options: Dict) -> yt_dlp.YoutubeDL:
        """创建下载器实例"""
        return yt_dlp.YoutubeDL(options)

    def _merge_options(self, mode: str, custom_options: Optional[Dict] = None) -> Dict:
        """合并全局配置、模式配置和自定义配置"""
        if mode not in self.mode_configs:
            raise ValueError(f"不支持的模式: {mode}")
        
        # 合并顺序：全局配置 -> 模式配置 -> 自定义配置（后者覆盖前者）
        merged = {**self.global_options,** self.mode_configs[mode]}
        if custom_options:
            merged.update(custom_options)
        return merged

    def set_mode(self, mode: str, custom_options: Optional[Dict] = None) -> None:
        """
        设置下载模式及自定义参数
        
        :param mode: 下载模式（使用类的MODE_*常量）
        :param custom_options: 该模式下的自定义参数（覆盖默认模式配置）
        """
        self.current_mode = mode
        merged_options = self._merge_options(mode, custom_options)
        self.downloader = self._create_downloader(merged_options)

    def update_global_options(self, new_global: Dict) -> None:
        """更新全局配置（会影响所有模式）"""
        self.global_options.update(new_global)
        # 如果已设置模式，重新应用当前模式
        if self.current_mode:
            self.set_mode(self.current_mode)

    def update_mode_defaults(self, mode: str, new_defaults: Dict) -> None:
        """更新模式的默认配置（影响后续set_mode调用）"""
        if mode in self.mode_configs:
            self.mode_configs[mode].update(new_defaults)

    def set_cookie_file(self, cookie_path: str) -> None:
        """设置Netscape格式Cookie文件"""
        if not os.path.exists(cookie_path):
            raise FileNotFoundError(f"Cookie文件不存在: {cookie_path}")
        self.update_global_options({'cookiefile': cookie_path})

    def get_video_info(self, url: str) -> Dict:
        """获取视频信息（不下载）"""
        with self.downloader:
            return self.downloader.extract_info(url, download=False)

    def download(self, urls: Union[str, List[str]], output_template: Optional[str] = None) -> None:
        """
        执行下载（需先通过set_mode设置模式）
        
        :param urls: 单个URL或URL列表
        :param output_template: 临时输出路径模板（覆盖全局配置）
        """
        if not self.current_mode:
            raise RuntimeError("请先通过set_mode设置下载模式")
        
        url_list = [urls] if isinstance(urls, str) else urls
        if not isinstance(url_list, list):
            raise ValueError("urls必须是字符串或列表")
        
        # 处理临时输出模板
        temp_downloader = self.downloader
        if output_template:
            temp_options = self._merge_options(self.current_mode, {'outtmpl': output_template})
            temp_downloader = yt_dlp.YoutubeDL(temp_options)
        
        with temp_downloader:
            temp_downloader.download(url_list)


# ==================== 集中配置区域 ====================
urls_list = [
"https://www.bilibili.com/video/BV1moySBYEu6/?spm_id_from=333.1007.tianma.1-1-1.click"
]


CONFIG = {
    # Cookie设置
    'cookie_file': 'cookies.txt',
    
    # 下载模式选择
    'mode_choice': "subtitles_only",  # 可选: video_only, audio_only, subtitles_only, both, both_with_subtitles
    
    # 进度回调配置
    'progress_hooks': [lambda d: 
        print(f"进度: {d['_percent_str']}") if d['status'] == 'downloading' else None
    ],
    
    # 各模式参数配置
    'video_only': {
        'format': 'bestvideo[height<=720][ext=mp4]',  # 限制720p以内
        'outtmpl': './videos/%(title)s.%(ext)s',
        'urls': urls_list
    },
    
    'audio_only': {
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',   # mp3格式
            'preferredquality': '0',    # 最高质量
        }],
        'outtmpl': './audios/%(title)s.%(ext)s',
        'urls': urls_list
    },
    
    'subtitles_only': {
        'subtitleslangs': ['zh','ai-zh'],  # 下载不了就使用"all"参数
        'outtmpl': './subtitles/%(title)s.%(ext)s',
        'urls': urls_list
    },
    
    'both': {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]',
        'outtmpl': './both/%(title)s.%(ext)s',
        'urls': urls_list
    },
    
    'both_with_subtitles': {
        'format': 'bestvideo[height<=1080]+bestaudio',  # 1080p以内
        'subtitleslangs': ['zh','zh-CN', 'en', 'ja'],
        'outtmpl': './complete/%(title)s.%(ext)s',
        'urls': urls_list
    }
}

# ==================== 主程序逻辑（保持不变） ====================
if __name__ == "__main__":
    # 初始化下载器
    downloader = YTDLPDownloader({
        'progress_hooks': CONFIG['progress_hooks']
    })

    # 设置Cookie（可选）
    try:
        downloader.set_cookie_file(CONFIG['cookie_file'])
        print("Cookie设置成功")
    except FileNotFoundError as e:
        print(f"Cookie设置警告: {e}")

    # 选择下载模式
    mode_choice = CONFIG['mode_choice']

    # 根据选择的模式执行对应下载逻辑
    try:
        if mode_choice == YTDLPDownloader.MODE_VIDEO_ONLY:
            print("\n=== 开始仅下载视频 ===")
            downloader.set_mode(
                mode=YTDLPDownloader.MODE_VIDEO_ONLY,
                custom_options={
                    'format': CONFIG['video_only']['format'],
                    'outtmpl': CONFIG['video_only']['outtmpl']
                }
            )
            download_urls = CONFIG['video_only']['urls']

        elif mode_choice == YTDLPDownloader.MODE_AUDIO_ONLY:
            print("\n=== 开始仅下载音频 ===")
            downloader.set_mode(
                mode=YTDLPDownloader.MODE_AUDIO_ONLY,
                custom_options={
                    'postprocessors': CONFIG['audio_only']['postprocessors'],
                    'outtmpl': CONFIG['audio_only']['outtmpl']
                }
            )
            download_urls = CONFIG['audio_only']['urls']

        elif mode_choice == YTDLPDownloader.MODE_SUBTITLES_ONLY:
            print("\n=== 开始仅下载字幕 ===")
            downloader.set_mode(
                mode=YTDLPDownloader.MODE_SUBTITLES_ONLY,
                custom_options={
                    'subtitleslangs': CONFIG['subtitles_only']['subtitleslangs'],
                    'outtmpl': CONFIG['subtitles_only']['outtmpl']
                }
            )
            download_urls = CONFIG['subtitles_only']['urls']

        elif mode_choice == YTDLPDownloader.MODE_BOTH:
            print("\n=== 开始下载音视频 ===")
            downloader.set_mode(
                mode=YTDLPDownloader.MODE_BOTH,
                custom_options={
                    'format': CONFIG['both']['format'],
                    'outtmpl': CONFIG['both']['outtmpl']
                }
            )
            download_urls = CONFIG['both']['urls']

        elif mode_choice == YTDLPDownloader.MODE_BOTH_WITH_SUBTITLES:
            print("\n=== 开始下载音视频及字幕 ===")
            downloader.set_mode(
                mode=YTDLPDownloader.MODE_BOTH_WITH_SUBTITLES,
                custom_options={
                    'format': CONFIG['both_with_subtitles']['format'],
                    'subtitleslangs': CONFIG['both_with_subtitles']['subtitleslangs'],
                    'outtmpl': CONFIG['both_with_subtitles']['outtmpl']
                }
            )
            download_urls = CONFIG['both_with_subtitles']['urls']

        else:
            raise ValueError(f"不支持的下载模式: {mode_choice}")

        # 执行下载
        downloader.download(download_urls)
        print(f"\n{mode_choice} 模式下载完成")

    except Exception as e:
        print(f"下载失败: {e}")
