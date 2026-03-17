# comtrade-io

Python library for loading waveform data from COMTRADE specification CFG/DAT/INF/DMF/HDR file sequences, providing a convenient Pandas DataFrame interface.

## Features

- **Single File API**: Load a COMTRADE instance directly from `Comtrade.from_file(file_name)`
- **Auto-Location**: Automatically locate related files (cfg/dat/dmf/hdr/inf) in the same directory
- **Multi-Format Support**: Supports both ASCII and binary DAT data formats (including BINARY, BINARY32, FLOAT32)
- **Data Conversion**: Transform analog data to real values using coefficients (multiply by multiplier plus offset)
- **Data Model**: Supports DMF data model parsing, including power system equipment models such as buses, lines, and transformers
- **INF Support**: INF information optionally parsed as `InfInfo` object, preserving original field mappings for extensibility
- **Read/Write**: Support writing Comtrade objects to CFG/DAT files
- **Lightweight**: Pure Python implementation, depends on Pandas/Numpy/Pydantic

## Dependencies

- Python 3.10+
- pandas >= 2.3.3
- pydantic >= 2.12.5
- openpyxl >= 3.1.5
- path

## Installation

```bash
# Using uv
uv sync

# Install dev dependencies
uv pip install -e .[dev]
```

## Quick Start

```python
from comtrade_io import Comtrade

# Assuming D51_RCD_2346_20150917_105253_065_F.cfg exists in data directory
c = Comtrade.from_file("data/D51_RCD_2346_20150917_105253_065_F.cfg")

# Access CFG file content
c.cfg.header  # CFG file header config, including substation name, recorder name, recorder version
c.cfg.analogs # CFG file analog channel array, collection of Analog objects

# Access DAT file content
c.data  # 2D array, each row contains one sample point info
        # First column is sample point number, second column is relative time
        # Starting from third column are instantaneous values of each analog channel at that sample point
        # After all analogs, starting from column c.cfg.channel_num.analog + 2 are instantaneous values of digital channels
```

## Advanced Usage

### Data Model (DMF)

```python
# Access power system data model
c.buses           # List of buses
c.lines           # List of lines
c.transformers    # List of transformers
c.analog_channels # Analog channel dictionary
c.status_channels # Status channel dictionary

# Get equipment by name
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
c.to_file("output.cfg", data_type="BINARY")  # Save as binary format
c.to_file("output.cfg", data_type="ASCII")   # Save as ASCII format

# Export to JSON
c.to_json_file("output.json")

# Export to dictionary
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
│   ├── __init__.py              # Entry file, exports Comtrade class
│   ├── model/
│   │   ├── comtrade.py          # Comtrade main class
│   │   ├── comtrade_file.py     # File path wrapper class
│   │   ├── cfg/                 # CFG configuration module
│   │   │   ├── configure.py     # Configuration parser main class
│   │   │   ├── analog.py        # Analog channel class
│   │   │   ├── digital.py       # Digital channel class
│   │   │   ├── header.py       # File header class
│   │   │   ├── sampling.py      # Sampling info class
│   │   │   └── ...
│   │   ├── dmf/                 # DMF data model module
│   │   │   ├── comtrade_model.py # Data model main class
│   │   │   ├── bus.py           # Bus class
│   │   │   ├── line.py          # Line class
│   │   │   ├── transformer.py   # Transformer class
│   │   │   ├── analog_channel.py # Analog channel class
│   │   │   ├── status_channel.py # Status channel class
│   │   │   └── ...
│   │   ├── inf/                 # INF info module
│   │   └── type/                # Type definition module
│   ├── data/
│   │   └── data_content.py      # DAT data parser
│   └── utils/                   # Utility module
├── tests/                       # Test files
└── data/                        # Sample data
```

## Core Classes

### Comtrade

Main class encapsulating complete COMTRADE file data.

**Main Attributes:**
- `file`: ComtradeFile object, contains all file path information
- `cfg`: Configure object, contains CFG configuration information
- `data`: Pandas DataFrame, contains DAT data
- `buses`: List of buses
- `lines`: List of lines
- `transformers`: List of transformers

**Main Methods:**
- `from_file(file_name)`: Load Comtrade object from file
- `to_file(filename, data_type)`: Save as COMTRADE file
- `to_json_file(filename)`: Export to JSON
- `get_bus(name)`: Get bus by name
- `get_line(name)`: Get line by name
- `get_transformer(name)`: Get transformer by name
- `get_analog_channel(index)`: Get analog channel by index
- `get_status_channel(index)`: Get status channel by index

### Configure

CFG configuration file parser class.

**Main Attributes:**
- `header`: File header information
- `channel_num`: Channel count
- `analogs`: Analog channel dictionary
- `digitals`: Digital channel dictionary
- `sampling`: Sampling information
- `data_type`: Data format type

### ComtradeFile

File path wrapper class, automatically locates related files in the same directory.

**Main Attributes:**
- `cfg_path`: CFG file path
- `dat_path`: DAT file path
- `dmf_path`: DMF file path (optional)
- `hdr_path`: HDR file path (optional)
- `inf_path`: INF file path (optional)

## COMTRADE File Format

COMTRADE is the standard format for power system fault recording data, containing the following files:

| File | Required | Description |
|------|----------|-------------|
| .cfg | Yes | Configuration file, defines channels, sampling rate and other metadata |
| .dat | Yes | Data file, contains sample point data |
| .dmf | No | Data model file, defines power system equipment models |
| .hdr | No | Header file, contains recorder equipment information |
| .inf | No | Information file, contains additional configuration information |

## Sample Data

The `data/` directory contains sample data files (CFG, DAT, INF, etc.) for testing and learning.

## Contribution and License

- License: MIT
- Contributing: For help, please submit issue/PR (please follow the repository's existing style)

## Version History

- 0.1.0: Initial version, supports basic read/write functionality for COMTRADE files
