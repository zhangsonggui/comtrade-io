# Comtrade 类

Comtrade 是库的主入口类，封装完整的 COMTRADE 文件数据，提供统一的数据访问接口。

## 类定义

```python
class Comtrade(ComtradeModel):
    file: ComtradeFile = Field(default_factory=ComtradeFile, description="文件路径")
    cfg: Configure = Field(..., description="参数配置文件")
    dat: Optional[DataContent] = Field(default=None, description="故障数据")
```

## 属性

| 属性             | 类型                    | 描述                         |
|----------------|-----------------------|----------------------------|
| `file`         | ComtradeFile          | 文件路径封装对象                   |
| `cfg`          | Configure             | CFG 配置对象                   |
| `dat`          | Optional[DataContent] | DAT 数据内容对象                 |
| `description`  | Description           | 文件描述信息（继承自 ComtradeModel）  |
| `buses`        | List[Bus]             | 母线列表（继承自 ComtradeModel）    |
| `lines`        | List[Line]            | 线路列表（继承自 ComtradeModel）    |
| `transformers` | List[Transformer]     | 变压器列表（继承自 ComtradeModel）   |
| `analogs`      | Dict[int, Analog]     | 模拟量通道字典（继承自 ComtradeModel） |
| `statuses`     | Dict[int, Status]     | 状态量通道字典（继承自 ComtradeModel） |

## 方法

### from_file()

从文件加载 Comtrade 对象。

```python
@classmethod
def from_file(cls, file_name: str | Path | ComtradeFile) -> "Comtrade|None"
```

**参数：**

- `file_name`: 文件路径，可以是字符串、Path 对象或 ComtradeFile 对象。可以是 cfg/dat/cff/inf/dmf 任意文件名。

**返回：**

- Comtrade 对象，加载失败返回 None

**解析顺序：**

1. 判断是否是 CFF 单文件，如果是则使用 CFF 解析逻辑
2. 解析 CFG 文件获取 Configure 对象
3. 解析 DMF 文件获取 ComtradeModel 对象
4. 如果 DMF 不存在，尝试解析 INF 文件
5. 同步 Configure 和 ComtradeModel 的通道信息
6. 解析 DAT 文件获取 DataContent 对象
7. 合并形成 Comtrade 对象

**示例：**

```python
from comtrade_io import Comtrade

# 通过 cfg 文件加载
comtrade = Comtrade.from_file("data/example.cfg")

# 通过 cff 文件加载
comtrade = Comtrade.from_file("data/example.cff")
```

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
def get_analog_channel(self, index: int) -> Optional[Analog]
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
def get_status_channel(self, index: int) -> Optional[Status]
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
def save_comtrade(
    self,
    output_file_path: ComtradeFile | Path | str,
    data_type: str = "BINARY"
)
```

**参数：**

- `output_file_path`: 输出文件路径
- `data_type`: 保存格式，"BINARY"（默认）或 "ASCII"

**返回：**

- 成功消息字符串

**示例：**

```python
# 保存为二进制格式
comtrade.save_comtrade("output/output.cfg", data_type="BINARY")

# 保存为 ASCII 格式
comtrade.save_comtrade("output/output.cfg", data_type="ASCII")
```

---

### save_json()

将 Comtrade 对象转换为 JSON 字符串（包含 dat 数据）。

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

将 Comtrade 模型转换为 JSON 字符串（不包含 dat、cfg、file 字段）。

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

## 继承的方法（来自 ComtradeModel）

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
- 等等

**示例：**

```python
# 转换为字典（不含数据）
data_dict = comtrade.model_dump(exclude={"dat", "cfg", "file"})

# 转换为 JSON（不含数据）
json_str = comtrade.model_dump_json(exclude={"dat", "cfg", "file"}, indent=2)
```
