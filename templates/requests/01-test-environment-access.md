# Request: access to a test environment of <APPLICATION>

**To:** <application owner or vendor support>  **From:** <your name and team>  **Priority:** <normal>

## What we need

Access to a **non-production** instance of <APPLICATION> (test, training or sandbox), so we can record step-by-step training walk-throughs automatically. Nothing will be recorded in production: the tool rejects production addresses by rule (DS3).

| Item | Value |
|---|---|
| Environment | <test / training / sandbox> |
| URL | <https://...> (shared privately, not in this ticket, if it is sensitive) |
| Modules and screens | <e.g. Invoices: search, details, approval> |
| Interface languages | <e.g. English, Spanish, Thai> |
| Period | <from> to <to>, then <ongoing, for re-runs?> |
| Data | Fictional only. We create and delete our own test records. |

## Why

Each walk-through (a video, a slide deck and a written guide) is generated from one spec file and recorded against the real screens, so the material matches the system. When the system changes, running the spec again shows exactly which step no longer matches.

## Questions for you

1. Is the test environment refreshed from production? If so, how is personal data masked?
2. Can the interface language be chosen per user or per session (a URL parameter or a user preference)?
3. Are there maintenance windows or session time-outs we should plan around?
4. Do your terms and your bot protection allow automated browser access (Playwright / Chromium)?
