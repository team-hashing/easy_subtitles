# Easy Subtitles

Easy Subtitles is a very opinionated Python tool that automatically generates and burns subtitles into videos using OpenAI's Whisper for accurate speech-to-text transcription. It supports multiple display modes including word-by-word highlighting and reading modes with precise timing.

## Features

- **AI-Powered Transcription**: Uses OpenAI Whisper for accurate speech-to-text conversion
- **Multiple Display Modes**: 
  - Standard chunked subtitles
  - Word-by-word display
  - Reading mode with cumulative highlighting
- **Precise Timing**: Word-level timestamps for accurate audio synchronization
- **Customizable Styling**: Font, size, colors, and borders
- **Professional Output**: ASS/SRT subtitle formats with video burning
- **Multi-Language Support**: Supports multiple languages via Whisper
- **Flexible Input**: Works with video files or existing subtitle files

## Installation

### Prerequisites

- **Python 3.10+**
- **FFmpeg** (for video processing)

### Option 1: Install with uv (Recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url>
cd easy_subtitles

# Install with uv (automatically creates virtual environment)
uv sync
```

### Option 2: Manual Installation

```bash
# Clone the repository
git clone <repository-url>
cd easy_subtitles

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# OR
pip install openai-whisper
```

### Install FFmpeg

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Linux (Fedora/RHEL):
```bash
sudo dnf install ffmpeg
```

#### macOS:
```bash
brew install ffmpeg
```

#### Windows:
Download from [FFmpeg official website](https://ffmpeg.org/download.html) or use:
```bash
choco install ffmpeg  # With Chocolatey
# OR
winget install ffmpeg  # With winget
```

## Usage

### Basic Usage

```bash
# Generate and burn subtitles into video
python main.py input.mp4

# With uv
uv run python main.py input.mp4
```

### Command Line Options

```bash
python main.py [input_video] [OPTIONS]
```

#### Required Arguments
- `input`: Path to input video file

#### Optional Arguments

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-o, --output` | string | `{input}_subtitled.mp4` | Output video file path |
| `-s, --srt` | string | `{input}.srt` | Subtitle file path |
| `-i, --input_srt` | string | - | Use existing subtitle file (.srt) or text file (.txt) as script |

## Display Modes

### 1. Standard Mode (Default)
| `--only_srt` | flag | `False` | Generate only subtitle files, don't burn into video |
| `--lang` | string | `es` | Language for transcription (en, es, fr, etc.) |
| `--font` | string | `Arial` | Font family for subtitles |
| `--size` | integer | `36` | Font size in points |
| `--color` | string | `white` | Text color (white, black, red, green, blue, yellow, cyan, magenta) |
| `--max_chars` | integer | `30` | Maximum characters per subtitle line |
| `--max_duration` | float | `3.0` | Maximum duration per subtitle in seconds |
| `--skip_transcribe` | flag | `False` | Skip transcription (use with existing subtitles) |

#### Display Modes

| Option | Description |
|--------|-------------|
| `--word` | **Word-by-word mode**: Each word appears individually with precise timing |
| `--read` | **Reading mode**: Cumulative word highlighting with color progression |
| `--read-color` | string | `yellow` | Color for highlighted words in reading mode |

## Display Modes

### 1. Standard Mode (Default)
```bash
python main.py video.mp4
```
- Displays subtitles in chunks (respecting `max_chars` and `max_duration`)
- Traditional subtitle experience
- Best for general viewing

### 2. Word-by-Word Mode
```bash
python main.py video.mp4 --word
```
- Each word appears individually
- Perfect timing synchronization with speech
- Great for language learning
- Uses Whisper's word-level timestamps for accuracy

### 3. Reading Mode (Advanced)
```bash
python main.py video.mp4 --read --read-color yellow
```
- **Cumulative highlighting**: Words turn yellow as they're spoken
- **Persistent display**: Subtitles never disappear, maintaining reading context
- **Perfect for comprehension**: See full sentences while tracking progress
- **Customizable colors**: Choose highlight color

## Examples

### Language Learning Setup
```bash
# English content with word-by-word for precise learning
python main.py lesson.mp4 --lang en --word --size 42 --color white
```

### Reading Comprehension Mode
```bash
# Spanish content with reading mode and custom highlighting
python main.py podcast.mp4 --lang es --read --read-color cyan --size 40
```

