---
name: verify-calendars
description: Generate the .ics calendars and sanity-check the output. Use after changing src/ (fetch, ics, or main) to confirm the generator still produces well-formed RFC 5545 files. Stands in for the missing test suite.
---

This project has no automated tests. Use this skill to verify changes by running the generator and inspecting its output.

## Steps

1. Run the generator from the repo root:
   ```bash
   python3 src/main.py
   ```
   - Exit code 0 = success. Note the per-region `[info] <slug>: N 场比赛` counts.
   - Exit code 1 = a fetch failed; by design no `.ics` was written. Report the error; this is the intended failure-preserves-old-files behavior, not a bug to "fix" by writing partial output.

2. Sanity-check each generated file (`dist/lpl.ics`, `dist/lck.ics`, `dist/intl.ics`):
   - Starts with `BEGIN:VCALENDAR` and ends with `END:VCALENDAR`.
   - Uses CRLF (`\r\n`) line endings (RFC 5545). Check with:
     ```bash
     python3 -c "d=open('dist/lpl.ics','rb').read(); print('CRLF' if b'\r\n' in d else 'LF-ONLY!')"
     ```
   - VEVENT blocks are balanced (`BEGIN:VEVENT` count == `END:VEVENT` count).
   - UIDs follow `lolmatch-<id>@lol-esports-calendar`.
   - An empty calendar (no VEVENTs) is normal during the off-season — not a failure.

3. If you changed folding/escaping in `ics.py`, spot-check that no line exceeds 75 bytes (continuation lines start with a single space) and that `;`, `,`, `\`, newline are escaped in TEXT values.

Report a concise pass/fail summary with the event counts and any anomalies.
