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

```bash
# Using uv
uv sync

# Or install directly
pip install comtrade_io
```

## Quick Start

```python
from comtrade_io import Comtrade

# Load COMTRADE file (automatically finds cfg/dat/dmf/hdr/inf files)
c = Comtrade.from_file("data/D51_RCD_2346_20150917_105253_065_F.cfg")

# Access CFG configuration
c.cfg.header  # Substation name, recorder name, version
c.cfg.analogs  # Analog channel dictionary
c.cfg.digitals  # Digital channel dictionary

# Access DAT data as DataFrame
c.get_data()  # Returns pandas DataFrame with all sample data

# Access specific analog channel data
c.get_analog_channel(1)  # Get analog channel by index
```

## Advanced Usage

### Data Model (DMF)

```python
# Access power system data model
c.buses  # List of buses
c.lines  # List of lines
c.transformers  # List of transformers
c.analog_channels  # Analog channel dictionary
c.status_channels  # Status channel dictionary

# Get equipment by name (loads channel data automatically)
bus = c.get_bus("Bus Name")
line = c.get_line("Line Name")
transformer = c.get_transformer("Transformer Name")

# Get channel by index
analog = c.get_analog_channel(1)
status = c.get_status_channel(1)
```

### Write Files

```python
# Save Comtrade object to files
c.to_file("output.cfg", data_type="BINARY")  # Binary format
c.to_file("output.cfg", data_type="ASCII")    # ASCII format

# Export to JSON
c.to_json_file("output.json")

# Export to dictionary (pickle)
c.to_dict_file("output.pkl")
```

### Configuration Operations

```python
# Get analog channel
analog = c.cfg.get_analog(1)

# Get digital channel
digital = c.cfg.get_digital(1)

# Get sampling rate info
nrate = c.cfg.get_sampling_nrate(1)
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
- `get_bus(name)`: Get bus by name
- `get_line(name)`: Get line by name
- `get_transformer(name)`: Get transformer by name
- `get_analog_channel(index)`: Get analog channel by index
- `get_status_channel(index)`: Get status channel by index

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
| .cfg | Yes | Configuration file - channels, sampling rate |
| .dat | Yes | Data file - sample point data |
| .dmf | No | Data model file - equipment models |
| .hdr | No | Header file - recorder info |
| .inf | No | Information file - additional config |

## License

MIT License

## Version History

- 0.1.0: Initial release - basic COMTRADE read/write support