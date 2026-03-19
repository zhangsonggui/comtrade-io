# comtrade-io

Python 库，用于从 COMTRADE 标准的 CFG/DAT/INF/DMF/HDR 文件序列加载波形数据，并提供便捷的 Pandas DataFrame 接口。

## 特性

- **单文件 API**: 通过 `Comtrade.from_file(file_name)` 直接加载 COMTRADE 实例
- **自动定位**: 自动查找同目录下的相关文件（cfg/dat/dmf/hdr/inf）
- **多格式支持**: 支持 ASCII 和二进制 DAT 数据格式（BINARY, BINARY32, FLOAT32）
- **数据转换**: 将模拟量数据按系数转换为真实值（乘以 multiplier 加上 offset）
- **数据模型**: 支持 DMF 数据模型解析，包含电力系统设备模型（母线、线路、变压器）
- **INF 支持**: INF 信息可选解析为 `InfInfo` 对象，保留原始字段映射
- **读写功能**: 支持将 Comtrade 对象写入为 CFG/DAT 文件
- **Pandas 集成**: 返回 Pandas DataFrame 格式，方便数据分析
- **纯 Python**: 轻量实现，依赖少

## 依赖

- Python 3.10+
- pandas >= 2.3.3
- pydantic >= 2.12.5
- openpyxl >= 3.1.5

## 安装

```bash
# 使用 uv
uv sync

# 或直接安装
pip install comtrade_io
```

## 快速开始

```python
from comtrade_io import Comtrade

# 加载 COMTRADE 文件（自动查找 cfg/dat/dmf/hdr/inf 文件）
c = Comtrade.from_file("data/D51_RCD_2346_20150917_105253_065_F.cfg")

# 访问 CFG 配置
c.cfg.header  # 变电站名、录波设备名、版本
c.cfg.analogs  # 模拟量通道字典
c.cfg.digitals  # 数字量通道字典

# 访问 DAT 数据（返回 DataFrame）
c.get_data()  # 返回包含所有采样数据的 pandas DataFrame

# 访问指定模拟通道数据
c.get_analog_channel(1)  # 按索引获取模拟通道
```

## 进阶用法

### 数据模型（DMF）

```python
# 访问电力系统数据模型
c.buses  # 母线列表
c.lines  # 线路列表
c.transformers  # 变压器列表
c.analog_channels  # 模拟通道字典
c.status_channels  # 状态通道字典

# 按名称获取设备（自动加载通道数据）
bus = c.get_bus("母线名称")
line = c.get_line("线路名称")
transformer = c.get_transformer("变压器名称")

# 按索引获取通道
analog = c.get_analog_channel(1)
status = c.get_status_channel(1)
```

### 写入文件

```python
# 保存 Comtrade 对象为文件
c.to_file("output.cfg", data_type="BINARY")  # 二进制格式
c.to_file("output.cfg", data_type="ASCII")   # ASCII 格式

# 导出为 JSON
c.to_json_file("output.json")

# 导出为字典（pickle）
c.to_dict_file("output.pkl")
```

### 配置操作

```python
# 获取模拟量通道
analog = c.cfg.get_analog(1)

# 获取数字量通道
digital = c.cfg.get_digital(1)

# 获取采样段信息
nrate = c.cfg.get_sampling_nrate(1)
```

## 项目结构

```
comtrade_io/
├── src/comtrade_io/
│   ├── __init__.py           # 入口文件，导出 Comtrade 类
│   ├── comtrade.py           # Comtrade 主类
│   ├── comtrade_file.py      # 文件路径封装类
│   ├── cfg/                  # CFG 配置模块
│   │   ├── configure.py      # 配置解析主类
│   │   ├── analog.py         # 模拟通道类
│   │   ├── digital.py        # 数字通道类
│   │   ├── header.py         # 文件头类
│   │   └── sampling.py       # 采样信息类
│   ├── dmf/                  # DMF 数据模型模块
│   │   ├── comtrade_model.py # 数据模型主类
│   │   ├── bus.py            # 母线类
│   │   ├── line.py           # 线路类
│   │   ├── transformer.py   # 变压器类
│   │   └── ...
│   ├── inf/                  # INF 信息模块
│   ├── data/                 # DAT 数据解析器
│   └── utils/                # 工具函数
├── tests/                    # 测试文件
└── example/                  # 示例脚本
```

## 核心类说明

### Comtrade

主类，封装完整的 COMTRADE 文件数据。

**主要属性:**
- `file`: ComtradeFile - 包含所有文件路径信息
- `cfg`: Configure - CFG 配置信息
- `dat`: DataContent - DAT 数据内容
- `buses`: List[Bus] - 母线列表
- `lines`: List[Line] - 线路列表
- `transformers`: List[Transformer] - 变压器列表

**主要方法:**
- `from_file(file_name)`: 从文件加载 Comtrade 对象
- `to_file(filename, data_type)`: 保存为 COMTRADE 文件
- `to_json_file(filename)`: 导出为 JSON
- `get_bus(name)`: 根据名称获取母线
- `get_line(name)`: 根据名称获取线路
- `get_transformer(name)`: 根据名称获取变压器
- `get_analog_channel(index)`: 根据索引获取模拟通道
- `get_status_channel(index)`: 根据索引获取状态通道

### Configure

CFG 配置文件解析类。

**主要属性:**
- `header`: 文件头信息
- `channel_num`: 通道数量
- `analogs`: 模拟量通道字典
- `digitals`: 数字量通道字典
- `sampling`: 采样信息

### ComtradeFile

文件路径封装类，自动定位相关文件。

**主要属性:**
- `cfg_path`: CFG 文件路径
- `dat_path`: DAT 文件路径
- `dmf_path`: DMF 文件路径（可选）
- `hdr_path`: HDR 文件路径（可选）
- `inf_path`: INF 文件路径（可选）

## COMTRADE 文件格式

电力系统故障录波数据的标准格式：

| 文件 | 必需 | 说明 |
|------|------|------|
| .cfg | 是 | 配置文件，定义通道、采样率等元数据 |
| .dat | 是 | 数据文件，包含采样点数据 |
| .dmf | 否 | 数据模型文件，定义电力系统设备模型 |
| .hdr | 否 | 头文件，包含录波设备信息 |
| .inf | 否 | 信息文件，包含额外的配置信息 |

## 许可证

MIT 许可证

## 版本历史

- 0.1.0: 初始版本，支持 COMTRADE 文件的基本读写功能