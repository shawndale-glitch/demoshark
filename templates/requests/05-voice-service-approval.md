# Request: approval to use an online text-to-speech service for narration

**To:** <security or data protection>

## What we want to use

DEMOShark narrates each step with a neural voice. By default it uses Microsoft's online neural voices, through the open-source `edge-tts` package, because they sound natural and cover more than 100 languages.

## What is sent, and what is not

| Sent to the service | Never sent |
|---|---|
| The narration sentence of each step, e.g. "Select Approve." | Screenshots or video |
| The chosen voice name, speed and pitch | Test data, record numbers or URLs |
| | Credentials or personal data |

The narration lines are written in the spec and reviewed like any other change before a run.

## Alternatives if this is not approved

- **Offline voices** (`voice: { engine: sapi }`): the voices installed in Windows. Fewer languages.
- **Captions only** (`engine: none`): no audio. Each step stays on screen as long as it takes to read.
- **A licensed cloud speech service** under an existing company agreement. An engine can be added in `demoshark/voice.py`.

We ask you to approve the default, or to choose one of the alternatives.
