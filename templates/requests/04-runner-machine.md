# Request: a runner machine for automated walk-through recordings

**To:** <IT infrastructure or platform team>

## What we need

A machine, virtual machine or CI runner that can reach the test environment. It will run the walk-throughs again on a schedule (for example, nightly) and after every change to a spec.

| Item | Requirement |
|---|---|
| OS | Windows 10/11, Ubuntu 22.04+ or macOS 13+ |
| Software | Python 3.10+, Chromium (installed by Playwright), outbound HTTPS |
| Network | Access to <test environment URL>, and to `speech.platform.bing.com` if neural voices are approved (template 05) |
| Fonts | The scripts of every language recorded (e.g. Thai needs Noto Sans Thai on Linux) |
| Resources | 2 vCPU, 4 GB RAM, 5 GB disk |
| Secrets | A secrets store or masked CI variables for the test accounts and API credentials |

## Why

Each recording checks every step on screen and every result in the data. Running them regularly turns the training material into a test: if an application release renames a button, the run fails at that exact step, before anyone follows an outdated guide.
