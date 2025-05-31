#!/usr/bin/env python3
import typer
import yt_dlp
from rich.console import Console
from rich.table import Table
from typing import Optional, List
from pathlib import Path

app = typer.Typer()
console = Console()

def is_playlist(url: str) -> bool:
    """Check if the URL is a playlist."""
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return 'entries' in info
        except Exception as e:
            console.print(f"[red]Error checking URL: {str(e)}[/red]")
            return False

def get_playlist_info(url: str) -> dict:
    """Get playlist information."""
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown Playlist'),
                'count': len(info.get('entries', [])),
                'entries': info.get('entries', [])
            }
        except Exception as e:
            console.print(f"[red]Error getting playlist info: {str(e)}[/red]")
            return {'title': 'Unknown', 'count': 0, 'entries': []}

def get_video_formats(url: str) -> list:
    """Get available formats for the video."""
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info.get('formats', [])
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            return []

def display_formats(formats: list):
    """Display available formats in a table."""
    table = Table(title="Available Formats")
    table.add_column("Format Code", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Resolution", style="green")
    table.add_column("Extension", style="yellow")
    table.add_column("Size", style="magenta")
    table.add_column("Note", style="red")

    # Sort formats by resolution (height) in descending order
    formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)

    for f in formats:
        format_id = f.get('format_id', 'N/A')
        resolution = f.get('resolution', 'N/A')
        ext = f.get('ext', 'N/A')
        filesize = f.get('filesize', 'N/A')
        if filesize != 'N/A':
            filesize = f"{filesize / (1024*1024):.2f} MB"
        
        # Determine format type
        has_video = f.get('vcodec', 'none') != 'none'
        has_audio = f.get('acodec', 'none') != 'none'
        
        if has_video and has_audio:
            format_type = "Video+Audio"
            note = ""
        elif has_video:
            format_type = "Video Only"
            note = "Will auto-download best audio and merge"
        elif has_audio:
            format_type = "Audio Only"
            note = "Will auto-download best video and merge"
        else:
            continue  # Skip formats with neither video nor audio
        
        table.add_row(format_id, format_type, resolution, ext, filesize, note)
    
    console.print(table)
    console.print("\n[yellow]Note:[/yellow] When selecting video-only or audio-only formats, the program will automatically download and merge the best matching stream.")

def get_download_options() -> dict:
    """Get download options from user."""
    console.print("\n[yellow]Download Options:[/yellow]")
    console.print("1. Download thumbnails")
    console.print("2. Download subtitles")
    console.print("3. Download metadata")
    console.print("4. All of the above")
    console.print("5. None of the above")
    
    choice = typer.prompt("Enter your choice (1-5)", type=int)
    
    options = {
        'thumbnails': False,
        'subtitles': False,
        'metadata': False
    }
    
    if choice == 1:
        options['thumbnails'] = True
    elif choice == 2:
        options['subtitles'] = True
    elif choice == 3:
        options['metadata'] = True
    elif choice == 4:
        options['thumbnails'] = True
        options['subtitles'] = True
        options['metadata'] = True
    
    return options

@app.command()
def download(
    url: str = typer.Argument(..., help="URL of the video or playlist to download"),
    format_id: Optional[str] = typer.Option(None, "--format", "-f", help="Format ID to download"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Output directory for downloads"),
    concurrent_fragments: Optional[int] = typer.Option(None, "--concurrent-fragments", "-N", help="Number of concurrent fragments to download"),
):
    """Download a video or playlist from the given URL."""
    # Check if URL is a playlist
    if is_playlist(url):
        playlist_info = get_playlist_info(url)
        console.print(f"\n[blue]Playlist detected: {playlist_info['title']}[/blue]")
        console.print(f"[blue]Number of videos: {playlist_info['count']}[/blue]")
        
        # Ask user what to do with the playlist
        console.print("\n[yellow]What would you like to do?[/yellow]")
        console.print("1. Download all videos")
        console.print("2. Download specific videos")
        console.print("3. Download a range of videos")
        console.print("4. Exit")
        
        choice = typer.prompt("Enter your choice (1-4)", type=int)
        
        if choice == 1:
            playlist_items = None
        elif choice == 2:
            items = typer.prompt("Enter video numbers (comma-separated, e.g., 1,3,5)")
            playlist_items = items
        elif choice == 3:
            start = typer.prompt("Enter start number", type=int)
            end = typer.prompt("Enter end number", type=int)
            playlist_items = f"{start}-{end}"
        else:
            console.print("[red]Exiting...[/red]")
            return
    else:
        playlist_items = None

    # Get download options
    download_options = get_download_options()

    # Create output directory if specified
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_template = str(Path(output_dir) / "%(title)s.%(ext)s")
    else:
        output_template = "%(title)s.%(ext)s"

    if not format_id:
        # Show available formats
        formats = get_video_formats(url)
        if formats:
            display_formats(formats)
            format_id = typer.prompt("Enter the format code to download")
        else:
            console.print("[red]No formats found for the given URL[/red]")
            return

    # Get format info to determine if it's video-only or audio-only
    formats = get_video_formats(url)
    selected_format = next((f for f in formats if f.get('format_id') == format_id), None)
    
    if selected_format:
        has_video = selected_format.get('vcodec', 'none') != 'none'
        has_audio = selected_format.get('acodec', 'none') != 'none'
        
        if has_video and not has_audio:
            # Video-only format: download best audio and merge
            format_spec = f'{format_id}+bestaudio/best'
            console.print("[yellow]Selected video-only format. Will download best audio and merge automatically.[/yellow]")
        elif has_audio and not has_video:
            # Audio-only format: download best video and merge
            format_spec = f'bestvideo/{format_id}+best'
            console.print("[yellow]Selected audio-only format. Will download best video and merge automatically.[/yellow]")
        else:
            # Combined format or unknown
            format_spec = format_id
    else:
        format_spec = format_id

    # Configure yt-dlp options
    ydl_opts = {
        'format': format_spec,
        'merge_output_format': 'mp4',  # Merge into MP4
        'outtmpl': output_template,
        'progress_hooks': [lambda d: console.print(f"[green]Downloading: {d['_percent_str']} of {d['_total_bytes_str']}[/green]") if d['status'] == 'downloading' else None],
        'writethumbnail': download_options['thumbnails'],
        'writesubtitles': download_options['subtitles'],
        'writeautomaticsub': download_options['subtitles'],
        'writedescription': download_options['metadata'],
        'writeinfojson': download_options['metadata'],
        'writeannotations': download_options['metadata'],
        'playlist_items': playlist_items,
        'ignoreerrors': True,  # Continue on download errors
        'no_warnings': True,
    }

    # Add concurrent fragments if specified
    if concurrent_fragments is not None:
        ydl_opts['concurrent_fragments'] = concurrent_fragments

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        console.print("[green]Download completed successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error during download: {str(e)}[/red]")

if __name__ == "__main__":
    app() 