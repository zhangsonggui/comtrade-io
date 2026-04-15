# DataContent 类

DataContent 是 DAT 数据文件的解析类，负责读取和解析 COMTRADE 标准的数据文件。

## 类定义

```python
class DataContent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    cfg: Configure = Field(..., description="配置文件")
    file_name: Path | ComtradeFile | str | None = Field(default=None, description="dat文件路径")
    dat_text: str | None = Field(default=None, description="DAT数据文本(ASCII格式)")
    dat_bytes: bytes | None = Field(default=None, description="DAT数据字节(二进制格式)")
    data: pd.DataFrame = Field(default=None, description="数据内容")
```

## 属性

| 属性          | 类型                                    | 描述                          |
|-------------|---------------------------------------|-----------------------------|
| `cfg`       | Configure                             | 配置文件对象                      |
| `file_name` | Optional[Path \| ComtradeFile \| str] | DAT 文件路径（从文件读取时使用）          |
| `dat_text`  | Optional[str]                         | DAT 数据文本（ASCII 格式，从内存读取时使用） |
| `dat_bytes` | Optional[bytes]                       | DAT 数据字节（二进制格式，从内存读取时使用）    |
| `data`      | pd.DataFrame                          | 解析后的 pandas DataFrame 数据    |

## 初始化方式

### 从文件读取

```python
from comtrade_io.data import DataContent

data_content = DataContent(cfg=configure, file_name="data/example.dat")
```

### 从内存读取（ASCII）

```python
data_content = DataContent(cfg=configure, dat_text=ascii_data_str)
```

### 从内存读取（二进制）

```python
data_content = DataContent(cfg=configure, dat_bytes=binary_data_bytes)
```

## DataFrame 数据结构

| 列索引            | 内容      | 类型      |
|----------------|---------|---------|
| 0              | 数据点索引   | int32   |
| 1              | 时间戳     | int32   |
| 2 ~ An+1       | 模拟量通道数据 | float64 |
| An+2 ~ An+Dn+1 | 状态量通道数据 | int32   |

其中：

- An = 模拟通道数
- Dn = 状态通道数

## 方法

### read()

从文件读取数据，返回 pandas DataFrame。

```python
def read(self) -> pd.DataFrame | None
```

**返回：**

- pandas DataFrame，读取失败返回 None

---

### read_from_memory()

从内存数据读取，返回 pandas DataFrame。

```python
def read_from_memory(self) -> pd.DataFrame | None
```

**返回：**

- pandas DataFrame，读取失败返回 None

---

### get_data()

获取指定通道的数据。

```python
def get_data(
    self,
    index: int,
    data_type: str = "analog",
    start_point: int = 1,
    end_point: int = None,
)
```

**参数：**

- `index`: 通道索引（从 0 开始）
- `data_type`: 数据类型，可选值：
    - `"point"`: 获取数据点索引列（第 0 列）
    - `"time"`: 获取时间戳列（第 1 列）
    - `"analog"`: 获取模拟量通道数据（默认）
    - `"status"`: 获取开关量通道数据
- `start_point`: 起始采样点（从 1 开始）
- `end_point`: 结束采样点

**返回：**

- numpy 数组，列索引超出范围返回 None

**示例：**

```python
# 获取时间戳
time_data = data_content.get_data(0, data_type="time")

# 获取第一个模拟通道数据
analog_data = data_content.get_data(0, data_type="analog")

# 获取第一个状态通道数据
status_data = data_content.get_data(0, data_type="status")

# 获取指定范围的数据
partial_data = data_content.get_data(0, data_type="analog", start_point=1, end_point=100)
```

---

### write_file()

将数据写入文件。

```python
def write_file(
    self,
    output_file_path: ComtradeFile | Path | str,
    data_type: str = "BINARY"
)
```

**参数：**

- `output_file_path`: 输出文件路径
- `data_type`: 保存格式，"BINARY"（默认）或 "ASCII"

**返回：**

- True 表示成功

**示例：**

```python
# 保存为二进制格式
data_content.write_file("output/output.dat", data_type="BINARY")

# 保存为 ASCII 格式
data_content.write_file("output/output.dat", data_type="ASCII")
```

---

### verify_and_recalculate_sampling()

校验采样时间并重新计算采样频率。

```python
def verify_and_recalculate_sampling(self) -> Sampling
```

**返回：**

- 重新计算后的 Sampling 对象

**算法说明：**

1. 读取 data 文件中第二列的采样时间（微秒）
2. 与 cfg 中的 timemult 相乘得出真正的采样时间
3. 根据采样时间间隔重新计算采样频率，将相同采样频率的点放到一起
4. Segment 中的 samp 是该段的采样频率，end_point 是该段最后一个采样点索引
5. 周波默认 20ms

---

## 内部方法

### from_ascii_file()

从 ASCII 格式文件读取数据。

```python
def from_ascii_file(self, expected_rows, expected_cols)
```

### from_ascii_str()

从 ASCII 格式字符串读取数据。

```python
def from_ascii_str(self, expected_rows, expected_cols)
```

### from_binary_file()

从二进制格式文件读取数据。

```python
def from_binary_file(self, expected_rows)
```

### from_binary_bytes()

从字节数据读取二进制格式数据。

```python
def from_binary_bytes(self, expected_rows)
```

### _process_data()

处理读取的数据，设置格式并转换模拟量值。

```python
def _process_data(
    self,
    content: pd.DataFrame | None,
    expected_rows: int,
    expected_cols: int
) -> pd.DataFrame | None
```

### _process_ascii_content()

处理 ASCII 格式的 DataFrame 内容。

```python
def _process_ascii_content(
    self,
    content: pd.DataFrame,
    expected_rows: int,
    expected_cols: int,
    source_name: str
)
```

### _write_ascii_dat_file()

将数据写入 ASCII 格式文件。

```python
def _write_ascii_dat_file(self, output_file_path: Path | str)
```

### _write_binary_dat_file()

将数据写入二进制格式文件。

```python
def _write_binary_dat_file(self, output_file_path: Path | str)
```

---

## 数据转换

DataContent 会自动将模拟量的原始采样值转换为真实值：

```
真实值 = 原始值 × multiplier + offset
```

这个转换在 `_process_data()` 方法中使用向量化操作完成，保证了性能。

---

## 二进制格式说明

支持的二进制数据类型：

| DataType | 说明         | 模拟量字节数 |
|----------|------------|--------|
| ASCII    | ASCII 文本格式 | -      |
| BINARY   | 16 位整数     | 2 字节   |
| BINARY32 | 32 位整数     | 4 字节   |
| FLOAT32  | 32 位浮点数    | 4 字节   |

二进制采样点结构：

- 4 字节：数据点索引（int32）
- 4 字节：时间戳（int32）
- An × 2/4 字节：模拟量数据
- Dn_words × 2 字节：状态量数据（每 16 位一个字）
