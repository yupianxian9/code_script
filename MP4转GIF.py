from moviepy import VideoFileClip

def mp4_to_gif(input_path, output_path, start_time=0, end_time=None, fps=10, resize=0.5):
    """
    将 MP4 视频片段转换为 GIF
    参数：
    - input_path: 输入视频文件路径
    - output_path: 输出 GIF 路径
    - start_time: 截取开始时间（秒）
    - end_time: 截取结束时间（秒）
    - fps: 输出 GIF 帧率
    - resize: 缩放比例（0.5 表示宽度高度各减半）
    """
    # 加载视频文件
    clip = VideoFileClip(input_path)
    
    # 截取指定时间段
    if end_time is not None:
        clip = clip.subclipped(start_time, end_time)  # 确保方法名正确
    else:
        clip = clip.subclipped(start_time)
    
    # 调整尺寸和帧率
    clip = clip.resized(resize).with_fps(fps)
    
    # 生成 GIF
    clip.write_gif(output_path)

# 使用示例
mp4_to_gif(
    input_path=r"D:\download\input.mp4",
    output_path="output.gif",
    # start_time=2,    # 从第2秒开始
    # end_time=6,      # 到第6秒结束
    fps=15,          # 设置帧率
    resize=1      # 调整为原尺寸的100%
)

