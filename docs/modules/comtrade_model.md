# ComtradeModel 类

ComtradeModel 是数据模型基类，包含电力系统设备模型和通道信息。

## 类定义

```python
class ComtradeModel(BaseModel):
    description: Description = Field(default_factory=Description, description="描述信息")
    buses: list[Bus] = Field(default_factory=list, description="母线列表")
    lines: list[Line] = Field(default_factory=list, description="线路列表")
    transformers: list[Transformer] = Field(default_factory=list, description="变压器列表")
    analogs: dict[int, Analog] = Field(default_factory=dict, description="模拟量通道")
    statuses: dict[int, Status] = Field(default_factory=dict, description="状态量通道")
```

## 属性

| 属性             | 类型                | 描述      |
|----------------|-------------------|---------|
| `description`  | Description       | 文件描述信息  |
| `buses`        | List[Bus]         | 母线列表    |
| `lines`        | List[Line]        | 线路列表    |
| `transformers` | List[Transformer] | 变压器列表   |
| `analogs`      | Dict[int, Analog] | 模拟量通道字典 |
| `statuses`     | Dict[int, Status] | 状态量通道字典 |

## 方法

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

## 继承类

- [Comtrade](comtrade.md) - 主类，继承自 ComtradeModel

## 数据来源

ComtradeModel 可以从以下来源解析：

- DMF 文件（XML 格式）
- INF 文件（INI 格式）
- 从 CFG 通道信息自动生成
