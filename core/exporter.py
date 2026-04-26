from __future__ import annotations

from pathlib import Path

from mutagen.id3 import ID3, ID3NoHeaderError, TALB, TCOM, TCON, TIT2, TPE1, TRCK, TYER
from pydub import AudioSegment


def export_audio(
    audio: AudioSegment,
    output_path: str,
    metadata: dict | None = None,
    output_format: str = "mp3",
    bitrate: str = "192k",
) -> str:
    if output_format == "wav":
        return export_wav(audio, output_path)
    return export_mp3(audio, output_path, metadata=metadata, bitrate=bitrate)


def export_mp3(
    audio: AudioSegment,
    output_path: str,
    metadata: dict | None = None,
    bitrate: str = "192k",
) -> str:
    """Export AudioSegment to MP3 and write ID3 tags. Returns output path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    audio.export(str(path), format="mp3", bitrate=bitrate)

    if metadata:
        _write_id3(str(path), metadata)

    return str(path)


def export_wav(audio: AudioSegment, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    audio.export(str(path), format="wav")
    return str(path)


def _write_id3(path: str, metadata: dict) -> None:
    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()

    if title := metadata.get("title"):
        tags["TIT2"] = TIT2(encoding=3, text=title)
    if artist := metadata.get("artist"):
        tags["TPE1"] = TPE1(encoding=3, text=artist)
    if album := metadata.get("album"):
        tags["TALB"] = TALB(encoding=3, text=album)
    if year := metadata.get("year"):
        tags["TYER"] = TYER(encoding=3, text=str(year))
    if genre := metadata.get("genre"):
        tags["TCON"] = TCON(encoding=3, text=genre)
    if composer := metadata.get("composer"):
        tags["TCOM"] = TCOM(encoding=3, text=composer)
    if track := metadata.get("track"):
        tags["TRCK"] = TRCK(encoding=3, text=str(track))

    tags.save(path)
