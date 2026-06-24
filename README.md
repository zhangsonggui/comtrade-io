# comtrade-io

Python library for loading and writing waveform data from COMTRADE specification files (CFG/DAT/CFF/DFR/INF/DMF/HDR),
providing a convenient Pandas DataFrame interface.

## Features

- **Single File API**: Load a COMTRADE instance directly from `ComtradeFile.from_file(file_name)`
- **Multi-Format Reading**: Supports CFG+DAT (multi-file), CFF single file, and DFR (WNDR) format
- **Auto-Location**: Automatically locate related files (cfg/dat/dmf/hdr/inf) in the same directory
- **Data Formats**: Supports ASCII and binary DAT data (BINARY, BINARY32, FLOAT32)
- **Data Conversion**: Transform analog data to real values using coefficients
- **Equipment Model**: Parse DMF data model and INF information into power system equipment (buses, lines, transformers)
- **Multiple Export Formats**: Export to multi-file (CFG+DAT), CFF single file, JSON, and CSV formats
- **Write Support**: Save Comtrade objects to CFG/DAT/INF/DMF/CFF files
- **Pandas Integration**: Returns data as Pandas DataFrame for easy analysis
- **Pure Python**: Lightweight implementation with minimal dependencies

## Dependencies

- Python 3.10+
- pandas >= 2.3.3
- numpy >= 1.26.0
- pydantic >= 2.12.5
- loguru >= 0.7.3

## Installation

### Install from PyPI

```bash
# Using uv
uv add comtrade-io

# Using pip
pip install comtrade-io

```

### Install from source

```bash
# Clone the repository
git clone https://github.com/zhangsonggui/comtrade-io.git
git clone https://gitee.com/zhangsonggui/comtrade-io.git
# Install dependencies
cd comtrade-io
uv sync
```


## Quick Start

```python
from comtrade_io.parser.comtrade_file import ComtradeFile

# Load COMTRADE file (automatically finds cfg/dat/dmf/hdr/inf files)
wave = ComtradeFile.from_file("tests/data/binary_1999.cfg")

# Access configuration
wave.config.description.header.station      # Station name
wave.config.description.header.recorder     # Recording device ID
wave.channel_num.analog                      # Analog channel count
wave.channel_num.status                      # Status channel count
wave.sampling.segments[0].samp               # Sample rate (Hz)

# Access channel definitions
wave.analogs[1]                               # Analog channel by index
wave.statuses[1]                              # Status channel by index

# Access equipment model (from DMF/INF)
wave.get_bus_info("Bus Name")                 # Bus model by name
wave.get_line_info("Line Name")               # Line model by name
wave.get_transformer_info("Transformer Name") # Transformer model by name

# Access DAT data (DataFrame: col 1 = timestamp, col 2+ = analog then status)
data = wave.get_data()

# Access specific channel data
wave.get_analog_channel(1)                    # Analog channel with sample data
wave.get_status_channel(1)                    # Status channel with sample data

# Access equipment with instantaneous data
wave.get_bus("Bus Name")                      # Bus with voltage channel data
wave.get_line("Line Name")                    # Line with current/voltage data
wave.get_transformer("Transformer Name")      # Transformer with winding data
```

## Advanced Usage

### Multi-Format Loading

```python
# From CFF single file
cf = ComtradeFile.from_cff("recording.cff")

# From DFR (WNDR) file
cf = ComtradeFile.from_dfr("recording.dfr")
```

### Export Files

```python
# Save as multi-file (CFG+DAT+INF+DMF) - default
wave.save_comtrade("output.cfg")

# Save as CFF single file
wave.save_comtrade("output.cff", format="cff")

# Export to JSON
wave.save_comtrade("output.json", format="json")

# Export to CSV
wave.save_comtrade("output.csv", format="csv")

# Choose data format
wave.save_comtrade("output.cfg", data_format="ASCII")   # ASCII
wave.save_comtrade("output.cfg", data_format="BINARY")   # Binary (default)
wave.save_comtrade("output.cfg", data_format="BINARY32") # 32-bit binary
wave.save_comtrade("output.cfg", data_format="FLOAT32")  # 32-bit float

# Direct JSON export
wave.save_json("output.json")
```

