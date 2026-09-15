import logging
import subprocess
import sys
from functools import cached_property
from pathlib import Path
from typing import Optional, List

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# 用户配置区域（请在此修改您的设置）
# =============================================================================
# ---- 必填参数 ----
INPUT_FILE = Path("./1.txt")
OUTPUT_FILE = Path("./1.epub")

# ---- 可选参数 ----
COVER_IMAGE = Path("./cover.png")      # 封面图片，无则为None，有则为 Path("./cover.png")
CSS_FILE = Path("./style1.css")        # 外部 CSS 样式文件
TITLE = ""                             # 书名
AUTHOR = ""                            # 作者
DESCRIPTION = """
"""                                    # 简介（多行文本需谨慎，建议简短）
PUBLISHER = "倾城出版社"                # 出版社
PANDOC_PATH = "pandoc"                 # pandoc 可执行文件路径

# ---- Markdown 解析控制（新增） ----
INPUT_FORMAT = "commonmark"            # pandoc 支持的输入格式，如 "markdown", "gfm", "markdown_strict" 等

ADDITIONAL_EXTENSIONS = [
    "pipe_tables",          # 表格支持
    "footnotes",            # 脚注支持,标准脚注语法 [^1] 配合 [^1]: 脚注内容。
    "strikeout",            # 删除线,语法： ~~删除的文字~~。
]

GENERATE_TOC = False                   # 是否生成目录
TOC_DEPTH = 3                          # 目录深度（仅当 GENERATE_TOC=True 时生效）
# =============================================================================


class TxtToEpubConverter:
    """将 CommonMark 格式的 TXT 文件转换为 EPUB 电子书。"""

    def __init__(
        self,
        input_file: Path,
        output_file: Path,
        cover_image: Optional[Path] = None,
        css_file: Optional[Path] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        publisher: Optional[str] = None,
        input_format: str = "commonmark",
        additional_extensions: Optional[List[str]] = None,
        generate_toc: bool = False,
        toc_depth: int = 3,
        *,
        pandoc_path: str = "pandoc",
    ) -> None:

        """初始化转换器。"""
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.cover_image = Path(cover_image) if cover_image else None
        self.css_file = Path(css_file) if css_file else None
        self.title = title
        self.author = author
        self.description = description
        self.publisher = publisher
        self.input_format = input_format
        self.additional_extensions = additional_extensions or []
        self.generate_toc = generate_toc
        self.toc_depth = toc_depth
        self.pandoc_path = pandoc_path

        self._validate_files()

    def _validate_files(self) -> None:
        """检查输入文件、封面、CSS 是否存在，输出目录是否可写。"""
        if not self.input_file.is_file():
            raise FileNotFoundError(f"输入文件不存在: {self.input_file}")

        out_dir = self.output_file.parent
        if out_dir and not out_dir.exists():
            raise FileNotFoundError(f"输出目录不存在: {out_dir}")

        if self.cover_image and not self.cover_image.is_file():
            raise FileNotFoundError(f"封面图片不存在: {self.cover_image}")

        if self.css_file and not self.css_file.is_file():
            raise FileNotFoundError(f"CSS 样式文件不存在: {self.css_file}")

    @cached_property
    def epub_version_supported(self) -> bool:
        """
        检测 pandoc 是否支持 --epub-version 选项。
        结果会被缓存，避免重复检测。
        """
        try:
            result = subprocess.run(
                [self.pandoc_path, "--help"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return "--epub-version" in result.stdout
        except Exception as e:
            logger.warning(f"无法检测 pandoc 版本支持 ({e})，假定不支持 --epub-version")
            return False

    def _build_command(self) -> list[str]:
        """构建 pandoc 命令行参数列表。"""
        cmd = [self.pandoc_path]

        # ---- 输入格式 ----
        input_format = self.input_format
        if self.additional_extensions:
            # 追加扩展，如 markdown + footnotes + pipe_tables
            ext_str = "+".join(self.additional_extensions)
            input_format = f"{input_format}+{ext_str}"
        cmd.extend(["-f", input_format])
        cmd.extend(["-t", "epub"])
        
        # ---- 取消单独的标题页（新增） ----
        cmd.append("--epub-title-page=false")

        # ---- 封面图片 ----
        if self.cover_image:
            cmd.extend(["--epub-cover-image", str(self.cover_image)])

        # ---- 外部 CSS ----
        if self.css_file:
            cmd.extend(["--css", str(self.css_file)])

        # ---- 目录生成 ----
        if self.generate_toc:
            cmd.append("--toc")
            cmd.extend(["--toc-depth", str(self.toc_depth)])

        # ---- 元数据 ----
        meta_map = {
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "publisher": self.publisher,
        }
        for key, value in meta_map.items():
            if value:
                cmd.extend(["--metadata", f"{key}={value}"])

        # ---- 输入输出文件 ----
        cmd.extend([str(self.input_file), "-o", str(self.output_file)])
        return cmd

    def convert(self) -> None:
        """执行转换，失败时抛出 RuntimeError。"""
        cmd = self._build_command()
        logger.info(f"执行命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as err:
            raise RuntimeError(
                f"未找到 pandoc 可执行文件，请确保已安装 pandoc 并可通过 '{self.pandoc_path}' 调用。"
            ) from err

        if result.returncode != 0:
            error_msg = f"pandoc 转换失败 (返回码 {result.returncode}):\n"
            error_msg += result.stderr.strip() if result.stderr else "(无错误输出)"
            raise RuntimeError(error_msg)

        logger.info(f"转换成功！EPUB 文件已生成: {self.output_file}")


# =============================================================================
# 主程序入口（使用上方配置参数）
# =============================================================================
if __name__ == "__main__":
    converter = TxtToEpubConverter(
        input_file=INPUT_FILE,
        output_file=OUTPUT_FILE,
        cover_image=COVER_IMAGE,
        css_file=CSS_FILE,
        title=TITLE,
        author=AUTHOR,
        description=DESCRIPTION,
        publisher=PUBLISHER,
        input_format=INPUT_FORMAT,
        additional_extensions=ADDITIONAL_EXTENSIONS,
        generate_toc=GENERATE_TOC,
        toc_depth=TOC_DEPTH,
        pandoc_path=PANDOC_PATH,
    )

    try:
        converter.convert()
    except Exception as exc:
        logger.error(f"转换失败: {exc}")
        sys.exit(1)
