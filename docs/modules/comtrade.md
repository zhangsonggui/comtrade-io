# Comtrade 类

Comtrade 是库的主入口类，封装完整的 COMTRADE 文件数据，提供统一的数据访问接口。

## 类定义

```python
class Comtrade(BaseModel):
    config: Configure = Field(default_factory=Configure, description="CFG配置")
    data: pd.DataFrame | None = Field(default=None, description="故障数据")
    buses: list[Bus] | None = Field(default_factory=list, description="母线")
    lines: list[Line] | None = Field(default_factory=list, description="线路")
    transformers: list[Transformer] | None = Field(default_factory=list, description="变压器")
```

## 属性

| 属性             | 类型                    | 描述                         |
|----------------|-----------------------|----------------------------|
| `config`       | Configure             | CFG 配置对象                   |
| `data`         | pd.DataFrame \| None  | 采样数据（DataFrame 格式）         |
| `description`  | Description           | 文件描述信息（委托至 `config.description`） |
| `buses`        | list[Bus] \| None     | 母线列表                       |
| `lines`        | list[Line] \| None    | 线路列表                       |
| `transformers` | list[Transformer] \| None | 变压器列表                  |

### 便捷属性（委托至 `config`）

| 属性                 | 类型                    | 描述                         |
|--------------------|-----------------------|----------------------------|
| `analogs`          | dict[int, Analog]     | 模拟量通道字典                   |
| `statuses`         | dict[int, Status]     | 状态量通道字典                   |
| `channel_num`      | ChannelNum \| None    | 通道数量定义                    |
| `sampling`         | Sampling \| None      | 采样信息（频率、采样率分段）            |
| `start_time`       | datetime \| None      | 录波开始时间                    |
| `fault_time`       | datetime \| None      | 故障触发时间                    |
| `data_type`        | DataType \| None      | 数据格式（ASCII/BINARY/BINARY32/FLOAT32） |
| `timemult`         | float \| None         | 时间乘数                      |
| `header`           | Header \| None        | 文件头（厂站名、录波器名、版本号）        |
| `time_info`        | TimeInfo \| None      | 时间信息及与UTC时间关系             |
| `sampling_time_quality` | SamplingTimeQuality \| None | 采样时间品质               |

## 工厂方法

### from_file() / from_cff() / from_dfr()

通过 `ComtradeFile` 类从文件加载 Comtrade 对象：

```python
from comtrade_io.parser.comtrade_file import ComtradeFile

# 通过 cfg 文件加载传统多文件格式
comtrade = ComtradeFile.from_file("dat/example.cfg")

# 通过 cff 单文件加载
comtrade = ComtradeFile.from_cff("dat/example.cff")

# 通过 dfr 单文件加载
comtrade = ComtradeFile.from_dfr("dat/example.dfr")
```

**解析顺序（from_file）：**

1. 调用 `ComtradeFile.from_path()` 自动定位同目录下的同名文件
2. 解析 CFG 文件获取 Configure 对象
3. 解析 DMF 文件获取设备模型；DMF 不存在时尝试解析 INF 文件
4. 若 DMF/INF 均不存在，通过通道名称自动推断设备拓扑
5. 解析 DAT 文件获取采样数据
6. 组装生成 Comtrade 对象

---

### get_data()

获取完整的数据 DataFrame。

```python
def get_data(self) -> pd.DataFrame
```

**返回：**

- pandas DataFrame，包含所有采样数据

**DataFrame 列结构：**

- 第 0 列：数据点索引
- 第 1 列：时间戳
- 第 2 列开始：模拟量通道数据
- 之后：状态量通道数据

---

### get_analog_channel()

根据通道标识获取模拟量通道，并加载通道数据。

```python
def get_analog_channel(self, index: int) -> Analog | None
```

**参数：**

- `index`: 通道索引（从 0 开始）

**返回：**

- Analog 对象，包含瞬时值采样数据

**示例：**

```python
analog = comtrade.get_analog_channel(0)
print(analog.data)  # 通道数据的 numpy 数组
```

---

### get_status_channel()

根据通道标识获取状态量通道，并加载通道数据。

```python
def get_status_channel(self, index: int) -> Status | None
```

