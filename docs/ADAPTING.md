# Pointing DEMOShark at your own application

## 1. Access

Ask for it with the [request templates](../templates/requests/README.md): a test environment, test accounts, sandbox API credentials if you need test data, a runner machine, approval for the voice service, and agreement on privacy.

## 2. An adapter for test data

A walk-through such as "approve an invoice" needs an invoice to approve. The adapter creates it before the run, reads it back afterwards to prove the result (`verify`), and deletes it. It's a class with three methods:

```python
# demoshark/adapters/myapp.py
import os, requests

class MyAppAdapter:
    def __init__(self, base_url: str):
        self.api = os.environ["MYAPP_API_URL"]                      # never hard-code
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {os.environ['MYAPP_API_TOKEN']}"   # from .env or CI secrets

    def create(self, kind: str, values: dict) -> dict:             # fixtures.<kind>: values
        r = self.s.post(f"{self.api}/{kind}s", json=values, timeout=15); r.raise_for_status()
        return r.json()                                              # fields usable as {{kind.field}}

    def get(self, kind: str, record: dict) -> dict:
        return self.s.get(f"{self.api}/{kind}s/{record['id']}", timeout=15).json()

    def delete(self, kind: str, record: dict) -> None:
        self.s.delete(f"{self.api}/{kind}s/{record['id']}", timeout=15)
```

Register it in `demoshark/adapters/__init__.py` (`ADAPTERS = {..., "myapp": MyAppAdapter}`) and set `app.adapter: myapp` in the spec. If the walk-through needs no data, use `adapter: none`.

Keep secrets in environment variables: a git-ignored `.env` file locally, masked variables in CI.

## 3. Apps that need a sign-in

DEMOShark never types passwords. For an app behind a sign-in page:

1. A person signs in once in a browser that Playwright saves:

   ```bash
   python -m playwright codegen --save-storage=.auth/myapp.json https://test.example.com
   ```

2. Load that session when the context is created, in `runner.record` (`browser.new_context(storage_state=".auth/myapp.json", ...)`). Keep `.auth/` git-ignored. It's already in `.gitignore`.
3. Sessions expire, so sign in again before a recording session.

## 4. Languages

If your app reads its language from the URL, set `app.lang_param`. If it reads it from a user preference, use one test account per language, or add an `open` step that switches the language.

## 5. Privacy on screen

Lists in shared test environments can show other people's records. Filter them out before recording (a search step), or use an environment with only fictional data. See [template 07](../templates/requests/07-test-data-and-privacy.md).
