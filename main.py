import json
from deepgram import DeepgramClient, PrerecordedOptions
from itertools import groupby
from operator import itemgetter

# STEP 1: Transcribe using Deepgram Nova-3
dg = DeepgramClient("YOUR_SECRET_KEY")  # Replace with your actual Deepgram API key

AUDIO_URL = {"url": "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav"}

opts = PrerecordedOptions(
    model="nova-3",
    language="en",
    smart_format=True,
    diarize=True  # We will also use word-level diarization manually
)

res = dg.listen.prerecorded.v("1").transcribe_url(AUDIO_URL, opts)

# Save response to JSON file (optional)
with open("deepgram_output.json", "w") as f:
    json.dump(res.to_dict(), f, indent=2)

# STEP 2: Build diarized transcript using word-level speaker IDs
words = res.results.channels[0].alternatives[0].words

# Group words by contiguous speaker id
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

# Print diarized transcript
print("\n--- Diarized Transcript ---\n")
for segment in diarized_segments:
    start_time = f"{segment['start']:.2f}s"
    end_time = f"{segment['end']:.2f}s"
    print(f"[{start_time} - {end_time}] {segment['speaker']}: {segment['text']}")

