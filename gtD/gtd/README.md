# Get The Download (GTD)

A powerful command-line tool for downloading videos from YouTube and other supported platforms.

## Features

- Download single videos or entire playlists
- Choose specific video formats and quality
- Download thumbnails, subtitles, and metadata
- Concurrent fragment downloading for faster speeds
- Rich terminal interface with progress bars
- Automatic format selection and merging

## Installation

```bash
pip install gtd
```

## Usage

Basic usage:

```bash
gtd "https://www.youtube.com/watch?v=VIDEO_ID"
```

Download with specific format:

```bash
gtd "https://www.youtube.com/watch?v=VIDEO_ID" --format FORMAT_ID
```

Download to specific directory:

```bash
gtd "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir /path/to/directory
```

Download with concurrent fragments:

```bash
gtd "https://www.youtube.com/watch?v=VIDEO_ID" --concurrent-fragments 4
```

## Development

1. Clone the repository:

```bash
git clone https://github.com/yourusername/gtd.git
cd gtd
```

2. Install development dependencies:

```bash
pip install -e ".[dev]"
```

3. Build the package:

```bash
python -m build
```

4. Test installation:

```bash
pip install dist/gtd-0.1.0-py3-none-any.whl
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
