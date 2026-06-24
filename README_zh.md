# comtrade-io

Python 库，用于从 COMTRADE 标准的 CFG/DAT/CFF/DFR/INF/DMF/HDR 文件加载波形数据，并提供便捷的 Pandas DataFrame 接口。

## 特性

- **单文件 API**: 通过 `ComtradeFile.from_file(file_name)` 直接加载 COMTRADE 实例
- **多格式读取**: 支持 CFG+DAT（多文件）、CFF 单文件、DFR（WNDR）格式
- **自动定位**: 自动查找同目录下的相关文件（cfg/dat/dmf/hdr/inf）
- **数据格式**: 支持 ASCII 和二进制 DAT 数据格式（BINARY、BINARY32、FLOAT32）
- **数据转换**: 将模拟量数据按系数转换为真实值
- **设备模型**: 解析 DMF 数据模型和 INF 信息为电力系统设备（母线、线路、变压器）
- **多种导出格式**: 支持导出为多文件（CFG+DAT）、CFF 单文件、JSON、CSV 格式
- **写入功能**: 支持将 Comtrade 对象写入为 CFG/DAT/INF/DMF/CFF 文件
- **Pandas 集成**: 返回 Pandas DataFrame 格式，方便数据分析
- **纯 Python**: 轻量实现，依赖少

## 依赖

- Python 3.10+
- pandas >= 2.3.3
- numpy >= 1.26.0
- pydantic >= 2.12.5
- loguru >= 0.7.3

## 安装

### 使用 pypi 仓库安装

```bash
# 使用 UV
uv add comtrade-io

# 使用 pip
pip install comtrade-io

```

### 使用 git 仓库源码安装

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
from comtrade_io.parser.comtrade_file import ComtradeFile

# 加载 COMTRADE 文件（自动查找 cfg/dat/dmf/hdr/inf 文件）
wave = ComtradeFile.from_file("tests/data/binary_1999.cfg")

# 访问配置信息
wave.config.description.header.station  # 厂站名
wave.config.description.header.recorder  # 录波器名
wave.channel_num.analog  # 模拟量通道数
wave.channel_num.status  # 数字量通道数
wave.sampling.segments[0].samp  # 采样率（Hz）

# 访问通道定义
wave.analogs[1]  # 模拟量通道（按索引）
wave.statuses[1]  # 数字量通道（按索引）

# 访问设备模型（从 DMF/INF 解析）
wave.get_bus_info("母线名称")  # 根据名称获取母线模型
wave.get_line_info("线路名称")  # 根据名称获取线路模型
wave.get_transformer_info("主变名称")  # 根据名称获取主变模型

# 访问 DAT 数据（DataFrame 列结构：第1列时间戳，之后为模拟量，再之后为数字量）
data = wave.get_data()

# 访问指定通道的瞬时值数据
wave.get_analog_channel(1)  # 获取模拟量通道及采样数据
wave.get_status_channel(1)  # 获取数字量通道及采样数据

# 访问设备及关联通道的瞬时值数据
wave.get_bus("母线名称")  # 获取母线及电压通道数据
wave.get_line("线路名称")  # 获取线路及电流/电压通道数据
wave.get_transformer("主变名称")  # 获取主变及各绕组通道数据
```

## 进阶用法

### 多格式加载

```python
# 从 CFF 单文件加载
cf = ComtradeFile.from_cff("recording.cff")

# 从 DFR（WNDR）文件加载
cf = ComtradeFile.from_dfr("recording.dfr")
```

### 导出文件

```python
# 保存为多文件格式（CFG+DAT+INF+DMF）— 默认
wave.save_comtrade("output.cfg")

# 保存为 CFF 单文件
wave.save_comtrade("output.cff", format="cff")

# 导出为 JSON
wave.save_comtrade("output.json", format="json")

# 导出为 CSV
wave.save_comtrade("output.csv", format="csv")

# 选择数据格式
wave.save_comtrade("output.cfg", data_format="ASCII")  # ASCII
wave.save_comtrade("output.cfg", data_format="BINARY")  # 二进制（默认）
wave.save_comtrade("output.cfg", data_format="BINARY32")  # 32位二进制
wave.save_comtrade("output.cfg", data_format="FLOAT32")  # 32位浮点