### Write Individual Files

```python
wave.write_cfg("output.cfg")    # Write CFG configuration
wave.write_dmf("output.dmf")    # Write DMF data model
wave.write_inf("output.inf")    # Write INF information
```

### CFF Single File Format

```python
from comtrade_io.parser.cff import CffFile

cff = CffFile.from_file("recording.cff")
cfg = cff.to_configure()             # Parse CFG section
data = cff.to_data_content(cfg)      # Parse DAT section
inf = cff.to_information()           # Parse INF section (optional)
```

## Project Structure

```
comtrade_io/
├── src/comtrade_io/
│   ├── __init__.py               # Entry point, exports Comtrade class
│   ├── model/                    # Data models (Pydantic)
│   │   ├── comtrade.py           # Main Comtrade class
│   │   ├── configure/            # CFG configuration model
│   │   ├── description/          # File description (header, sampling, time)
│   │   ├── channel/              # Analog and status channel models
│   │   ├── equipment/            # Power system equipment (Bus, Line, Transformer)
│   │   └── type/                 # Enumerations and type definitions
│   ├── parser/                   # File parsers
│   │   ├── comtrade_file.py      # ComtradeFile path wrapper
│   │   ├── cfg/                  # CFG configuration parser
│   │   ├── dat/                  # DAT data parser (ASCII/Binary)
│   │   ├── cff/                  # CFF single file parser
│   │   ├── dfr/                  # DFR (WNDR) format parser
│   │   ├── dmf/                  # DMF data model parser (XML)
│   │   ├── inf/                  # INF information file parser
│   │   └── description/         # Parser helpers (time, header, sampling)
│   ├── exporters/               # Export functionality
│   │   ├── cff_exporter.py       # CFF single file export
│   │   ├── csv_exporter.py       # CSV export
│   │   ├── json_exporter.py      # JSON export
│   │   ├── multi_file_exporter.py # Multi-file (CFG+DAT) export
│   │   └── decorators.py         # @export_format decorator
│   └── utils/                    # Utility functions
│       ├── file_path.py          # FilePath smart path class
│       ├── logging.py            # Loguru-based logging
│       ├── text_utils.py         # Text splitting utilities
│       └── numeric_utils.py      # Numeric parsing utilities
├── tests/                        # Test files
└── docs/                         # Documentation
```

## Core Classes

### Comtrade

Main class encapsulating complete COMTRADE file data.

**Attributes:**

- `config`: Configure - CFG configuration (header, channel definitions, sampling)
- `data`: pd.DataFrame | None - Sample data
- `buses`: List[Bus] - Bus list (from DMF/INF)
- `lines`: List[Line] - Line list (from DMF/INF)
- `transformers`: List[Transformer] - Transformer list (from DMF/INF)

**Properties (delegated to `config`):**

- `analogs` / `statuses` - Channel dictionaries
- `channel_num` - Channel count
- `sampling` - Sampling information
- `start_time` / `fault_time` - Time information
- `data_type` - Data format
- `header` - File header

**Key Methods:**

- `get_data()`: Return sample data as DataFrame
- `get_bus(name)`: Get bus with voltage channel data
- `get_line(name)`: Get line with current/voltage channel data
- `get_transformer(name)`: Get transformer with winding data
- `get_analog_channel(index)`: Get analog channel with data
- `get_status_channel(index)`: Get status channel with data
- `save_comtrade(path, format, data_format)`: Export to file
- `save_json(path)`: Export to JSON
- `write_cfg(path)` / `write_dmf(path)` / `write_inf(path)`: Write individual files

### Configure

CFG configuration model.

**Attributes:**

- `description`: Description - Header, channel count, sampling, time
- `analogs`: Dict[int, Analog] - Analog channel definitions
- `statuses`: Dict[int, Status] - Status channel definitions

### ComtradeFile

File path wrapper with auto-location and format detection.

**Supported Formats:**

