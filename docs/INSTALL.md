# Install

DEMOShark runs on Windows, macOS and Linux. Everything it needs installs with pip, including a private copy of ffmpeg and a private Chromium for the browser.

## Requirements

| Need | Version | Why |
|---|---|---|
| Python | 3.10 or newer | The tool itself |
| Disk | About 600 MB | Chromium (about 400 MB) and the packages |
| Internet | During the install, and for neural voices | pip, Chromium and narration. Without internet, use `--voice none` or Windows voices. |
| Fonts | Your languages' scripts | Linux needs, for example, `fonts-noto-core` (Thai) and `fonts-noto-cjk` (Chinese, Japanese) |

Nothing else needs installing: ffmpeg comes with the `imageio-ffmpeg` package.

## Steps

```bash
git clone https://github.com/shawndale-glitch/demoshark.git
cd demoshark
python -m venv .venv
```

Activate the environment:

| OS | Command |
|---|---|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| macOS / Linux | `source .venv/bin/activate` |

Then:

```bash
pip install -e ".[dev]"
python -m playwright install chromium
```

On Linux, add `--with-deps` to the last command so it also installs the system libraries Chromium needs.

## Check the install

```bash
python -m demoshark check specs/paydesk-approve-invoice.yaml
python -m demoshark voices
python -m pytest -q
```

You should see `PASS ... 0 errors`, the voice engines available on your machine, and `12 passed`.

## First run

```bash
python -m demoshark demo
```

This starts the bundled Paydesk app, records the sample walk-through in English, Spanish and Thai, and builds a narrated video, a PowerPoint deck and a guide for each language. It takes about two minutes. The results are in `build/paydesk-approve-invoice/<lang>/`.

## Other ways to run it

- **Dev container / Codespaces:** open the repository in VS Code with the Dev Containers extension, or in a GitHub Codespace. `.devcontainer/` installs everything, so you can type `python -m demoshark demo`.
- **The `demoshark` command:** after `pip install -e .`, `demoshark demo` works too. Some locked-down Windows machines block new `.exe` files in a virtual environment; if so, use `python -m demoshark` instead, which runs the same code.

## Corporate networks

| Symptom | Cause | What to do |
|---|---|---|
| `playwright install` hangs or fails | A proxy blocks the download | Set `HTTPS_PROXY`, or ask IT to allow `playwright.azureedge.net` |
| Voice falls back to `sapi` or `none` | The speech service is blocked | Ask for approval ([template 05](../templates/requests/05-voice-service-approval.md)), or use `--voice none` |
| `pip install` fails on certificates | TLS inspection | `pip config set global.cert <your-company-ca.pem>` |
