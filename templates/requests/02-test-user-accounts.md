# Request: test user accounts in <APPLICATION> (<ENVIRONMENT>)

**To:** <application admin or identity team>

## What we need

One named, non-personal test account for each role that appears in our walk-throughs:

| Role in the walk-through | Permissions needed | Suggested account name |
|---|---|---|
| <e.g. Accounts payable clerk> | <search and open invoices> | `demo.clerk` |
| <e.g. Finance manager> | <approve invoices> | `demo.manager` |

## Conditions

- The accounts must **not** belong to a real person and must have no production access.
- Passwords come through <password manager or vault>, never by e-mail or chat. A person signs in, and the tool reuses the saved browser session; it never stores the password.
- If single sign-on or MFA is enforced, please tell us how long a session lasts, so we can sign in again before each recording session.
- Please tell us if the accounts are disabled after a period of inactivity.