# 直接 JSON 导出
wave.save_json("output.json")
```

### 写入单个文件

```python
wave.write_cfg("output.cfg")  # 写入 CFG 配置文件
wave.write_dmf("output.dmf")  # 写入 DMF 数据模型
wave.write_inf("output.inf")  # 写入 INF 信息文件
```

### CFF 单文件格式

```python
from comtrade_io.parser.cff import CffFile

cff = CffFile.from_file("recording.cff")
cfg = cff.to_configure()  # 解析 CFG 部分
data = cff.to_data_content(cfg)  # 解析 DAT 部分
inf = cff.to_information()  # 解析 INF 部分（可选）
```

## 项目结构

```
comtrade_io/
├── src/comtrade_io/
│   ├── __init__.py               # 入口文件，导出 Comtrade 类
│   ├── model/                    # 数据模型（Pydantic）
│   │   ├── comtrade.py           # Comtrade 主类
│   │   ├── configure/            # CFG 配置模型
│   │   ├── description/          # 文件描述（文件头、采样、时间）
│   │   ├── channel/              # 模拟量和数字量通道模型
│   │   ├── equipment/            # 电力系统设备（母线、线路、变压器）
│   │   └── type/                 # 枚举和类型定义
│   ├── parser/                   # 文件解析器
│   │   ├── comtrade_file.py      # ComtradeFile 文件路径封装
│   │   ├── cfg/                  # CFG 配置文件解析
│   │   ├── dat/                  # DAT 数据解析器（ASCII/二进制）
│   │   ├── cff/                  # CFF 单文件解析器
│   │   ├── dfr/                  # DFR（WNDR）格式解析器
│   │   ├── dmf/                  # DMF 数据模型解析器（XML）
│   │   ├── inf/                  # INF 信息文件解析器
│   │   └── description/         # 解析辅助（时间、文件头、采样）
│   ├── exporters/               # 导出功能
│   │   ├── cff_exporter.py       # CFF 单文件导出
│   │   ├── csv_exporter.py       # CSV 导出
│   │   ├── json_exporter.py      # JSON 导出
│   │   ├── multi_file_exporter.py # 多文件（CFG+DAT）导出
│   │   └── decorators.py         # @export_format 装饰器
│   └── utils/                    # 工具函数
│       ├── file_path.py          # FilePath 智能路径类
│       ├── logging.py            # 基于 loguru 的日志
│       ├── text_utils.py         # 文本分割工具
│       └── numeric_utils.py      # 数字解析工具
├── tests/                        # 测试文件
└── docs/                         # 文档
```

## 核心类说明

### Comtrade

主类，封装完整的 COMTRADE 文件数据。

**属性:**

- `config`: Configure - CFG 配置信息（文件头、通道定义、采样信息）
- `data`: pd.DataFrame | None - 采样数据
- `buses`: List[Bus] - 母线列表（来自 DMF/INF）
- `lines`: List[Line] - 线路列表（来自 DMF/INF）
- `transformers`: List[Transformer] - 变压器列表（来自 DMF/INF）

**便捷属性（委托至 config）:**

- `analogs` / `statuses` - 通道字典
- `channel_num` - 通道数量
- `sampling` - 采样信息
- `start_time` / `fault_time` - 时间信息
- `data_type` - 数据格式
- `header` - 文件头

**主要方法:**

- `get_data()`: 返回采样数据 DataFrame
- `get_bus(name)`: 获取母线及电压通道数据
- `get_line(name)`: 获取线路及电流/电压通道数据
- `get_transformer(name)`: 获取变压器及各绕组数据
- `get_analog_channel(index)`: 获取模拟量通道及数据
- `get_status_channel(index)`: 获取数字量通道及数据
- `save_comtrade(path, format, data_format)`: 导出为文件
- `save_json(path)`: 导出为 JSON
- `write_cfg(path)` / `write_dmf(path)` / `write_inf(path)`: 写入单个文件

### Configure

CFG 配置模型。

**属性:**

- `description`: Description - 描述信息（文件头、通道数、采样、时间）
- `analogs`: Dict[int, Analog] - 模拟量通道定义
- `statuses`: Dict[int, Status] - 数字量通道定义

### ComtradeFile

文件路径封装类，自动定位相关文件并检测格式。

**支持格式:**

- **多文件格式**: CFG+DAT（传统方式），可选 DMF、INF、HDR
- **CFF 单文件**: `.cff` 将 CFG、INF、DAT 合并为一个文件
- **DFR**: `.dfr` WNDR 专有单文件格式

**主要方法:**

- `from_path(path)`: 根据任意 COMTRADE 文件路径创建
- `from_file(path)`: 解析文件并返回 `Comtrade` 实例

### 设备模型

- **Bus（母线）**: 电压通道、开关量/告警通道
- **Line（线路）**: 电流分支、母线关联、阻抗参数
- **Transformer（变压器）**: 多个绕组，每个绕组有独立的电压/电流通道
- **EquipmentGroup（设备组）**: 设备容器，支持通道覆盖

## COMTRADE 文件格式

电力系统故障录波数据的标准格式：

| 文件   | 必需 | 说明                              |
|------|----|---------------------------------|
| .cfg | 是  | 配置文件，定义通道、采样率等元数据               |
| .dat | 是  | 数据文件，包含采样点数据                    |
| .dmf | 否  | 数据模型文件（XML），定义电力系统设备模型          |
| .hdr | 否  | 头文件，包含录波设备信息                    |
| .inf | 否  | 信息文件，INI 格式的额外配置信息              |
| .cff | 否  | CFF 单文件格式，将 CFG、INF、DAT 合并为一个文件 |
| .dfr | 否  | DFR（WNDR）专有单文件格式                |

## 模块文档

详细的模块文档请参考 [docs/modules/README.md](docs/modules/README.md)。

### 主要模块

- [Comtrade 主类](docs/modules/comtrade.md) - 主要入口类
- [Configure (CFG 配置)](docs/modules/cfg/configure.md) - CFG 配置文件解析
- [DataContent (DAT 数据)](docs/modules/data/data_content.md) - DAT 数据文件解析
- [CffFile (CFF 单文件)](docs/modules/cff/cff.md) - CFF 单文件格式解析
- [ComtradeFile](docs/modules/comtrade_file.md) - 文件路径封装类
- [Information (INF 信息)](docs/modules/inf/information.md) - INF 信息文件解析

## 许可证

MIT 许可证

## 版本历史

- 0.1.0: 初始版本，支持 COMTRADE 文件的基本读写功能
- 0.1.1: 添加对 DMF 数据模型文件的支持
- 0.1.2: 和 0.1.1 版本一致
- 0.1.3: 添加对 CFF 单文件、INF 信息文件的支持
- **0.2.0**: 重大重构和新功能
  - 包结构重构为 `model/`、`parser/`、`exporters/`、`utils/` 模块
  - Comtrade 模型重构：`cfg` → `config`，集成设备模型
  - 全新的导出系统，`@export_format` 装饰器（多文件、CFF、JSON、CSV）
  - CFF 单文件格式解析和写入
  - DFR（WNDR）格式解析
  - 完整的 INF 文件解析，支持设备组生成
  - DMF 数据模型增强（母线、线路、带绕组的变压器）
  - `FilePath` 智能路径类，支持文件状态检测
  - 日志系统迁移至 loguru
  - 所有模型迁移至 Pydantic v2
  - 改进的 GBK/UTF-8 编码处理
- **0.2.1**: 增强 DFR 格式兼容性和 Bug 修复
  - 支持多型号 DFR 装置（2704V042、2704V072）
  - DFR 帧大小根据通道配置动态计算
  - 修复数据中模拟量未转换为瞬时值的问题
  - 修复 ASCII 导出未反向转换为 ADC 计数值的问题
  - 修复 INF/DMF 导出时母线/线路/变压器为 None 的崩溃问题
  - DFR 解析器重构为模块化子模块（wndr_section、binary_section、converter）
  - 添加批量 DFR→COMTRADE 转换脚本
- **0.3.0**: 代码规范和内部重构
  - 移除所有源文件的 shebang 和 coding 头部声明
  - 修复 `__init__.py` 中 `version` 变量名遮蔽问题
  - 替换不必要的 f-string 为普通字符串
  - `.env` 移至项目根目录，通过 `.env.example` 提供模板
  - 依赖规范：`dev-dependencies` 转为标准 `[project.optional-dependencies] dev`
  - 移除非必要的 `openpyxl` 依赖
  - 消除 `Comtrade.save_comtrade` 后置猴子补丁，`@export_format` 内联到类定义
  - 为 `Comtrade` 所有委托属性添加完整类型注解
  - 新增 CI/CD 工作流（`.github/workflows/publish.yml`），含多 Python 版本测试
  - 全部 357 个包内绝对导入转为相对导入（覆盖 95 个文件）
  - 清理 `compatibility.md` 中的硬编码本地路径
