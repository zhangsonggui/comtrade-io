# InfFile 类（原 Information）

`Information` 类在 0.3.0 重构中重命名为 `InfFile`，解析 INI 格式的 INF 信息文件。

## 类定义

```python
@dataclass
class InfFile:
    ...
```

## 主要方法

### from_file()

从文件读取并解析 INF 内容。

```python
@classmethod
def from_file(cls, file_name: str | Path) -> InfFile | None
```

**参数：**

- `file_name`: 文件路径

**返回：**

- InfFile 对象，文件不存在返回 None

---

### from_str()

从字符串解析 INF 内容。

```python
@classmethod
def from_str(cls, content: str) -> InfFile
```

**参数：**

- `content`: INF 内容字符串

**返回：**

- InfFile 对象

---

### to_equipment_group()

将 INF 解析结果转换为 EquipmentGroup 对象。

```python
def to_equipment_group(self) -> EquipmentGroup | None
```

**返回：**

- EquipmentGroup 对象（包含设备拓扑和通道信息），解析失败返回 None

---

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

- [Comtrade](../comtrade.md) - 主类
- [CffFile](../cff/cff.md) - CFF 单文件格式（INF 解析由 CffFile 内部调用）
