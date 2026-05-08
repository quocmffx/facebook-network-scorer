# Privacy Boundaries

**Quiet tools for noisy systems. Local-first. Privacy-safe.**

This project is built on the principle that your social data belongs to you and should never be exposed to the public internet.

## 1. Local Processing Only
The Facebook Network Scorer is a command-line application that runs entirely on your local machine.
- No cloud uploads.
- No telemetry or tracking.
- No API keys needed.
- No outbound network requests are made during the scoring process.

## 2. No Data Commits
You must **never commit** any real Facebook export data to this repository or any public server. The `.gitignore` file is strictly configured to ignore the default Facebook export folder names (`facebook-*`, `your_facebook_activity`, etc.).

## 3. Dashboard Examples
If you build a UI on top of this scorer, ensure that it operates statically and locally. Do not use external CDNs for CSS/JS, and do not embed third-party analytics. Keep it simple and private.
