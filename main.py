import argparse
import json
from itertools import groupby
from operator import itemgetter
from pathlib import Path

from deepgram import ( 
    DeepgramClient, 
    PrerecordedOptions,
    FileSource,
)

from rich.console import Console
from rich.table import Table
from rich.progress import Progress


def transcribe_audio(audio_path, api_key):
    dg = DeepgramClient(api_key)

    opts = PrerecordedOptions(
        model="nova-3",
        language="en",
        smart_format=True,
        diarize=True
    )

    if audio_path.startswith("http://") or audio_path.startswith("https://"):
        source = {"url": audio_path}
        res = dg.listen.rest.v("1").transcribe_url(source, opts)
    else:
        with open(audio_path, "rb") as f:
            payload: FileSource = {
                "buffer": f.read()
            }
            res = dg.listen.rest.v("1").transcribe_file(payload, opts)

    return res


def build_diarized_transcript(res):
    words = res.results.channels[0].alternatives[0].words
    diarized_segments = []

    for speaker, group in groupby(words, key=itemgetter("speaker")):
        group = list(group)
        start = group[0]["start"]
        end = group[-1]["end"]
        text = " ".join([w["punctuated_word"] for w in group])
        diarized_segments.append({
            "speaker": f"Speaker {speaker}",
            "start": start,
            "end": end,
            "text": text
        })
    return diarized_segments


def print_diarized_table(diarized_segments):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Start", style="cyan")
    table.add_column("End", style="cyan")
    table.add_column("Speaker", style="green")
    table.add_column("Text", style="white", overflow="fold")

    for seg in diarized_segments:
        start_time = f"{seg['start']:.2f}s"
        end_time = f"{seg['end']:.2f}s"
        table.add_row(start_time, end_time, seg["speaker"], seg["text"])

    console = Console()
    console.print("\n[bold underline]Diarized Transcript[/bold underline]\n")
    console.print(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe audio with Deepgram Nova-3 and diarization.")
    parser.add_argument("audio", help="Path or URL to the audio file")
    parser.add_argument("--api_key", required=True, help="Deepgram API key")
    parser.add_argument("--save_json", help="Optional path to save raw Deepgram JSON output")
    args = parser.parse_args()

    console = Console()

    with Progress() as progress:
        task = progress.add_task("[cyan]Transcribing audio...", total=None)
        res = transcribe_audio(args.audio, args.api_key)
        progress.update(task, completed=1)

    if args.save_json:
        with open(args.save_json, "w") as f:
            json.dump(res.to_dict(), f, indent=2)

    diarized_segments = build_diarized_transcript(res)
    print_diarized_table(diarized_segments)

