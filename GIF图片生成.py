from PIL import Image, ImageSequence
import os

# 图片文件夹路径
folder_path = r"D:\download\gif"
images = [Image.open(os.path.join(folder_path, img)) for img in sorted(os.listdir(folder_path))]

# 保存为 GIF
images[0].save("output.gif", save_all=True, append_images=images[1:], duration=300, loop=0)
