# User guide

DEMOShark turns **one spec file** into a narrated walk-through video, a PowerPoint deck and a written guide, in every language the spec declares. Each output comes from a real, checked run of the application.

```
spec.yaml ──► check (rules DS1–DS10) ──► run in the app, one language at a time ──► build in parallel:
                                          · caption + highlight + voice per step     · walkthrough.mp4 (+ .srt/.vtt)
                                          · each step checked on screen              · <id>-<lang>.pptx
                                          · test data created, verified, deleted     · guide.md + guide.html
                                                                                     · qa-report.md
```

## 1. Write a spec

Start from [`templates/spec-template.yaml`](../templates/spec-template.yaml), or copy the sample [`specs/paydesk-approve-invoice.yaml`](../specs/paydesk-approve-invoice.yaml). A step has four parts:

```yaml
- id: S5
  say:    { en: Select Approve., es: Pulse Aprobar. }                  # caption, voice, subtitle, slide title, guide step
  do:     { action: click, target: { role: button, name: { en: Approve, es: Aprobar } } }
  expect: { target: { role: dialog, name: { en: Approve invoice, es: Aprobar factura } } }
  result: { en: The Approve invoice window opens., es: Se abre la ventana Aprobar factura. }
```

- **say** is the one sentence the audience hears and reads. Keep it short: what to do, then what happens.
- **do** is what the browser does. Name controls the way a person sees them (role and visible name, label, placeholder or text), never by code selectors. If a release renames the button, the run fails at this step, which is exactly what you want.
- **expect** is what must be on screen afterwards. A step without one proves nothing (rule DS5).
- **result** is the "What you should see" line in the guide and the deck.

All the fields are described in the [spec reference](SPEC-REFERENCE.md).

## 2. Check it

```bash
python -m demoshark check specs/my-walkthrough.yaml
```

The check needs no browser or network. Each finding names a rule, where it is, and what's wrong:

```
DS2 [error] steps[3].say: missing th
DS6 [error] fixtures.order.customer: 'Acme Ltd' must start with Demo or Test
FAIL  specs/my-walkthrough.yaml: 2 errors, 0 warnings
```

A spec with errors never runs.

## 3. Run it

```bash
python -m demoshark run specs/my-walkthrough.yaml              # every language in the spec
python -m demoshark run specs/my-walkthrough.yaml --lang es    # one language
python -m demoshark run specs/my-walkthrough.yaml --headed     # watch the browser
python -m demoshark run specs/my-walkthrough.yaml --voice none # silent, captions only (fast, offline)
python -m demoshark run specs/my-walkthrough.yaml --only deck  # build only some outputs
```

For each language, the run:

1. creates the test data (the `fixtures`) through the app's adapter;
2. records the narration first, so it knows how long each step must last;
3. opens the app and, for each step, shows the caption, rings the control, lets the voice play, acts, and checks the expected result;
4. reads the test data back (`verify`) and deletes it.

Once every language is recorded, the video, the deck and the guide of every language are built **in parallel**.

To rebuild the outputs after changing only presentation code, without running the app again, use `python -m demoshark build specs/my-walkthrough.yaml`.

## 4. The outputs

`build/<id>/<lang>/` holds:

| File | What it is |
|---|---|
| `walkthrough.mp4` | 720p narrated video, with captions on screen and a subtitle track |
| `walkthrough.srt`, `.vtt` | Subtitles, for players and learning platforms |
| `<id>-<lang>.pptx` | Deck: title, overview, one slide per step (ringed screenshot, what you should see, the second in the video, pass), verification. The narration is in the speaker notes. |
| `guide.md` | Written guide for a wiki or repository |
| `guide.html` | One page with the video; each step jumps to its second in the video |
| `qa-report.md`, `run.json` | Each step's result and start time; the data checks |
| `shots/S<n>.png` | The screenshot of each step |

## 5. When the app changes

Run the spec again. If the screens still match, every output is regenerated. If a release renamed or moved something, the run stops at that step:

```
FAIL at S5: could not find button name="Approve" on screen within 8 s
Nothing is published for a language that failed: its qa-report.md says where and why.
```

To try it with the bundled app, run `python -m demoshark demo --drift --voice none`: Paydesk renames Approve to Authorise, as a vendor release might.

## 6. Languages and voices

Add a language to `walkthrough.languages` and a translation to every text; rule DS2 lists anything you've missed. The app must support the language too (Paydesk speaks English, Spanish and Thai).

Voices come from presets:

| Preset | Sound | English | Spanish | Thai |
|---|---|---|---|---|
| `smooth` (default) | Warm, relaxed, slightly slower and lower | Ava (multilingual) | Ximena | Premwadee |
| `warm-male` | Deep and confident | Andrew (multilingual) | Álvaro | Niwat |
| `bright` | Clear and upbeat | Emma (multilingual) | Dalia | Premwadee |

Listen before choosing:

```bash
python -m demoshark voices --sample --lang en     # writes build/voice-samples/en-<preset>.wav
```

To fine-tune, set `voice.rate` (e.g. `"-10%"`) or `voice.pitch` (e.g. `"-4Hz"`), or override one language's voice under `voice.voices`. Engines: `edge` (neural, online), `sapi` (Windows, offline), `none` (captions only), and `auto`, which tries them in that order.

## 7. Your own application

To record your own application:

1. **Get access.** The [request templates](../templates/requests/README.md) cover the test environment, test accounts, API credentials, a runner machine, the voice service, review rules and privacy.
2. **Write an adapter** if your walk-through needs test data. It's three methods: see [ADAPTING.md](ADAPTING.md).
3. **Sign in, if needed.** For apps behind a sign-in page, see "Apps that need a sign-in" in [ADAPTING.md](ADAPTING.md).

## Troubleshooting

| Message | Meaning | Fix |
|---|---|---|
| `could not find ... on screen within 8 s` | The control isn't there under that name | Open the app with `--headed` and compare the visible name. Did a release rename it? |
| `expected ... on screen` | The action didn't lead where the spec says | Check the expect target, or whether the step needs a `wait` before it |
| `no voice engine worked` | No network for neural voices, and no offline voice for that language | `--voice none`, or install a Windows voice |
| Squares instead of letters in the video | The machine lacks a font for that script | Install one, e.g. Noto Sans Thai (Linux: `fonts-noto-core`) |
| `The spec has errors: nothing was run.` | A rule failed | Run `check` and fix what it lists |
