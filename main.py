def clean_color_codes(text: str) -> str:
    import re
    return re.sub(r'\{\\c&H[0-9A-Fa-f]{6}&\}|\{\\c\}', '', text).strip()

def split_read_mode(segments: list[dict[str, float | str]], max_chars: int = 50, max_duration: float = 4.0, read_color: str = "yellow") -> list[dict[str, float | str]]:
    if any("words" in seg for seg in segments if isinstance(seg, dict)):
        word_segments = extract_word_timestamps(segments)
    else:
        word_segments = split_into_words(segments)
    
    new_segments = []
    current_chunk = []
    current_length = 0
    current_start = None
    
    for word_seg in word_segments:
        word = str(word_seg["text"]).strip()
        
        if current_length + len(word) + 1 <= max_chars and len(current_chunk) > 0:
            current_chunk.append(word_seg)
            current_length += len(word) + 1
        else:
            if current_chunk:
                process_chunk(current_chunk, new_segments, read_color, max_duration)
            current_chunk = [word_seg]
            current_length = len(word)
            current_start = word_seg["start"]
        
        if current_start and (word_seg["end"] - current_start) >= max_duration:
            if current_chunk:
                process_chunk(current_chunk, new_segments, read_color, max_duration)
            current_chunk = []
            current_length = 0
            current_start = None
    
    if current_chunk:
        process_chunk(current_chunk, new_segments, read_color, max_duration)
    
    for i in range(len(new_segments) - 1):
        current_seg = new_segments[i]
        next_seg = new_segments[i + 1]
        if current_seg["end"] < next_seg["start"]:
            new_segments[i]["end"] = next_seg["start"]
    
    return new_segments

def process_chunk(chunk: list[dict[str, float | str]], new_segments: list, read_color: str, max_duration: float) -> None:
    for i, current_word in enumerate(chunk):
        chunk_text = []
        for j, word_seg in enumerate(chunk):
            word = str(word_seg["text"]).strip()
            if j <= i:
                chunk_text.append(f'{{\\c&H{color_to_hex(read_color)}&}}{word}{{\\c&HFFFFFF&}}')
            else:
                chunk_text.append(word)
        
        seg_text = ' '.join(chunk_text)
        if i < len(chunk) - 1:
            end_time = chunk[i + 1]["start"]
        else:
            end_time = current_word["end"]
        new_segments.append({
            "start": current_word["start"],
            "end": end_time,
            "text": seg_text
        })
import argparse
import subprocess
import sys
from pathlib import Path
import whisper

