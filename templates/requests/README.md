# Access requests: templates

DEMOShark runs a real application the way a person would. To point it at **your** application instead of the bundled Paydesk demo, you need access that usually has to be requested from IT, security or the application's vendor. These templates are the requests that made the original pilot possible, made generic.

Copy one, fill in the `<placeholders>`, delete what doesn't apply, and send it through your usual ticketing channel.

| # | Template | Ask it of | Needed for | Without it |
|---|---|---|---|---|
| 01 | [Test environment access](01-test-environment-access.md) | Application owner or vendor | Recording against a non-production instance | Nothing runs |
| 02 | [Test user accounts](02-test-user-accounts.md) | Application admin or identity team | Signing in as each role a walk-through shows | Nothing runs |
| 03 | [API sandbox credentials](03-api-sandbox-credentials.md) | Vendor developer portal or integration team | Creating test data before a run and checking it after | No data checks (`verify`) |
| 04 | [Runner machine](04-runner-machine.md) | IT infrastructure | A machine or CI runner that can reach the test environment | No scheduled re-runs |
| 05 | [Voice service approval](05-voice-service-approval.md) | Security or data protection | Neural narration (online text-to-speech) | Offline voices or captions only |
| 06 | [Repository and review](06-repository-and-review.md) | Engineering or platform team | Storing specs, reviewing and approving changes | No change control |
| 07 | [Test data and privacy](07-test-data-and-privacy.md) | Data protection officer | Agreeing what may appear on screen in videos and decks | Nothing can be shared |

**An order that works:** 01 and 02 first, since nothing runs without them. Then 03. Then 05 and 07 before anything is shared. Finally 04 and 06, which make it repeatable.

**Never put secrets in a ticket, e-mail, chat or the repository.** Each template asks for credentials to come through a password manager or a secrets vault. DEMOShark reads them from environment variables only.
