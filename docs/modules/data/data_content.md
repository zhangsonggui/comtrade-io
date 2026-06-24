# DatFile（原 DataContent）

`DataContent` 已在 0.3.0 重构中重命名为 `DatFile`，并从 Pydantic BaseModel 改为 `@dataclass`。

## 类定义

```python
@dataclass
class DatFile:
    config: Configure
```

## 工厂方法

DatFile 的工厂方法直接返回 `pd.DataFrame`，不再返回 DatFile 实例。

### from_file()

从文件读取 DAT 数据。

```python
@classmethod
def from_file(cls, config: Configure, file_name: str | Path | None) -> pd.DataFrame | None
```

**参数：**

- `config`: Configure 配置对象（提供通道数量、数据格式等信息）
- `file_name`: DAT 文件路径

**返回：**

- pandas DataFrame，读取失败返回 None

---

### from_str()

从 ASCII 字符串读取 DAT 数据。

```python
@classmethod
def from_str(cls, config: Configure, dat_text: str) -> pd.DataFrame | None
```

---

### from_bytes()

从二进制字节数据读取 DAT 数据。

```python
@classmethod
def from_bytes(cls, config: Configure, dat_bytes: bytes) -> pd.DataFrame | None
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

## 数据转换

DatFile 会自动将模拟量的原始采样值转换为真实值：

```
真实值 = 原始值 × multiplier + offset
```

这个转换在数据解析过程中使用向量化操作完成，保证了性能。

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
