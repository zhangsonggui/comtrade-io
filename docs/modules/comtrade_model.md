# ComtradeModel（已合并至 Comtrade）

ComtradeModel 作为独立基类已合并到 [Comtrade](comtrade.md) 中。

## 变更说明

在 0.2.0 重构中，`ComtradeModel` 的功能被直接合并到 `Comtrade` 类：

- **设备模型**（`buses`、`lines`、`transformers`）：现在是 `Comtrade` 的直接字段
- **通道字典**（`analogs`、`statuses`）：通过委托属性访问 `config.analogs` / `config.statuses`
- **描述信息**（`description`）：通过 `config.description` 访问
- **查询方法**（`get_bus_info()`、`get_line_info()`、`get_transformer_info()` 等）：直接在 `Comtrade` 上定义

## 数据来源

设备模型可以从以下来源解析：

- DMF 文件（XML 格式）
- INF 文件（INI 格式）
- 从 CFG 通道信息自动推断（通过 `CfgToEquipment`）

详情请参见 [Comtrade](comtrade.md)。
