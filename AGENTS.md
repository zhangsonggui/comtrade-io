# AGENTS.md — comtrade-io

## Workflow Orchestration（工作流编排）

### 1. Plan Node Default（默认计划节点）

- 任何非琐碎任务（3+ 步或架构决策）必须进入计划模式。
- 一旦出现偏差，立即停止并重新规划，不要继续硬推。
- 验证步骤也要使用计划模式，而非仅用于构建。
- 提前写详细规格，减少歧义。

### 2. Subagent Strategy（子代理策略）

- 大量使用子代理，保持主上下文窗口干净。
- 将研究、探索、并行分析全部外包给子代理。
- 复杂问题时，通过子代理投入更多算力。
- 每个子代理只专注一个方向。

### 3. Self-Improvement Loop（自我改进循环）

- 用户任何一次纠正后，立即更新 `tasks/lessons.md` 并记录模式。
- 写规则防止自己重复犯错。
- 无情迭代 lessons，直到错误率下降。
- 每次会话开始时，先复习项目相关 lessons。

### 4. Verification Before Done（完成前验证）

- 绝不在证明它能工作前标记任务完成。
- 必要时对比主分支与修改行为。
- 自问："资深工程师会批准吗？"
- 运行测试、查日志、展示正确性。

### 5. Demand Elegance (Balanced)（要求优雅但平衡）

- 非琐碎改动时暂停："有没有更优雅的方式？"
- 如果修复感觉 hacky："基于我现在的一切知识，实现优雅方案。"
- 简单问题不要过度工程化。
- 每次呈现前先挑战自己的工作。

### 6. Autonomous Bug Fixing（自主 Bug 修复）

- 收到 bug 报告后直接修复，无需用户手把手。
- 指向日志、错误、失败测试，然后解决。
- 用户无需上下文切换。
- 自动修复失败的 CI 测试。

## Task Management（任务管理）

1. **先规划**：将计划写入 `tasks/todo.md`，使用可勾选清单。
2. **验证计划**：实现前先 check-in。
3. **跟踪进度**：每完成一项即标记。
4. **解释变更**：每步提供高层总结。
5. **记录结果**：在 `tasks/todo.md` 末尾添加 review 部分。
6. **捕捉教训**：纠正后更新 `tasks/lessons.md`。

## Core Principles（核心原则）

- **简洁优先**：每次变更尽量简单，只影响最小代码。
- **绝不偷懒**：找到根因，不用临时修复，坚持资深开发者标准。
- **最小影响**：只修改必要部分，避免引入新 bug。

## Entrypoint & Architecture

