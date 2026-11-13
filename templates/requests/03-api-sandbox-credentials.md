# Request: API sandbox credentials for <APPLICATION>

**To:** <vendor developer portal or integration team>

## What we need

Credentials for the application's **sandbox** API, so the tool can:

1. **Create** the test record a walk-through needs (for example, one invoice) just before recording.
2. **Read it back** afterwards, to prove the walk-through really did what it shows (for example, that the status is "approved").
3. **Delete or cancel** it at the end.

| Item | Value |
|---|---|
| API | <name and version> |
| Environment | Sandbox or test only |
| Scopes | <read and write on one object type, e.g. invoices>, and nothing else |
| Grant type | <client credentials or API key> |
| Volume | Fewer than 50 calls per recording |

## Conditions

- The client secret or API key comes through <vault>. It is stored only in a local, git-ignored `.env` file or a masked CI variable, never in tickets, e-mail, chat, documents or the repository.
- Test records use fictional names that start with **Demo** or **Test** (rule DS6).
- We will rotate the secret <every 90 days / on request>.

## Technical note

The tool's adapter needs three calls: create, get and delete (see `docs/ADAPTING.md`). Please share the API reference and the sandbox base URL.
