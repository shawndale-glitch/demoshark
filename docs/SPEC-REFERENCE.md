# Spec reference

A spec is a YAML file checked against [`demoshark/schema/walkthrough.schema.json`](../demoshark/schema/walkthrough.schema.json) and the rules below.

**Text fields** (`title`, `summary`, `say`, `result`, `name`, `label`, `placeholder`, `text`, `value`) take either one string, used in every language, or one string per language: `{ en: ..., es: ..., th: ... }`. They may contain `{{fixture.field}}` placeholders, filled in from the test data at run time (e.g. `{{invoice.number}}`).

## `walkthrough`

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Lowercase id, e.g. `paydesk-approve-invoice`. Names the output folder and files. |
| `title`, `summary` | yes | Shown on the title slide, in the guide header and in the video folder |
| `audience`, `owner` | no | Who watches it, and who approves changes to it |
| `version` | yes | `MAJOR.MINOR.PATCH` |
| `environment` | yes | `test`, `training` or `demo`. Anything else is rejected (DS3). |
| `languages` | yes | Language codes, e.g. `[en, es, th]`. Every text needs each of them (DS2). |

## `app`

| Field | Meaning |
|---|---|
| `name` | Shown on the title slide |
| `base_url` | Where the app runs. `demoshark demo` and `--base-url` override it. |
| `lang_param` | Query parameter that sets the interface language, e.g. `lang` → `/?lang=th`. Leave it out if the app has none. |
| `adapter` | Creates, reads and deletes the test data: `paydesk`, `none`, or your own ([ADAPTING.md](ADAPTING.md)) |
| `viewport` | `{ width: 1280, height: 720 }` by default, which is also the video size |

## `voice`

| Field | Values |
|---|---|
| `engine` | `auto` (default: edge, else sapi, else none), `edge`, `sapi`, `none` |
| `preset` | `smooth` (default), `warm-male`, `bright` |
| `voices` | Per-language override, e.g. `{ en: en-US-AndrewMultilingualNeural }` |
| `rate`, `pitch` | e.g. `"-6%"`, `"-2Hz"` |

## `fixtures`

Test records to create before the run, by name: `{ invoice: { supplier: Demo Supplier Delta, amount: 6400 } }`. The adapter returns each record with its fields (for example, the invoice `number`), which placeholders and `verify` then use.

## `steps`

| Field | Meaning |
|---|---|
| `id` | `S1`, `S2`, … in order (DS7) |
| `say` | One sentence: the caption, voice, subtitle, slide title and guide step |
| `do.action` | `open` (with `path`), `click`, `fill` (with `value`), `select` (with `value`, the option's label), `press` (with `key`), `wait` (with `seconds`) |
| `do.target` | The control (see Targets below) |
| `expect.target` | What must be on screen after the step |
| `expect.value` | For an input: the value it must hold |
| `expect.visible` | `false` to require that something has closed |
| `result` | The "What you should see" line in the guide and the deck |

### Targets

One of these, plus an optional `within`:

| Key | Finds | Example |
|---|---|---|
| `role` + `name` | Buttons, links, headings, dialogs, rows… by their visible name | `{ role: button, name: Approve }` |
| `label` | An input by its label | `{ label: Invoice number }` |
| `placeholder` | An input by its placeholder text | `{ placeholder: Search… }` |
| `text` | Any element by its exact text | `{ text: "Invoice {{invoice.number}} approved." }` |
| `within` | Narrows any of the above to inside another target | `within: { role: dialog, name: Approve invoice }` |

CSS selectors, XPath and test ids aren't accepted: a walk-through should break exactly when a person would get lost.

## `verify`

Data checks made through the adapter after the last step: `{ fixture: invoice, field: status, equals: approved }`, or `{ ..., filled: true }`.

## `outputs`

Any of `[video, deck, guide]`. All three by default.

## Rules

| Rule | Severity | Checks |
|---|---|---|
| DS1 | error | The spec matches the schema |
| DS2 | error | Every text is given in every declared language, with no TODO left |
| DS3 | error | The environment is test, training or demo, and the base URL isn't production |
| DS4 | error | Controls are found by role and visible name, label, placeholder or text |
| DS5 | error | Every step after the first has an `expect` |
| DS6 | error | Test data is fictional: no e-mail addresses or phone numbers; people and companies start with Demo or Test |
| DS7 | error | Step ids are S1, S2, … in order |
| DS8 | error | Every `{{fixture.field}}` names a declared fixture |
| DS9 | warning | Every step has a `result` line |
| DS10 | warning | At most 12 steps |
