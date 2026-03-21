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

### 使用pypi仓库安装

```bash
# 使用UV
uv add comtrade-io

# 使用pip
pip install comtrade-io

```

### 使用git仓库源码安装

```bash
# 克隆源码
git clone https://github.com/zhangsonggui/comtrade-io.git
git clone https://gitee.com/zhangsonggui/comtrade-io.git
# 进入项目安装依赖
cd comtrade-io
uv sync
```


## 快速开始

```python
from comtrade_io import Comtrade

# 加载 COMTRADE 文件（自动查找 cfg/dat/dmf/hdr/inf 文件）
wave = Comtrade.from_file("data/D51_RCD_2346_20150917_105253_065_F.cfg")

# 访问模型方法（不含采样数据）
wave.get_bus_info("母线名称")  # 返回指定母线名称的模型包含电压通道、开关量通道
wave.get_line_info("线路名称")  # 返回指定线路名称的模型包含电压通道、开关量通道
wave.get_transformer_info("主变名称")  # 返回指定主变、绕组名称的模型包含电压通道、开关量通道
wave.get_analog_channel_info("模拟量an")  # 返回指定模拟量标识的模型
wave.get_status_channel_info("开关量dn")  # 返回指定开关量标识的模型

# 访问 DAT 数据（DataFrame列结构：第1列为时间戳，第2列开始为模拟量，之后为开关量）
data = wave.get_data()  # 或wave.dat.data 返回包含所有采样数据的 pandas DataFrame，

# 访问指定模拟通道数据
wave.get_analog_channel(1)  # 按通道标识获取模拟量通道包含瞬时值采样数据
wave.get_status_channel(1)  # 按通道标识获取开关量通道包含瞬时值采样数据

# 访问指定线路、母线、主变通道数据
wave.get_bus("母线名称")  # 按母线名称获取母线参数及关联的电压通道及瞬时值数据
wave.get_line("线路名称")  # 按线路名称获取线路参数及关联的电流通道及瞬时值数据、母线参数及电压通道瞬时值数据
wave.get_transformer("主变名称")  # 按主变名称获取主变和各绕组的参数及关联电压电流通道和瞬时值数据


```

## 进阶用法

### 写入文件

```python
# 保存 Comtrade 对象为文件
wave.save_comtrade("output.cfg", data_type="BINARY")  # 二进制格式
wave.save_comtrade("output.cfg", data_type="ASCII")  # ASCII 格式

# 导出为 JSON文件
wave.save_json("output.json")

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
**注意** 本模块所有模型由pydantic进行约束，对于对象转json或dict可以调用pydantic的model_dump_json方法来实现

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
- `get_bus(name)`: 根据名称获取母线及对应电压通道的瞬时值数据
- `get_line(name)`: 根据名称获取线路及对应母线电压、电流通道的瞬时值数据
- `get_transformer(name)`: 根据名称获取变压器及对应电压、电流通道的瞬时值数据
- `get_analog_channel(index)`: 根据索引获取模拟通道及瞬时值数据
- `get_status_channel(index)`: 根据索引获取状态通道及瞬时值数据
- `get_bus_info()`: 根据名称获取母线模型
- `get_line_info()`: 根据名称获取线路模型
- `get_transformers_info()`: 根据名称获取主变模型
- `get_analog_channel_info()`: 根据名称获取模拟量模型
- `get_status_channel_info()`: 根据名称获取开关量模型

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