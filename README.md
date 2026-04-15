# comtrade-io

Python library for loading waveform data from COMTRADE specification CFG/DAT/INF/DMF/HDR file sequences, providing a convenient Pandas DataFrame interface.

## Features

- **Single File API**: Load a COMTRADE instance directly from `Comtrade.from_file(file_name)`
- **Auto-Location**: Automatically locate related files (cfg/dat/dmf/hdr/inf) in the same directory
- **Multi-Format Support**: Supports both ASCII and binary DAT data formats (BINARY, BINARY32, FLOAT32)
- **Data Conversion**: Transform analog data to real values using coefficients (multiply by multiplier plus offset)
- **Data Model**: Supports DMF data model parsing, including power system equipment models (buses, lines, transformers)
- **INF Support**: INF information optionally parsed as `InfInfo` object, preserving original field mappings
- **Read/Write**: Support writing Comtrade objects to CFG/DAT files
- **Pandas Integration**: Returns data as Pandas DataFrame for easy analysis
- **Pure Python**: Lightweight implementation with minimal dependencies

## Dependencies

- Python 3.10+
- pandas >= 2.3.3
- pydantic >= 2.12.5
- openpyxl >= 3.1.5

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
from comtrade_io import Comtrade

# Load COMTRADE file (automatically finds cfg/dat/dmf/hdr/inf files)
wave = Comtrade.from_file("data/D51_RCD_2346_20150917_105253_065_F.cfg")

# Access model methods (without sample data)
wave.get_bus_info("Bus Name")  # Returns model for specified bus name, including voltage and status channels
wave.get_line_info("Line Name")  # Returns model for specified line name, including voltage and status channels
wave.get_transformer_info("Transformer Name")  # Returns model for specified transformer/winding name, including voltage and status channels
wave.get_analog_channel_info("Analog Ch ID")  # Returns model for specified analog channel
wave.get_status_channel_info("Status Ch ID")  # Returns model for specified status channel

# Access DAT data (DataFrame column structure: col 1 is timestamp, col 2+ are analog data, then status data)
data = wave.get_data()  # or wave.dat.data - returns pandas DataFrame with all sample data

# Access specific analog channel data
wave.get_analog_channel(1)  # Get analog channel by index, includes instantaneous sample data
wave.get_status_channel(1)  # Get status channel by index, includes instantaneous sample data

# Access specific line, bus, transformer channel data
wave.get_bus("Bus Name")  # Get bus parameters and associated voltage channels with instantaneous data by bus name
wave.get_line("Line Name")  # Get line parameters and associated current channels with instantaneous data, bus parameters and voltage channel data by line name
wave.get_transformer("Transformer Name")  # Get transformer and winding parameters with associated voltage/current channels and instantaneous data by transformer name


```

## Advanced Usage

### Write Files

```python
# Save Comtrade object to files
wave.save_comtrade("output.cfg", data_type="BINARY")  # Binary format
wave.save_comtrade("output.cfg", data_type="ASCII")  # ASCII format

# Export to JSON file
wave.save_json("output.json")

```


## Project Structure

```
comtrade_io/
├── src/comtrade_io/
│   ├── __init__.py           # Entry point, exports Comtrade class
│   ├── comtrade.py           # Main Comtrade class
│   ├── comtrade_file.py      # File path wrapper
│   ├── cfg/                  # CFG configuration module
│   │   ├── configure.py      # Configuration parser
│   │   ├── analog.py         # Analog channel class
│   │   ├── digital.py        # Digital channel class
│   │   ├── header.py         # File header
│   │   └── sampling.py       # Sampling info
│   ├── dmf/                  # DMF data model module
│   │   ├── comtrade_model.py # Data model main class
│   │   ├── bus.py            # Bus class
│   │   ├── line.py           # Line class
│   │   ├── transformer.py    # Transformer class
│   │   └── ...
│   ├── inf/                  # INF info module
│   ├── data/                 # DAT data parser
│   └── utils/                # Utility functions
├── tests/                    # Test files
└── example/                  # Example scripts
```

## Core Classes

### Comtrade
**Note**: All models in this module are constrained by pydantic. For object to JSON/dict conversion, use pydantic's model_dump_json method.

Main class encapsulating complete COMTRADE file data.

**Main Attributes:**
- `file`: ComtradeFile - contains all file path information
- `cfg`: Configure - CFG configuration information
- `dat`: DataContent - DAT data content
- `buses`: List[Bus] - Bus list
- `lines`: List[Line] - Line list
- `transformers`: List[Transformer] - Transformer list

**Main Methods:**
- `from_file(file_name)`: Load Comtrade from file
- `to_file(filename, data_type)`: Save as COMTRADE file
- `to_json_file(filename)`: Export to JSON
- `get_bus(name)`: Get bus and instantaneous data of associated voltage channels by name
- `get_line(name)`: Get line and instantaneous data of associated bus voltage and current channels by name
- `get_transformer(name)`: Get transformer and instantaneous data of associated voltage/current channels by name
- `get_analog_channel(index)`: Get analog channel and instantaneous data by index
- `get_status_channel(index)`: Get status channel and instantaneous data by index
- `get_bus_info()`: Get bus model by name
- `get_line_info()`: Get line model by name
- `get_transformers_info()`: Get transformer model by name
- `get_analog_channel_info()`: Get analog channel model by name
- `get_status_channel_info()`: Get status channel model by name

### Configure

CFG configuration file parser.

**Main Attributes:**
- `header`: Header information
- `channel_num`: Channel count
- `analogs`: Analog channel dictionary
- `digitals`: Digital channel dictionary
- `sampling`: Sampling information

### ComtradeFile

File path wrapper, auto-locates related files.

**Main Attributes:**
- `cfg_path`: CFG file path
- `dat_path`: DAT file path
- `dmf_path`: DMF file path (optional)
- `hdr_path`: HDR file path (optional)
- `inf_path`: INF file path (optional)

## COMTRADE File Format

Standard format for power system fault recording data:

| File | Required | Description |
|------|----------|-------------|
| .cfg | Yes | Configuration file - defines channels, sampling rate and other metadata |
| .dat | Yes | Data file - contains sample point data |
| .dmf | No | Data model file - defines power system equipment models |
| .hdr | No | Header file - contains recorder device information |
| .inf | No | Information file - contains additional configuration information |

## Module Documentation

Detailed module documentation is available at [docs/modules/README.md](docs/modules/README.md).

### Main Modules

- [Comtrade Class](docs/modules/comtrade.md) - Main entry class, encapsulates complete COMTRADE data
- [Configure (CFG Config)](docs/modules/cfg/configure.md) - CFG configuration file parser
- [DataContent (DAT Data)](docs/modules/data/data_content.md) - DAT data file parser
- [CffFile (CFF Single File)](docs/modules/cff/cff.md) - CFF single file format parser
- [ComtradeFile](docs/modules/comtrade_file.md) - File path wrapper class
- [ComtradeModel](docs/modules/comtrade_model.md) - Data model base class
- [Information (INF Info)](docs/modules/inf/information.md) - INF information file parser

## License

MIT License

## Version History

- 0.1.0: Initial release - basic COMTRADE read/write support
- 0.1.1: Added support for DMF data model files
- 0.1.2: Same as version 0.1.1
- 0.1.3: Added support for CFF single file and INF information files
