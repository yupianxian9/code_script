import os
import win32com.client
import pythoncom

def ppt_to_pdf(input_folder, output_folder):
    """
    批量转换PPT/PPTX文件为PDF
    参数：
        input_folder: 输入文件夹路径
        output_folder: 输出文件夹路径（自动创建）
    """
    # 初始化COM库[1](@ref)
    pythoncom.CoInitialize()
    
    # 创建输出目录
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 初始化PowerPoint应用[4](@ref)
    ppt_app = win32com.client.DispatchEx("PowerPoint.Application")
    ppt_app.Visible = 1  # 后台运行
    
    try:
        # 遍历输入目录
        for filename in os.listdir(input_folder):
            if filename.lower().endswith(('.ppt', '.pptx')):
                input_path = os.path.join(input_folder, filename)
                output_name = os.path.splitext(filename)[0] + '.pdf'
                output_path = os.path.join(output_folder, output_name)
                
                try:
                    # 打开演示文稿[6](@ref)
                    presentation = ppt_app.Presentations.Open(input_path)
                    # 设置PDF选项[5](@ref)
                    presentation.SaveAs(output_path, 32)  # 32对应PDF格式
                    print(f"成功转换: {filename} → {output_name}")
                except Exception as e:
                    print(f"转换失败 {filename}: {str(e)}")
                finally:
                    presentation.Close()
    except Exception as e:
        print(f"程序异常: {str(e)}")
    finally:
        # 释放资源[1,4](@ref)
        ppt_app.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    input_dir = r"D:\江财\研一下学期\碳金融与绿色金融\PPT"  # 输入目录
    output_dir = r"D:\江财\研一下学期\碳金融与绿色金融\output"  # 输出目录
    ppt_to_pdf(input_dir, output_dir)