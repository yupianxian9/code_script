# -*- coding: utf-8 -*-
"""
图片转PDF工具（漫画专用）
功能：将指定文件夹中的所有图片按顺序转换为单页PDF，保持图片质量，无页边距设计
依赖库：Pillow (pip install pillow)
"""

from PIL import Image
import os
from pathlib import Path
import re  # 新增：用于提取文件名中的数字


def natural_sort_key(s):
    """
    自然排序键函数：提取字符串中的数字部分转为整数，实现自然数序列排序
    例如："10.jpg" 会排在 "2.jpg" 后面，而不是前面
    """
    # 提取文件名中的所有数字部分，组成元组用于排序
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def calculate_a4_target_width(config: dict) -> int:
    """
    计算目标宽度（A4宽度的指定比例）
    公式：像素宽度 = (A4宽度mm / 25.4mm per inch) * DPI * 比例系数
    :param config: 配置字典
    :return: 目标宽度（像素）
    """
    a4_width_mm = config["a4_params"]["width_mm"]
    dpi = config["a4_params"]["dpi"]
    ratio = config["a4_width_ratio"]
    
    # 转换mm到英寸，再计算像素数，最后取整
    target_width = int((a4_width_mm / 25.4) * dpi * ratio)
    return target_width


def get_sorted_image_paths(input_folder: str, supported_formats: tuple) -> list:
    """
    获取文件夹中所有支持的图片路径，并按文件名自然数序列排序（保证PDF页面顺序）
    :param input_folder: 输入文件夹路径
    :param supported_formats: 支持的图片格式元组
    :return: 排序后的图片路径列表
    """
    image_paths = []
    
    # 遍历文件夹中的所有文件
    for filename in os.listdir(input_folder):
        # 检查文件扩展名是否在支持的格式中（忽略大小写）
        if filename.lower().endswith(supported_formats):
            # 构建完整路径
            file_path = os.path.join(input_folder, filename)
            # 验证是文件而不是子文件夹
            if os.path.isfile(file_path):
                image_paths.append(file_path)
    
    # 按文件名进行自然数序列排序（核心修改）
    image_paths.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
    return image_paths


def resize_image(image: Image.Image, target_width: int) -> Image.Image:
    """
    按目标宽度等比例缩放图片，保持宽高比
    :param image: 原始PIL图片对象
    :param target_width: 目标宽度（像素）
    :return: 缩放后的图片对象
    """
    # 获取原始图片尺寸
    original_width, original_height = image.size
    
    # 计算缩放比例（目标宽度 / 原始宽度）
    scale_ratio = target_width / original_width
    
    # 计算目标高度（等比例缩放）
    target_height = int(original_height * scale_ratio)
    
    # 使用高质量缩放算法（LANCZOS适用于缩小和放大，能保持图片细节）
    resized_image = image.resize(
        (target_width, target_height),
        resample=Image.Resampling.LANCZOS
    )
    
    return resized_image


def process_single_image(image_path: str, target_width: int, config: dict) -> Image.Image:
    """
    处理单张图片：打开、转换格式、缩放
    :param image_path: 图片路径
    :param target_width: 目标宽度
    :param config: 配置字典
    :return: 处理后的图片对象
    """
    try:
        # 打开图片（支持所有Pillow兼容格式）
        with Image.open(image_path) as img:
            # 确保图片已加载
            img.load()
            
            # 处理透明图片（PNG等）：将透明背景转为白色（漫画常用背景）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景的新图片
                if img.mode == 'P':
                    # 对于调色板模式，先转换为RGBA
                    img = img.convert('RGBA')
                
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    # 将透明图片叠加到白色背景上
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                img = background
            elif img.mode not in ('RGB', 'L'):
                # 转换为RGB模式
                img = img.convert('RGB')
            
            # 等比例缩放到目标宽度
            resized_img = resize_image(img, target_width)
            return resized_img
            
    except Exception as e:
        error_msg = f"处理图片失败：{os.path.basename(image_path)} - {str(e)}"
        if config.get("skip_problematic_images", True):
            print(f"⚠️  {error_msg}，跳过此图片")
            return None
        else:
            raise RuntimeError(error_msg) from e


