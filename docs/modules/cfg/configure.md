# Configure 类

Configure 是 CFG 配置文件的解析类，负责解析 COMTRADE 标准的配置文件。

## 类定义

```python
class Configure(BaseModel):
    header: Header = Field(description="配置文件头")
    channel_num: ChannelNum = Field(description="通道数量")
    analogs: dict[int, Analog] = Field(default_factory=dict, description="模拟量通道")
    statuses: dict[int, Status] = Field(default_factory=dict, description="数字量通道")
    sampling: Sampling = Field(default_factory=Sampling, description="采样信息")
    start_time: PrecisionTime = Field(default_factory=PrecisionTime, description="故障文件开始时间")
    fault_time: PrecisionTime = Field(default_factory=PrecisionTime, description="故障时间")
    data_type: DataType = Field(default=DataType.BINARY, description="录波文件数据格式")
    timemult: float = Field(default=1.0, description="时标倍率因子")
    time_info: Optional[TimeInfo] = Field(default=None, description="时间信息及与UTC时间关系")
    sampling_time_quality: Optional[SamplingTimeQuality] = Field(default=None, description="采样时间品质")
```

## 属性

| 属性                      | 类型                            | 描述                                      |
|-------------------------|-------------------------------|-----------------------------------------|
| `header`                | Header                        | 配置文件头信息                                 |
| `channel_num`           | ChannelNum                    | 通道数量信息                                  |
| `analogs`               | Dict[int, Analog]             | 模拟量通道字典，key为通道索引                        |
| `statuses`              | Dict[int, Status]             | 状态量通道字典，key为通道索引                        |
| `sampling`              | Sampling                      | 采样信息                                    |
| `start_time`            | PrecisionTime                 | 故障文件开始时间                                |
| `fault_time`            | PrecisionTime                 | 故障时间                                    |
| `data_type`             | DataType                      | 录波文件数据格式（ASCII/BINARY/BINARY32/FLOAT32） |
| `timemult`              | float                         | 时标倍率因子                                  |
| `time_info`             | Optional[TimeInfo]            | 时间信息及与UTC时间关系                           |
| `sampling_time_quality` | Optional[SamplingTimeQuality] | 采样时间品质                                  |

## 方法

### from_str()

从逗号分隔的文本字符串反序列化配置对象。

```python
@classmethod
def from_str(cls, _str: str) -> 'Configure'
```

**参数：**

- `_str`: 包含完整配置文件内容的字符串，以换行符分隔各行

**返回：**

- Configure 对象

**示例：**

```python
cfg_content = """GHBZ,220kV线路故障,2013
288,96A,192D
1,220kV母线_Ua,A,220kV母线U,V,0.007854353,...
...
"""
configure = Configure.from_str(cfg_content)
```

---

### from_file()

从文件名中解析配置文件。

```python
@classmethod
def from_file(cls, file_name: str | Path | ComtradeFile) -> 'Configure|None'
```

**参数：**

- `file_name`: 配置文件路径，可以是字符串、Path对象或ComtradeFile对象

**返回：**

- Configure 对象，文件禁用则返回 None

**示例：**

```python
from pathlib import Path
from comtrade_io.cfg import Configure

configure = Configure.from_file("data/example.cfg")
```

---

### write_file()

将配置写入文件。

```python
def write_file(self, output_file_path: ComtradeFile | Path | str)
```

**参数：**

- `output_file_path`: 输出文件路径

**返回：**

- True 表示成功

**示例：**

```python
configure.write_file("output/new.cfg")
```

---

### get_analog()

按通道的 an(index) 获取模拟量通道。

```python
def get_analog(self, index: int) -> Optional[Analog]
```

**参数：**

- `index`: 通道索引

**返回：**

- Analog 对象，不存在返回 None

---

### get_digital()

按通道的 an(index) 获取数字量通道。

```python
def get_digital(self, index: int) -> Optional[Status]
```

**参数：**

- `index`: 通道索引

**返回：**

- Status 对象，不存在返回 None

---

### get_sampling_segment()

按采样段号获取该采样段的采样频率和结束采样点。

```python
def get_sampling_segment(self, index: int) -> Optional[Segment]
```

**参数：**

- `index`: 采样段号，从1开始

**返回：**

- Segment 对象

---

### \_\_str\_\_()

返回对象的字符串表示形式。

```python
def __str__(self) -> str
```

**返回：**

- 完整的CFG文件内容字符串

**示例：**

```python
cfg_str = str(configure)
print(cfg_str)
```

---

## 配置文件结构

CFG 文件按行包含以下内容：

| 行号           | 内容                     | 说明                 |
|--------------|------------------------|--------------------|
| 1            | 站号, 记录装置ID, 版本         |                    |
| 2            | 总通道数, An, Dn           | 模拟通道数 An, 数字通道数 Dn |
| 3~An+2       | 模拟通道信息                 | 每行一个模拟通道           |
| An+3~An+Dn+2 | 数字通道信息                 | 每行一个数字通道           |
| An+Dn+3      | 采样频率                   |                    |
| An+Dn+4      | 采样率个数                  |                    |
| An+Dn+5~     | 采样段信息                  | 每行一个采样段            |
| 最后           | 开始时间, 触发时间, 数据类型, 时标倍率 |                    |

## 子模块

- [header.py](header.md) - Header 类
- [channel_num.py](channel_num.md) - ChannelNum 类
- [analog_dispose.py](analog_dispose.md) - Analog 类
- [status_dispose.py](status_dispose.md) - Status 类
- [sampling.py](sampling.md) - Sampling 类
- [segment.py](segment.md) - Segment 类
- [time_info.py](time_info.md) - TimeInfo 类
- [sampling_time_quality.py](sampling_time_quality.md) - SamplingTimeQuality 类
- [precision_time.py](precision_time.md) - PrecisionTime 类