**参数：**

- `index`: 通道索引（从 0 开始）

**返回：**

- Status 对象，包含瞬时值采样数据

---

### get_bus()

根据名称获取母线，并加载通道数据。

```python
def get_bus(self, name: str) -> Bus | None
```

**参数：**

- `name`: 母线名称

**返回：**

- Bus 对象，包含关联的电压通道及瞬时值数据

---

### get_line()

根据名称获取线路，并加载通道数据。

```python
def get_line(self, name: str) -> Line | None
```

**参数：**

- `name`: 线路名称

**返回：**

- Line 对象，包含关联的电流通道及瞬时值数据、母线参数及电压通道瞬时值数据

---

### get_transformer()

根据名称获取变压器，并加载通道数据。

```python
def get_transformer(self, name: str) -> Transformer | None
```

**参数：**

- `name`: 变压器名称

**返回：**

- Transformer 对象，包含主变和各绕组的参数及关联电压电流通道和瞬时值数据

---

### save_comtrade()

将 Comtrade 对象保存为文件。

```python
@export_format
def save_comtrade(
    self,
    output_file_path: ComtradeFile | Path | str,
    format: str = "multi_file",
    data_format: str = "BINARY",
    **kwargs,
)
```

**参数：**

- `output_file_path`: 输出文件路径
- `format`: 导出格式，"multi_file"（默认）、"cff"、"json"、"csv"
- `data_format`: 数据格式，"BINARY"（默认）、"ASCII"、"BINARY32"、"FLOAT32"

**示例：**

```python
# 保存为多文件格式（CFG+DAT）
comtrade.save_comtrade("output/output.cfg")

# 保存为 CFF 单文件
comtrade.save_comtrade("output/output.cff", format="cff")

# 保存为 JSON
comtrade.save_comtrade("output/output.json", format="json")

# 保存为 CSV
comtrade.save_comtrade("output/output.csv", format="csv")
```

---

### save_json()

将 Comtrade 对象转换为 JSON 字符串（包含 data 数据）。

```python
def save_json(
    self,
    output_file_path: Path | str,
    indent: int | None = None
)
```

**参数：**

- `output_file_path`: 输出 JSON 文件路径
- `indent`: JSON 缩进空格数，可选

**返回：**

- True 表示成功

---

### model_dump_json()

将 Comtrade 模型转换为 JSON 字符串（不包含 data、config 字段）。

```python
def model_dump_json(
    self,
    *,
    indent: int | None = None,
    **kwargs
) -> str
```

**参数：**

- `indent`: JSON 缩进空格数，可选
- `**kwargs`: 其他 pydantic 参数

**返回：**

- JSON 字符串

---

## 设备拓扑查询方法

### get_bus_info()

根据名称获取母线模型（不包含数据）。

```python
def get_bus_info(self, name: str) -> Bus | None
```

### get_line_info()

根据名称获取线路模型（不包含数据）。

```python
def get_line_info(self, name: str) -> Line | None
```

### get_transformer_info()

根据名称获取变压器模型（不包含数据）。

```python
def get_transformer_info(self, name: str) -> Transformer | None
```

### get_analog_channel_info()

根据索引获取模拟量通道模型（不包含数据）。

```python
def get_analog_channel_info(self, index: int) -> Analog | None
```

### get_status_channel_info()

根据索引获取状态量通道模型（不包含数据）。

```python
def get_status_channel_info(self, index: int) -> Status | None
```

---

## Pydantic 特性

由于 Comtrade 继承自 pydantic BaseModel，可以使用以下方法：

- `model_dump()`: 转换为字典
- `model_dump_json()`: 转换为 JSON 字符串
- `model_validate()`: 验证数据

**示例：**

```python
# 转换为字典（不含数据）
data_dict = comtrade.model_dump(exclude={"data"})

# 转换为 JSON（不含数据）
json_str = comtrade.model_dump_json(indent=2)
```

## 文件写入

```python
comtrade.write_cfg("output.cfg")    # 写入 CFG 配置文件
comtrade.write_dmf("output.dmf")    # 写入 DMF 数据模型
comtrade.write_inf("output.inf")    # 写入 INF 信息文件
```
