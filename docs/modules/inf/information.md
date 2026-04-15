# Information 类

Information 是 INF 信息文件的解析类，负责解析 INI 格式的信息文件。

## 类定义

```python
class Information(BaseModel):
    record_info: Optional[list] = Field(default_factory=list, description="录波记录信息")
    file_description: Optional[Description] = Field(default_factory=Description, description="文件描述信息")
    analog_channels: Optional[dict[int, Analog]] = Field(default_factory=dict, description="模拟通道信息")
    status_channels: Optional[dict[int, Status]] = Field(default_factory=dict, description="状态量通道信息")
    buses: Optional[list[Bus]] = Field(default_factory=list, description="母线信息")
    lines: Optional[list[Line]] = Field(default_factory=list, description="线路信息")
    transformers: Optional[list[Transformer]] = Field(default_factory=list, description="变压器信息")
```

## 方法

### from_file()

从文件读取并解析 INF 内容。

```python
@classmethod
def from_file(cls, file_name: str | Path) -> 'ComtradeModel | None'
```

**参数：**

- `file_name`: 文件路径

**返回：**

- ComtradeModel 对象，文件不存在返回 None

---

### from_str()

从字符串解析 INF 内容。

```python
@classmethod
def from_str(cls, content: str) -> 'ComtradeModel'
```

**参数：**

- `content`: INF 内容字符串

**返回：**

- ComtradeModel 对象

## INF 文件格式

INF 文件使用 INI 格式，使用方括号标记节：

```ini
[Public Record_Information]
Source=录波源
Location=录波位置

[Public File_Description]
Station_Name=站名
Recording_Device_ID=装置ID

[Public Analog_Channel_#1]
Channel_ID=Ia
Phase_ID=A
Channel_Units=A
...

[ZYHD Bus_#1]
DEV_ID=,Bus1
...
```

## 相关模块

- [ComtradeModel](../comtrade_model.md) - 数据模型基类