def read_text_file(text_path: Path) -> str:
    with open(text_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def align_text_with_transcription(text_content: str, whisper_segments: list) -> list[dict[str, float | str]]:
    import re
    
    text_words = re.findall(r'\b\w+\b', text_content.lower())
    whisper_words = []
    
    for seg in whisper_segments:
        if "words" in seg and seg["words"]:
            for word_data in seg["words"]:
                whisper_words.append({
                    "word": word_data["word"].strip().lower(),
                    "start": word_data["start"],
                    "end": word_data["end"]
                })
    
    aligned_segments = []
    text_idx = 0
    whisper_idx = 0
    
    while text_idx < len(text_words) and whisper_idx < len(whisper_words):
        text_word = text_words[text_idx]
        whisper_word = whisper_words[whisper_idx]["word"]
        
        if text_word == whisper_word:
            aligned_segments.append({
                "start": whisper_words[whisper_idx]["start"],
                "end": whisper_words[whisper_idx]["end"],
                "text": whisper_words[whisper_idx]["word"].strip()
            })
            text_idx += 1
            whisper_idx += 1
        elif text_word in whisper_word or whisper_word in text_word:
            aligned_segments.append({
                "start": whisper_words[whisper_idx]["start"],
                "end": whisper_words[whisper_idx]["end"],
                "text": text_words[text_idx]
            })
            text_idx += 1
            whisper_idx += 1
        else:
            whisper_idx += 1
            
            if whisper_idx >= len(whisper_words):
                break
    
    if not aligned_segments:
        print("Warning: Could not align text file with audio. Using standard transcription.")
        return whisper_segments
    
    return aligned_segments

def read_srt(srt_path: Path) -> list[dict[str, float | str]]:
    segments = []
    
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    subtitle_blocks = content.split("\n\n")
    
    for block in subtitle_blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
            
        time_line = lines[1]
        start_str, end_str = time_line.split(" --> ")
        
        start = parse_time(start_str)
        end = parse_time(end_str)
        
        text = "\n".join(lines[2:])
        
        segments.append({
            "start": start,
            "end": end,
            "text": text
        })
    
    return segments

def parse_time(time_str: str) -> float:
    time_str = time_str.replace(",", ".")
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    
    return hours * 3600 + minutes * 60 + seconds

def main() -> None:
    args = parse_args()
    video_path = Path(args.input)
    if not video_path.exists():
        print("Error: video file not found")
        sys.exit(1)
    srt_path = Path(args.srt) if args.srt else video_path.with_suffix(".srt")
    if args.input_srt:
        if not Path(args.input_srt).exists():
            print("Error: input file not found")
            sys.exit(1)
        
        file_path = Path(args.input_srt)
        if file_path.suffix.lower() == '.srt':
            segments = read_srt(file_path)
        else:
            text_content = read_text_file(file_path)
            if not args.skip_transcribe:
                segments = transcribe_audio(video_path, args.lang)
                segments = align_text_with_transcription(text_content, segments)
            else:
                print("Error: Text file requires transcription. Remove --skip_transcribe flag.")
                sys.exit(1)
        
        if args.read:
            ass_path = Path(args.srt).with_suffix(".ass") if args.srt else video_path.with_suffix(".ass")
            segments = split_read_mode(segments, args.max_chars, args.max_duration, args.read_color)
            save_ass(segments, ass_path, args.font, args.size, args.color)
            if args.only_srt:
                print(f"ASS subtitles generated in: {ass_path}")
                return
            output_path = Path(args.output) if args.output else video_path.stem + "_subtitled.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(video_path), "-vf", f"subtitles='{ass_path}'", str(output_path)
            ], check=True)
            print(f"Video subtitulado generado en: {output_path}")
            return
        else:
            save_srt(
                segments, srt_path, args.max_chars, args.max_duration,
                word_mode=args.word, read_mode=False, read_color=args.read_color
            )
    elif not args.skip_transcribe:
        segments = transcribe_audio(video_path, args.lang)
        if args.read:
            ass_path = Path(args.srt).with_suffix(".ass") if args.srt else video_path.with_suffix(".ass")
            segments = split_read_mode(segments, args.max_chars, args.max_duration, args.read_color)
            save_ass(segments, ass_path, args.font, args.size, args.color)
            if args.only_srt:
                print(f"ASS subtitles generated in: {ass_path}")
                return
            output_path = Path(args.output) if args.output else video_path.stem + "_subtitled.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(video_path), "-vf", f"subtitles='{ass_path}'", str(output_path)
            ], check=True)
            print(f"Video subtitulado generado en: {output_path}")
            return
        else:
            save_srt(
                segments, srt_path, args.max_chars, args.max_duration,
                word_mode=args.word, read_mode=False, read_color=args.read_color
            )
    if args.only_srt:
        print(f"Subtitles generated in: {srt_path}")
        return
    output_path = Path(args.output) if args.output else video_path.stem + "_subtitled.mp4"
    burn_subtitles(video_path, srt_path, output_path, args.font, args.size, args.color)
    print(f"Video subtitulado generado en: {output_path}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Easy subtitle generator")
    parser.add_argument("input", type=str)
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("-s", "--srt", type=str)
    parser.add_argument("-i", "--input_srt", type=str, help="Use existing subtitle file (.srt) or text file (.txt) as script")
    parser.add_argument("--only_srt", action="store_true")
    parser.add_argument("--lang", type=str, default="es")
    parser.add_argument("--font", type=str, default="Arial")
    parser.add_argument("--size", type=int, default=36)
    parser.add_argument("--color", type=str, default="white")
    parser.add_argument("--skip_transcribe", action="store_true")
    parser.add_argument("--max_chars", type=int, default=30)
    parser.add_argument("--max_duration", type=float, default=3.0)
    parser.add_argument("--word", action="store_true")
    parser.add_argument("--read", action="store_true")
    parser.add_argument("--read-color", type=str, default="yellow")
    return parser.parse_args()

def extract_audio(video_path: Path) -> Path:
    audio_path = video_path.with_suffix(".wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(audio_path)
    ], check=True)
    return audio_path

def transcribe_audio(video_path: Path, lang: str) -> list[dict[str, float | str]]:
    audio_path = extract_audio(video_path)
    model = whisper.load_model("small")
    result = model.transcribe(str(audio_path), language=lang, word_timestamps=True)
    return result["segments"]

