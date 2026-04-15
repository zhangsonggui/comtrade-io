# CffFile 类

CffFile 是 CFF 单文件格式的解析器，CFF 格式将 cfg/dat/inf/hdr 合并为单个 .cff 文件，便于文件管理和传输。

## 类定义

```python
class CffFile:
    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.sections = extract_sections(self.file_path)
```

## 属性

| 属性          | 类型         | 描述       |
|-------------|------------|----------|
| `file_path` | Path       | CFF 文件路径 |
| `sections`  | CffSection | 提取的各部分数据 |

### CffSection 类

存储从 CFF 单文件中提取的各个部分的数据。

```python
class CffSection(BaseModel):
    cfg: Optional[str] = Field(default=None, description="CFG 配置部分文本")
    dat: Optional[str] = Field(default=None, description="DAT 数据部分文本(ASCII格式)")
    dat_bytes: Optional[bytes] = Field(default=None, description="DAT 数据部分字节(二进制格式)")
    inf: Optional[str] = Field(default=None, description="INF 信息部分文本")
    hdr: Optional[str] = Field(default=None, description="HDR 头部部分文本")
```

## 只读属性

### cfg_text

返回 CFG 配置部分文本。

```python
@property
def cfg_text(self) -> Optional[str]
```

**返回：**

- CFG 配置文本，不存在则返回 None

---

### dat_text

返回 DAT 数据部分文本。

```python
@property
def dat_text(self) -> Optional[str]
```

**返回：**

- DAT 数据文本（ASCII 格式），不存在则返回 None

---

### inf_text

返回 INF 信息部分文本。

```python
@property
def inf_text(self) -> Optional[str]
```

**返回：**

- INF 信息文本，不存在则返回 None

---

### hdr_text

返回 HDR 头部部分文本。

```python
@property
def hdr_text(self) -> Optional[str]
```

**返回：**

- HDR 头部文本，不存在则返回 None

---

## 方法

### from_file()

从文件路径创建 CffFile 对象。

```python
@classmethod
def from_file(cls, file_path: Union[str, Path]) -> "CffFile"
```

**参数：**

- `file_path`: CFF 文件路径

**返回：**

- CffFile 对象

**示例：**

```python
from comtrade_io.cff import CffFile

cff_file = CffFile.from_file("data/example.cff")
```

---

### extract_sections()

从 CFF 文件中提取各个 section。

```python
def extract_sections(cff_path: Union[str, Path]) -> CffSection
```

**参数：**

- `cff_path`: CFF 文件路径

**返回：**

- CffSection 对象，包含各部分文本

**异常：**

- FileNotFoundError: 当 CFF 文件不存在时抛出

**CFF 文件格式：**
CFF 文件使用类似 "---file type CFG---" 的标记来分隔不同部分。

示例：

```
--- file type  CFG ---
[CFG 配置内容]
--- file type  DAT ---
[DAT 数据内容]
--- file type  INF ---
[INF 信息内容]
```

---

### to_configure()

将 CFG 部分转换为 Configure 对象（不生成临时文件）。

```python
def to_configure(self) -> Optional[Configure]
```

**返回：**

- Configure 对象，解析失败返回 None

**示例：**

```python
configure = cff_file.to_configure()
if configure:
    print(f"模拟通道数: {configure.channel_num.analog}")
```

---

### to_data_content()

将 DAT 部分转换为 DataContent 对象（不生成临时文件）。

```python
def to_data_content(self, cfg: Configure) -> Optional[DataContent]
```

**参数：**

- `cfg`: Configure 配置对象

**返回：**

- DataContent 对象，解析失败返回 None

**示例：**

```python
configure = cff_file.to_configure()
data_content = cff_file.to_data_content(configure)
if data_content:
    print(f"数据点数量: {len(data_content.data)}")
```

---

### to_information()

将 INF 部分转换为 Information 对象（不生成临时文件）。

```python
def to_information(self):
```

**返回：**

- ComtradeModel 对象，解析失败返回 None

**示例：**

```python
information = cff_file.to_information()
if information:
    print(f"母线数量: {len(information.buses)}")
```

---

## 使用示例

### 完整解析示例

```python
from comtrade_io.cff import CffFile

# 创建 CffFile 对象
cff_file = CffFile.from_file("data/example.cff")

# 解析 CFG 配置
configure = cff_file.to_configure()
print(f"站号: {configure.header.station}")
print(f"版本: {configure.header.version}")
print(f"模拟通道: {configure.channel_num.analog}")
print(f"数字通道: {configure.channel_num.status}")

# 解析 DAT 数据
if configure:
    data_content = cff_file.to_data_content(configure)
    print(f"数据点: {len(data_content.data)}")
    print(f"数据列: {data_content.data.shape[1]}")

# 解析 INF 信息（可选）
information = cff_file.to_information()
if information:
    print(f"母线: {len(information.buses)}")
    print(f"线路: {len(information.lines)}")
    print(f"变压器: {len(information.transformers)}")
```

### 通过 Comtrade.from_file 解析

```python
from comtrade_io import Comtrade

# 直接通过 Comtrade 类解析 CFF 文件
comtrade = Comtrade.from_file("data/example.cff")

# 访问数据
print(comtrade.cfg.header.station)
print(comtrade.dat.data.head())
```

---

## 编码处理

CFF 文件读取使用 GBK 编码，同时支持容错处理：

```python
content = path.read_text(encoding="gbk", errors="replace")
```

如果 GBK 解码失败，会使用替换模式避免异常。

---

## 性能优化

- CFF 文件解析在内存中完成，不生成任何临时文件
- 各部分数据直接传递给对应模块处理
- 支持 ASCII 和二进制 DAT 格式