- **Multi-file**: CFG+DAT (traditional), optionally DMF, INF, HDR
- **CFF single file**: `.cff` combines CFG, INF, DAT in one file
- **DFR**: `.dfr` WNDR proprietary single file format

**Key Methods:**

- `from_path(path)`: Create from any COMTRADE file path
- `from_file(path)`: Parse and return a `Comtrade` instance

### Equipment Model

- **Bus**: Voltage channels, status/alarm channels
- **Line**: Current branches, bus references, impedance parameters
- **Transformer**: Windings with individual voltage/current channels
- **EquipmentGroup**: Aggregate container for equipment + channel overrides

## COMTRADE File Format

Standard format for power system fault recording data:

| File | Required | Description                                                             |
|------|----------|-------------------------------------------------------------------------|
| .cfg | Yes      | Configuration file - defines channels, sampling rate and other metadata |
| .dat | Yes      | Data file - contains sample point data                                  |
| .dmf | No       | Data model file (XML) - defines power system equipment models           |
| .hdr | No       | Header file - contains recorder device information                      |
| .inf | No       | Information file - contains additional configuration in INI-like format |
| .cff | No       | CFF single file format - combines CFG, INF, DAT into one file           |
| .dfr | No       | DFR (WNDR) proprietary single file format                               |

## Module Documentation

Detailed module documentation is available at [docs/modules/README.md](docs/modules/README.md).

### Main Modules

- [Comtrade Class](docs/modules/comtrade.md) - Main entry class
- [Configure (CFG Config)](docs/modules/cfg/configure.md) - CFG configuration parser
- [DataContent (DAT Data)](docs/modules/data/data_content.md) - DAT data file parser
- [CffFile (CFF Single File)](docs/modules/cff/cff.md) - CFF single file format parser
- [ComtradeFile](docs/modules/comtrade_file.md) - File path wrapper class
- [Information (INF Info)](docs/modules/inf/information.md) - INF information file parser

## License

MIT License

## Version History

- 0.1.0: Initial release - basic COMTRADE read/write support
- 0.1.1: Added support for DMF data model files
- 0.1.2: Same as version 0.1.1
- 0.1.3: Added support for CFF single file and INF information files
- **0.2.0**: Major refactoring and new features
    - Package restructured into `model/`, `parser/`, `exporters/`, `utils/` modules
    - Comtrade model refactored: `cfg` → `config`, equipment model integration
    - New export system with `@export_format` decorator (multi-file, CFF, JSON, CSV)
    - CFF single file format parser and writer
    - DFR (WNDR) format parser
    - Full INF file parsing with equipment group generation
    - DMF data model enhancements (Bus, Line, Transformer with windings)
    - `FilePath` smart path class with file status detection
    - Logging migrated to loguru
    - All models migrated to Pydantic v2
    - Improved GBK/UTF-8 encoding handling
- **0.2.1**: Enhanced DFR format support and bug fixes
    - Added support for multiple DFR device types (2704V042, 2704V072)
    - Dynamic DFR frame size calculation based on channel configuration
    - Fixed analog scaling to physical instantaneous values in data
    - Fixed ASCII export by reversing physical values back to ADC counts
    - Fixed INF/DMF export crash on None buses/lines/transformers
    - DFR parser refactored into modular sub-modules (wndr_section, binary_section, converter)
    - Batch DFR→COMTRADE conversion script added
- **0.3.0**: Code cleanup and internal refactoring
    - Removed shebang and coding headers from all source files
    - Fixed `version` variable shadowing in `__init__.py`
    - Replaced unnecessary f-strings with plain strings
    - Moved `.env` to project root with `.env.example` template
    - Converted `dev-dependencies` to standard `[project.optional-dependencies] dev`
    - Removed unused `openpyxl` dependency
    - Eliminated post-class monkey-patching; `@export_format` decorator inlined to class definition
    - Added full type annotations on all `Comtrade` delegation properties
    - New CI/CD workflow (`.github/workflows/publish.yml`) with multi-Python-version test matrix
    - Converted all 357 internal absolute imports to relative imports (95 files)
    - Cleaned up hardcoded local paths in `compatibility.md`