def format_time(t) -> str:
    hours = int(t // 3600)
    minutes = int((t % 3600) // 60)
    seconds = int(t % 60)
    milliseconds = int((t % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def extract_word_timestamps(segments: list[dict]) -> list[dict[str, float | str]]:
    """Extract individual words with their precise timestamps from Whisper segments"""
    word_segments = []
    
    for seg in segments:
        if "words" in seg and seg["words"]:
            for word_data in seg["words"]:
                word_segments.append({
                    "start": word_data["start"],
                    "end": word_data["end"], 
                    "text": word_data["word"].strip()
                })
        else:
            text = clean_color_codes(str(seg["text"]).strip())
            start = seg["start"]
            end = seg["end"]
            duration = end - start
            
            words = text.split()
            if len(words) <= 1:
                word_segments.append({
                    "start": start,
                    "end": end,
                    "text": text
                })
                continue
            
            word_duration = duration / len(words)
            for i, word in enumerate(words):
                word_start = start + (i * word_duration)
                word_end = start + ((i + 1) * word_duration)
                
                word_segments.append({
                    "start": word_start,
                    "end": word_end,
                    "text": word
                })
    
    return word_segments

def split_into_words(segments: list[dict[str, float | str]]) -> list[dict[str, float | str]]:
    new_segments = []
    
    for seg in segments:
        text = clean_color_codes(str(seg["text"]).strip())
        start = seg["start"]
        end = seg["end"]
        duration = end - start
        
        words = text.split()
        if len(words) <= 1:
            new_segments.append({
                "start": start,
                "end": end,
                "text": text
            })
            continue
        
        word_duration = duration / len(words)
        
        for i, word in enumerate(words):
            word_start = start + (i * word_duration)
            word_end = start + ((i + 1) * word_duration)
            
            new_segments.append({
                "start": word_start,
                "end": word_end,
                "text": word
            })
    
    return new_segments

def split_long_segments(segments: list[dict[str, float | str]], max_chars: int = 50, max_duration: float = 4.0) -> list[dict[str, float | str]]:
    new_segments = []
    
    for seg in segments:
        text = str(seg["text"]).strip()
        start = seg["start"]
        end = seg["end"]
        duration = end - start
        
        if len(text) <= max_chars and duration <= max_duration:
            new_segments.append(seg)
            continue
        
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_chars and len(current_chunk) > 0:
                current_chunk.append(word)
                current_length += len(word) + 1
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        if len(chunks) > 1:
            chunk_duration = min(max_duration, duration / len(chunks))
            for i, chunk in enumerate(chunks):
                chunk_start = start + (i * chunk_duration)
                chunk_end = min(start + ((i + 1) * chunk_duration), end)
                
                new_segments.append({
                    "start": chunk_start,
                    "end": chunk_end,
                    "text": chunk
                })
        else:
            new_segments.append(seg)
    
    return new_segments

def save_ass(segments: list[dict[str, float | str]], ass_path: Path, font: str = "Arial", size: int = 36, color: str = "white") -> None:
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 1920\n")
        f.write("PlayResY: 1080\n")
        f.write("ScaledBorderAndShadow: yes\n\n")
        
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write(f"Style: Default,{font},{size},&H{color_to_hex(color)},&H{color_to_hex(color)},&H000000,&H000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n")
        
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        
        for seg in segments:
            start = format_ass_time(seg["start"])
            end = format_ass_time(seg["end"])
            text = str(seg["text"]).strip()
            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

def format_ass_time(t: float) -> str:
    hours = int(t // 3600)
    minutes = int((t % 3600) // 60)
    seconds = t % 60
    return f"{hours}:{minutes:02d}:{seconds:05.2f}"

def save_srt(segments: list[dict[str, float | str]], srt_path: Path, max_chars: int = 50, max_duration: float = 4.0, word_mode: bool = False, read_mode: bool = False, read_color: str = "yellow") -> None:
    if read_mode:
        segments = split_read_mode(segments, max_chars, max_duration, read_color)
        ass_path = srt_path.with_suffix(".ass")
        save_ass(segments, ass_path)
        return
    elif word_mode:
        # Use precise word timestamps when available
        if any("words" in seg for seg in segments if isinstance(seg, dict)):
            segments = extract_word_timestamps(segments)
        else:
            segments = split_into_words(segments)
    else:
        segments = split_long_segments(segments, max_chars, max_duration)
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = format_time(seg["start"])
            end = format_time(seg["end"])
            text = str(seg["text"]).strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

def modify_ass_style(ass_path: Path, font: str, size: int, color: str) -> None:
    with open(ass_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    new_lines = []
    
    for line in lines:
        if line.startswith("Style: Default,"):
            parts = line.split(",")
            if len(parts) >= 23:
                parts[1] = font
                parts[2] = str(size)
                parts[3] = f"&H{color_to_hex(color)}"
                parts[4] = "&H000000"
                parts[19] = "1"
                parts[20] = "2"
                parts[21] = "0"
                line = ",".join(parts)
        new_lines.append(line)
    
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

def burn_subtitles(video_path: Path, srt_path: Path, output_path: Path, font: str, size: int, color: str) -> None:
    ass_path = srt_path.with_suffix(".ass")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(srt_path), str(ass_path)
    ], check=False)
    
    modify_ass_style(ass_path, font, size, color)
    
    vf = f"subtitles='{ass_path}'"
    
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_path), "-vf", vf, str(output_path)
    ], check=True)

def color_to_hex(color: str) -> str:
    colors = {
        "white": "FFFFFF",
        "black": "000000",
        "red": "FF0000",
        "green": "00FF00",
        "blue": "0000FF",
        "yellow": "FFFF00",
        "cyan": "00FFFF",
        "magenta": "FF00FF"
    }
    return colors.get(color.lower(), "FFFFFF")

if __name__ == "__main__":
    main()
