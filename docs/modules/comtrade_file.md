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

## 主要功能

- 自动查找同目录下的相关文件
- 支持从任意相关文件路径初始化
- 提供各文件路径的启用状态检查

## 使用示例

```python
from comtrade_io.comtrade_file import ComtradeFile

# 从 cfg 文件初始化
cf = ComtradeFile.from_path("data/example.cfg")

# 检查各文件是否存在
print(f"CFG 存在: {cf.cfg_path.is_enabled()}")
print(f"DAT 存在: {cf.dat_path.is_enabled()}")
print(f"DMF 存在: {cf.dmf_path.is_enabled()}")

# 获取文件路径
print(f"CFG 路径: {cf.cfg_path.path}")
print(f"DAT 路径: {cf.dat_path.path}")
```

## 相关模块

- [Comtrade](comtrade.md) - 主类
