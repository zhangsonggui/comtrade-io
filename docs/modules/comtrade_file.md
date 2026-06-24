# ComtradeFile 类

ComtradeFile 是文件路径封装类，自动定位同目录下的相关文件。

## 概述

ComtradeFile 负责管理 COMTRADE 相关文件的路径，包括：

- .cfg - 配置文件
- .dat - 数据文件
- .dmf - 数据模型文件（可选）
- .hdr - 头文件（可选）
- .inf - 信息文件（可选）
- .cff - 单文件格式（可选）
- .dfr - DFR 单文件格式（可选）

## 主要功能

- 自动查找同目录下的相关文件
- 支持从任意相关文件路径初始化
- 提供各文件路径的启用状态检查
- 从各种格式解析为 Comtrade 对象

## 工厂方法

### from_path()

从任意 COMTRADE 文件路径创建 ComtradeFile 对象，自动匹配同目录下的同名文件。

```python
@classmethod
def from_path(cls, file_path: str | Path) -> "ComtradeFile"
```

### from_file()

从传统 COMTRADE 多文件（CFG+DAT）解析为 Comtrade 对象。

```python
@classmethod
def from_file(cls, file_name: str | Path) -> Comtrade | None
```

### from_cff()

从 CFF 单文件解析为 Comtrade 对象。

```python
@classmethod
def from_cff(cls, file_name: str | Path) -> Comtrade | None
```

### from_dfr()

从 DFR 单文件解析为 Comtrade 对象。

```python
@classmethod
def from_dfr(cls, file_name: str | Path) -> Comtrade | None
```

## 使用示例

```python
from comtrade_io.parser.comtrade_file import ComtradeFile

# 从 cfg 文件初始化
cf = ComtradeFile.from_path("data/example.cfg")

# 检查各文件是否存在
print(f"CFG 路径: {cf.cfg_path.path}")
print(f"DAT 路径: {cf.dat_path.path}")

# 直接解析文件
comtrade = ComtradeFile.from_file("data/example.cfg")
print(comtrade.config.description.header.station)
```

## 相关模块

- [Comtrade](comtrade.md) - 主类
