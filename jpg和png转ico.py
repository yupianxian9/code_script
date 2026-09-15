from PIL import Image
import os
from pathlib import Path

def convert_to_ico(
    input_path: str,
    output_path: str = None,
    sizes: list = [(32, 32), (64, 64), (128, 128), (256, 256), (256, 256), (512, 512)],
    quality: int = 95
) -> None:
    """
    将图片转换为包含多尺寸的ICO图标文件（支持PNG/JPG输入）
    :param input_path: 输入文件路径（支持.png/.jpg/.jpeg）
    :param output_path: 输出ICO文件路径（默认同目录）
    :param sizes: 生成的图标尺寸列表
    :param quality: 图像质量（1-100）
    """
    try:
        # 自动生成输出路径[5](@ref)
        if not output_path:
            dir_name = os.path.dirname(input_path)
            base_name = Path(input_path).stem
            output_path = os.path.join(dir_name, f"{base_name}.ico")

        with Image.open(input_path) as img:
            # 统一转换为RGBA模式[6,7](@ref)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
                
            # 居中裁剪非正方形图像[4](@ref)
            if img.width != img.height:
                crop_size = min(img.width, img.height)
                left = (img.width - crop_size) // 2
                top = (img.height - crop_size) // 2
                img = img.crop((left, top, left + crop_size, top + crop_size))

            # 生成多尺寸ICO[1](@ref)
            img.save(
                output_path,
                format="ICO",
                sizes=sizes,
                quality=quality
            )
            print(f"成功生成：{output_path}")

    except Exception as e:
        print(f"转换失败 [{input_path}]: {str(e)}")

def batch_convert_to_ico(
    input_dir: str,
    output_dir: str = None,
    supported_ext: list = ['.png', '.jpg', '.jpeg'],
    **kwargs
) -> None:
    """
    批量转换目录中的图片为ICO
    :param input_dir: 输入目录路径
    :param output_dir: 输出目录路径（默认同输入目录）
    :param supported_ext: 支持转换的文件扩展名
    :param kwargs: 传递给convert_to_ico的参数
    """
    input_path = Path(input_dir)
    if not output_dir:
        output_dir = input_dir
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    converted = 0
    for file_path in input_path.glob('*'):
        if file_path.suffix.lower() in supported_ext:
            output_path = Path(output_dir) / f"{file_path.stem}.ico"
            convert_to_ico(
                input_path=str(file_path),
                output_path=str(output_path),
                **kwargs
            )
            converted += 1

    print(f"\n批量转换完成！共处理 {converted} 个文件")

if __name__ == "__main__":
    # 测试参数
    test_config = {
        "input_dir": "./images",  # 输入目录路径
        "output_dir": "./output_icons",  # 输出目录
        "sizes": [(64,64), (128,128), (256,256), (512, 512)],  # 自定义尺寸
        "quality": 100,  # 最高质量
        "supported_ext": ['.png', '.jpg']  # 支持格式
    }
    
    # 执行批量转换
    batch_convert_to_ico(**test_config)