def convert_single_folder_to_pdf(input_folder: str, output_pdf: str, config: dict) -> bool:
    """
    将单个文件夹中的图片转换为PDF文件
    :param input_folder: 输入文件夹路径
    :param output_pdf: 输出PDF文件路径
    :param config: 配置字典
    :return: 转换是否成功
    """
    try:
        # 1. 验证输入文件夹是否存在
        if not os.path.exists(input_folder):
            print(f"❌ 输入文件夹不存在：{input_folder}")
            return False
        
        # 2. 获取目标宽度
        target_width = calculate_a4_target_width(config)
        print(f"目标图片宽度：{target_width} 像素（A4宽度的{config['a4_width_ratio']*100}%）")
        
        # 3. 获取排序后的图片路径列表
        image_paths = get_sorted_image_paths(input_folder, config["supported_formats"])
        if not image_paths:
            print(f"❌ 文件夹 {input_folder} 中未找到支持的图片文件")
            return False
        
        print(f"找到 {len(image_paths)} 张图片，开始转换...")
        
        # 4. 处理每张图片
        pdf_pages = []
        skipped_images = []
        
        for idx, image_path in enumerate(image_paths, 1):
            print(f"  正在处理第 {idx}/{len(image_paths)} 张：{os.path.basename(image_path)}")
            
            try:
                processed_img = process_single_image(image_path, target_width, config)
                if processed_img is not None:
                    pdf_pages.append(processed_img)
                else:
                    skipped_images.append(os.path.basename(image_path))
            except Exception as e:
                print(f"❌ 处理图片失败：{os.path.basename(image_path)} - {str(e)}")
                if not config.get("skip_problematic_images", True):
                    raise
        
        # 5. 检查是否有可用的图片
        if not pdf_pages:
            print("❌ 没有可成功处理的图片，无法生成PDF")
            if skipped_images:
                print(f"跳过的图片：{skipped_images}")
            return False
        
        # 6. 生成PDF文件（无页边距，页面间距最小）
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
        
        # 第一张图片作为PDF的起始页，后续图片追加
        pdf_pages[0].save(
            output_pdf,
            save_all=True,
            append_images=pdf_pages[1:],
            quality=config["pdf_quality"],  # 设置PDF图片质量
            optimize=True,  # 优化PDF文件大小
            dpi=(config["a4_params"]["dpi"], config["a4_params"]["dpi"])  # 保持DPI一致性
        )
        
        print(f"✅ PDF生成成功！保存路径：{output_pdf}")
        if skipped_images:
            print(f"⚠️  跳过了 {len(skipped_images)} 张无法处理的图片：{skipped_images}")
        return True
        
    except Exception as e:
        print(f"❌ 生成PDF时发生错误：{str(e)}")
        return False


def convert_images_to_pdf(config: dict) -> None:
    """
    核心功能：将图片文件夹转换为PDF文件（支持批量模式）
    :param config: 配置字典
    """
    if config.get("batch_mode", False):
        # 批量转换模式：处理输入文件夹下的所有子文件夹
        print("=" * 60)
        print("📁 批量转换模式启动")
        print("=" * 60)
        
        input_folder = config["input_folder"]
        output_folder = config.get("output_folder", "./pdf_output")
        
        # 验证输入文件夹是否存在
        if not os.path.exists(input_folder):
            raise FileNotFoundError(f"输入文件夹不存在：{input_folder}")
        
        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)
        
        # 获取所有子文件夹
        subfolders = []
        for item in os.listdir(input_folder):
            item_path = os.path.join(input_folder, item)
            if os.path.isdir(item_path):
                subfolders.append(item)
        
        if not subfolders:
            print("⚠️  输入文件夹中没有子文件夹，切换到单文件夹模式")
            # 如果没有子文件夹，回退到单文件夹模式
            convert_single_folder_to_pdf(
                input_folder, 
                config["output_pdf"], 
                config
            )
            return
        
        print(f"找到 {len(subfolders)} 个子文件夹，开始批量转换...")
        
        success_count = 0
        for folder_name in subfolders:
            print(f"\n🎯 正在处理文件夹: {folder_name}")
            print("-" * 40)
            
            input_subfolder = os.path.join(input_folder, folder_name)
            # 使用文件夹名称作为PDF文件名
            output_pdf = os.path.join(output_folder, f"{folder_name}.pdf")
            
            if convert_single_folder_to_pdf(input_subfolder, output_pdf, config):
                success_count += 1
        
        print("\n" + "=" * 60)
        print(f"📊 批量转换完成！")
        print(f"总文件夹数: {len(subfolders)} | 成功: {success_count} | 失败: {len(subfolders) - success_count}")
        print("=" * 60)
        
    else:
        # 单文件夹转换模式（保持原有功能）
        print("📄 单文件夹转换模式启动")
        convert_single_folder_to_pdf(
            config["input_folder"], 
            config["output_pdf"], 
            config
        )


if __name__ == "__main__":

    CONFIG = {
    # A4纸张宽度比例（1.0=100%，1.25=125%）
    "a4_width_ratio": 1,
    # 输入图片文件夹路径（可以是包含多个子文件夹的根目录）
    "input_folder": r"./comic_download",
    # 输出PDF文件夹路径（批量转换时使用）
    "output_folder": "./pdf_output",
    # 单个PDF文件输出路径（单文件夹转换时使用）
    "output_pdf": "./output.pdf",
    # PDF图片质量（1-95，越高质量越好，建议90-95，接近原图质量）
    "pdf_quality": 95,
    # A4纸张标准参数（300dpi，常用打印分辨率）
    "a4_params": {
        "width_mm": 210,    # A4宽度（毫米）
        "dpi": 90          # 分辨率（ dots per inch ）：72 - 150之间设置
    },
    # 支持的图片格式（可根据需要扩展）
    "supported_formats": ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff','.webp'),
    # 是否启用批量转换模式（True: 转换所有子文件夹, False: 只转换指定文件夹）
    "batch_mode": True,
    # 是否跳过无法处理的图片（True: 跳过错误图片继续处理, False: 遇到错误停止）
    "skip_problematic_images": True
    }
    # 执行图片转PDF操作
    convert_images_to_pdf(CONFIG)
