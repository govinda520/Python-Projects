# gtD - YouTube Video Downloader CLI

A simple command-line interface tool for downloading videos using yt-dlp.

## Installation

1. Make sure you have Python 3.7+ installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Basic usage:

```bash
python gtd.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

This will:

1. Show you all available formats for the video
2. Prompt you to select a format code
3. Download the video in your selected format

You can also specify the format directly:

```bash
python gtd.py "https://www.youtube.com/watch?v=VIDEO_ID" --format FORMAT_CODE
```

## Features

- View all available video formats and resolutions
- Select specific format for download
- Progress bar during download
- Support for various video platforms (YouTube, Vimeo, etc.)

## Requirements

- Python 3.7+
- yt-dlp
- typer
- rich


