# CffFile 类

CffFile 是 CFF 单文件格式的解析器，CFF 格式将 cfg/dat/inf/hdr 合并为单个 .cff 文件，便于文件管理和传输。

## 类定义

```python
@dataclass
class CffFile:
    file_path: Path
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

## 方法

### from_file()

从文件路径创建 CffFile 对象。

```python
@classmethod
def from_file(cls, file_path: str | Path) -> "CffFile"
```

**参数：**

- `file_path`: CFF 文件路径

**返回：**

- CffFile 对象

**示例：**

```python
from comtrade_io.parser.cff import CffFile

cff_file = CffFile.from_file("dat/example.cff")
```

---

### extract_sections()

从 CFF 文件中提取各个 section。

```python
def extract_sections(cff_path: str | Path) -> CffSection
```

**CFF 文件格式：**

CFF 文件使用类似 `---file type CFG---` 的标记来分隔不同部分。

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

将 CFG 部分转换为 Configure 对象。

```python
def to_configure(self) -> Configure | None
```

**返回：**

- Configure 对象，解析失败返回 None

---

### to_data_content()

将 DAT 部分转换为 DataFrame（不生成临时文件）。

```python
def to_data_content(self, cfg: Configure) -> pd.DataFrame | None
```

**参数：**

- `cfg`: Configure 配置对象

**返回：**

- pandas DataFrame，解析失败返回 None

---

### to_information()

将 INF 部分转换为 EquipmentGroup 对象（不生成临时文件）。

```python
def to_information(self) -> EquipmentGroup | None
```

**返回：**

- EquipmentGroup 对象，解析失败返回 None

---

## 使用示例

### 完整解析示例

```python
from comtrade_io.parser.cff import CffFile

# 创建 CffFile 对象
cff_file = CffFile.from_file("dat/example.cff")

# 解析 CFG 配置
configure = cff_file.to_configure()
print(f"站号: {configure.description.header.station}")
print(f"模拟通道: {configure.description.channel_num.analog}")

# 解析 DAT 数据
if configure:
    data = cff_file.to_data_content(configure)
    print(f"数据点: {len(data)}")
    print(f"数据列: {data.shape[1]}")

# 解析 INF 信息（可选）
eg = cff_file.to_information()
if eg:
    print(f"母线: {len(eg.buses)}")
    print(f"线路: {len(eg.lines)}")
    print(f"变压器: {len(eg.transformers)}")
```

### 通过 ComtradeFile 解析

```python
from comtrade_io.parser.comtrade_file import ComtradeFile

# 直接解析 CFF 文件
comtrade = ComtradeFile.from_cff("dat/example.cff")

# 访问数据
print(comtrade.config.description.header.station)
print(comtrade.data.head())
```

---

## 编码处理

CFF 文件读取使用 GBK 编码，同时支持容错处理：

```python
content = path.read_text(encoding="gbk", errors="replace")
```

如果 GBK 解码失败，会使用替换模式避免异常。
