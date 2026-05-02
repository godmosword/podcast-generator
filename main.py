from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from config import Config, Provider
from pipeline.podcast_pipeline import PodcastPipeline
from utils.file_utils import stem

app = typer.Typer(help="Podcast voice generator — convert scripts to MP3 podcasts.")


@app.command()
def generate(
    script: str = typer.Option(..., "--script", "-s", help="Path to script file (.txt or .md)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output MP3 path (default: output/<script_name>.mp3)"),
    provider: Provider = typer.Option(Provider.OPENAI, "--provider", "-p", help="TTS provider: edge | openai | elevenlabs"),
    bgm: Optional[str] = typer.Option(None, "--bgm", help="Background music file path"),
    title: Optional[str] = typer.Option(None, "--title", help="Podcast episode title (ID3 tag)"),
    artist: Optional[str] = typer.Option(None, "--artist", help="Podcast artist/host (ID3 tag)"),
    album: Optional[str] = typer.Option(None, "--album", help="Podcast series name (ID3 tag)"),
    normalize: bool = typer.Option(True, "--normalize/--no-normalize", help="Normalize audio loudness"),
) -> None:
    """Generate a podcast MP3 from a text/markdown script."""
    config = Config(provider=provider)

    if bgm:
        config.bgm_path = bgm

    script_path = Path(script)
    if not script_path.exists():
        typer.echo(f"Error: script file not found: {script}", err=True)
        raise typer.Exit(code=1)

    output_path = output or str(Path(config.output_dir) / f"{stem(script_path)}.mp3")

    metadata: dict = {"year": datetime.now().year}
    if title:
        metadata["title"] = title
    if artist:
        metadata["artist"] = artist
    if album:
        metadata["album"] = album

    typer.echo(f"Generating podcast from: {script_path}")
    typer.echo(f"Provider: {provider.value}")
    typer.echo(f"Output: {output_path}")

    pipeline = PodcastPipeline(config)
    asyncio.run(pipeline.run(str(script_path), output_path, metadata=metadata, normalize=normalize))

    typer.echo(f"\nDone! Output saved to: {output_path}")


@app.command()
def voices() -> None:
    """List available Edge TTS voices for Chinese."""
    import asyncio
    import edge_tts

    async def _list() -> None:
        all_voices = await edge_tts.list_voices()
        zh_voices = [v for v in all_voices if v["Locale"].startswith("zh")]
        for v in zh_voices:
            typer.echo(f"{v['ShortName']:<35} {v['Gender']:<8} {v['Locale']}")

    asyncio.run(_list())


if __name__ == "__main__":
    app()
