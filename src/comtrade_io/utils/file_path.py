from pathlib import Path

from pydantic import BaseModel, Field

from .logging import get_logger

logger = get_logger()


class FilePath(BaseModel):
    """文件路径类

    封装文件路径及其状态信息，包括文件是否存在、是否为空、是否可读等。
    用于 COMTRADE 文件体系中的各类文件路径管理（CFG/DAT/CFF/DMF/HDR/INF/DFR）。

    属性:
        path: 文件路径，为 None 时表示未设置
        is_exists: 文件在磁盘上是否存在
        is_empty: 文件内容是否为空（大小为 0）
        is_readable: 文件是否可读取
    """

    path: Path | None = Field(default=None, description="文件路径")
    is_exists: bool = Field(default=True, description="文件是否存在")
    is_empty: bool = Field(default=False, description="文件是否为空")
    is_readable: bool = Field(default=True, description="文件是否可读")

    def model_post_init(self, context, /):
        """初始化后自动检测文件状态

        根据 path 指向的磁盘文件，更新 is_exists / is_empty / is_readable 状态。
        当 path 为 None 时不执行任何检测。
        """
        if self.path is None:
            return
        if self.path.exists():
            self.is_exists = True
            self.is_empty = self.path.stat().st_size == 0
        else:
            self.is_exists = False
            self.is_readable = False
            self.is_empty = True

    @classmethod
    def from_name(cls, file_name: str | Path | None) -> "FilePath":
        """工厂方法：从文件名或路径创建 FilePath 对象

        参数:
            file_name: 文件路径字符串或 Path 对象。
                       None 或空白字符串时返回默认 FilePath()。

        返回:
            FilePath: 根据 file_name 创建的 FilePath 实例
        """
        if file_name is None or (
            isinstance(file_name, str) and file_name.strip() == ""
        ):
            return cls()
        if isinstance(file_name, str):
            file_name = Path(file_name.strip())
        return cls(path=file_name)

    def _ensure_checked(self):
        """惰性检查文件的读取权限

        仅对存在的文件执行一次读取测试，避免重复 I/O。
        若读取失败则将 is_readable 置为 False。
        """
        if (
            self.path is None
            or not self.is_exists
            or hasattr(self, "_readable_checked")
        ):
            return
        self._readable_checked = True
        try:
            with open(self.path, "rb") as f:
                f.read(1)
        except (OSError, PermissionError) as e:
            logger.debug(f"文件{self.path}不可读: {e}")
            self.is_readable = False

    def is_enabled(self) -> bool:
        """判断文件是否可用

        文件可用需同时满足三个条件：
        1. 文件存在（is_exists）
        2. 文件非空（not is_empty）
        3. 文件可读（is_readable）

        返回:
            bool: 文件可使用时返回 True，否则返回 False
        """
        if self.path is None:
            return False
        self._ensure_checked()
        return all([not self.is_empty, self.is_exists, self.is_readable])

    def __str__(self):
        """返回文件状态的简要描述"""
        return f"文件：{self.path}{'可用' if self.is_enabled() else '不可用'}"