### Subtitle-Only Generation
```bash
# Generate subtitles without burning into video
python main.py interview.mp4 --only_srt --lang en
```

### Using Existing Subtitles
```bash
# Apply word-by-word mode to existing subtitle file
python main.py video.mp4 --input_srt existing.srt --word
```

### Custom Styling
```bash
# Large, red subtitles with custom font
python main.py video.mp4 --font "Helvetica" --size 48 --color red
```

## Text File Script Support

You can use any text file as a script for your subtitles. The tool will align the text content with the spoken audio using Whisper's word-level timestamps.

### How it works:
- Provide a text file with the script content using `-i`
- Whisper transcribes the audio with precise timing
- The tool aligns your text with the spoken words
- Maintains exact timing while using your script's wording

### Example:
```bash
# Create a script file
echo "Remember the hotel sector in Spain. The hotel chain has increased revenue." > script.txt

# Generate subtitles using the script
python main.py video.mp4 -i script.txt --read
```

### Alignment Features:
- Handles minor differences between script and speech
- Falls back to standard transcription if alignment fails
- Provides warnings about alignment quality
- Works with all display modes (--read, --word, etc.)

## Styling Options

### Available Colors
- `white` (default)
- `black`
- `red`
- `green` 
- `blue`
- `yellow`
- `cyan`
- `magenta`

### Font Considerations
- Default: `Arial` (universally supported)
- System fonts: `Helvetica`, `Times`, `Courier`, etc.
- Ensure fonts are installed on your system for best results

## Output Files

### Subtitle Files Generated
- **SRT Format**: `input.srt` - Standard subtitle format
- **ASS Format**: `input.ass` - Advanced styling (for --read mode)

### Video Output
- **MP4 Format**: `input_subtitled.mp4` - Original video with burned subtitles
- Preserves original video quality and audio

## Performance Tips

### Faster Processing
```bash
# Skip video output for quick subtitle generation
python main.py video.mp4 --only_srt

# Use existing audio extraction
python main.py video.mp4 --skip_transcribe --input_srt existing.srt
```

### GPU Acceleration
- Whisper automatically uses GPU if available (CUDA/Metal)
- No additional configuration needed

## Troubleshooting

### Common Issues

#### "FFmpeg not found"
```bash
# Install FFmpeg (see installation section above)
which ffmpeg  # Verify installation
```

#### "CUDA warnings"
- Normal on CPU-only systems
- Whisper will fallback to CPU processing
- Performance will be slower but functional

#### "Memory errors with large videos"
```bash
# Process audio only first
python main.py large_video.mp4 --only_srt
# Then burn subtitles
python main.py large_video.mp4 --input_srt large_video.srt
```

#### "Subtitle timing issues"
- Ensure input video has clear audio
- Try different language settings with `--lang`
- Use `--read` mode for better sync visualization

### Debug Mode
```bash
# Enable verbose output for debugging
python main.py video.mp4 --lang en 2>&1 | tee debug.log
```

## Advanced Features

### Whisper Word-Level Timestamps
- Automatically enabled for `--word` and `--read` modes
- Provides millisecond-accurate word timing
- Dramatically improves synchronization accuracy

### Subtitle Persistence (Reading Mode)
- Subtitles extend until next word starts
- No gaps or disappearing text
- Maintains reading context throughout video

### Professional ASS Styling
- Black borders for readability
- Configurable background colors
- Proper subtitle positioning

## File Format Support

### Input Video Formats
- MP4, AVI, MOV, MKV, WMV
- Any format supported by FFmpeg

### Input Audio Languages
- All languages supported by OpenAI Whisper
- Common: `en`, `es`, `fr`, `de`, `it`, `pt`, `ru`, `ja`, `ko`, `zh`

### Output Formats
- **Video**: MP4 (H.264/AAC)
- **Subtitles**: SRT, ASS

## Integration Examples

### Batch Processing
```bash
#!/bin/bash
# Process multiple videos
for video in *.mp4; do
    python main.py "$video" --read --lang en
done
```

### Custom Workflow
```bash
# 1. Generate subtitles only
python main.py video.mp4 --only_srt --lang en

# 2. Review/edit subtitles
# (Edit video.srt manually)

# 3. Apply custom styling and burn
python main.py video.mp4 --input_srt video.srt --read --size 44 --color cyan
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you find this tool useful, please consider giving it a star on GitHub!

---

Made with OpenAI Whisper and FFmpeg