- Public API: `from comtrade_io import Comtrade` (`src/comtrade_io/__init__.py`)
- `Comtrade.from_file(file_name)` is the primary entry. It uses `ComtradeFile.from_path()` (in
  `parser/comtrade_file.py`) to auto-locate *.cfg/*.dat/*.dmf/*.hdr/*.inf/*.cff/*.dfr files with the same stem.
- Three-layer package structure:
    - `parser/` — raw file readers (`cfg/`, `dat/`, `cff/`, `dfr/`, `inf/`, `dmf/`, `description/`)
    - `model/` — Pydantic v2 models (`Comtrade`, `Configure`, `Description`, `EquipmentGroup`, channel types)
    - `exporters/` — serialization (json, csv, cff, multi-file)
    - `utils/` — logging (loguru), text/numeric helpers
- `ComtradeFile` lives in `parser/comtrade_file.py` (not `model/`). It merged with the former `ComtradeFileParser`.

## Key Model Relationships

- `Configure` has `description: Description` as the single info carrier. No duplicate fields remain (`header`,
  `channel_num`, `sampling`, `file_start_time`, `trigger_time`, `data_type`, `timemult` are accessed via
  `cfg.description.*`).
- `Description.station_name` / `rec_dev_name` / `version` are `@property` delegations to `description.header.*`. Write
  via `description.header.station = ...`.
- `Configure` serialization auto-flattens `description` into top-level JSON (via `model_serializer`). No nesting change
  in output.

## Circular Import Hazard

The import graph has a cycle at:
`parser/comtrade_file.py → parser/cfg/__init__.py → parser/cfg/cfg.py → parser/comtrade_file.py`. Safe at runtime
because:

- `cfg/cfg.py` uses `from __future__ import annotations` + `TYPE_CHECKING` import of `ComtradeFile`
- `ComtradeFile.from_path()` is imported lazily inside `cfg/cfg.py` method bodies
- `parser/comtrade_file.py` lazily imports `DatFile`, `DmfElement`, `Information`, `CffFile`, `DfrFile` inside method
  bodies

**Don't add top-level imports of `ComtradeFile` or `CfgFile` from opposite sides of this cycle.**

## Key Dependencies (from pyproject.toml)

- Python >= 3.10, pandas >= 2.3.3, pydantic >= 2.12.5, numpy >= 1.26.0, loguru >= 0.7.3
- Dev: pytest >= 9.0.2, black >= 26.1.0, setuptools >= 80.9.0, pandas-stubs ~= 2.3.3
- Package under `src/` layout (`[tool.setuptools.packages.find] where = ["src"]`)
- Registers package index: `https://pypi.tuna.tsinghua.edu.cn/simple` (default)

## Commands

```bash
# Run all tests (ignore unrelated text_utils errors)
uv run pytest tests/ -v --tb=short --ignore=tests/comtrade_io/utils/test_text_utils.py

# Single test file
uv run pytest tests/comtrade_io/cfg/test_configure.py -v --tb=short

# Single test
uv run pytest tests/comtrade_io/test_comtrade_file.py::TestFilePath::test_file_path_default_values -v

# Install/sync (includes dev dependencies)
uv sync --extra dev

# Build only
uv sync --no-dev

# Run the CFG↔INF comparison example
uv run python -m comtrade_io.example.main binary_inf
```

## Pre-existing Test Status

- 1 test skipped on Windows: `test_file_path_is_enabled_with_not_readable` (no permission emulation)

历史上曾存在的两个固定失败项已修复：

1. `test_comtrade_model_to_inf_with_parameters` — 已通过
2. `test_parse_float_invalid_raises` — 已通过（测试已改为验证返回 default 值的行为）

## Test Data

- All test data lives under `tests/data/`
- `tests/dat/` is a **junction** → `tests/data/` (test code references `tests/dat/`)
- Standard test files: `binary_1999.*`, `ascii_1999.*`, `ascii_1991.*`, `binary_inf.*`, plus JSON fixture files

## Logging

- Uses `loguru` with `LoguruLoggerWrapper` adapter (compatible with `logging.Logger` interface)
- Configured via `.env` (project root), with fallback to `comtrade_io/.env` (LOG_LEVEL=DEBUG by default in dev)
- `get_logger()` auto-resolves caller module name via frame walking (`sys._getframe`), cached by name
- Do NOT use `logging.getLogger()` — use `from comtrade_io.utils import get_logger`

## Style & Conventions

- Docstrings in Chinese, code comments in Chinese
- Pydantic v2 models use `model_validate()`/`model_dump()` (not v1 `.dict()`/`.parse_obj()`)
- `from __future__ import annotations` used in files with circular import sensitivity
- Enums in `model/type/`, all inherit from a `StrEnum`-like `BaseEnum` base

## Publishing

- GitHub Actions: triggered by `v*` tags → run tests (Python 3.10/3.11/3.12) → build → publish to PyPI
- Workflow: `.github/workflows/publish.yml`

## Notable Refactors

- `DataContent` → `DatFile`: now a `@dataclass` with `config` field. Factory methods `from_file()`, `from_str()`,
  `from_bytes()` return `pd.DataFrame` directly. File renamed from `data_content.py` to `dat.py`.
- `CffFile`: now a `@dataclass`. CFF parser split into `section_splitter.py` (CffSection), `cfg_section.py` (→CfgFile),
  `inf_section.py` (→InfFile), `dat_section.py` (→DatFile).
- `InfFile`: now a `@dataclass`. INF parser split into `text_splitter.py`, `configure_builder.py`,
  `equipment_builder.py`, plus per-section modules (`analog_section.py`, `status_section.py`, etc.).
- `time_formats` is a `tuple` (immutable), not `list`
- `PrecisionTime.time` uses `default_factory=datetime.now` (not `default=datetime.now()')
