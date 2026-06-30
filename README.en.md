# lol-esports-calendar

[简体中文](README.md) · **English** · [한국어](README.ko.md)

Auto-fetches **League of Legends esports schedules** (**LPL / LCK / LEC / LCP / LTA / MSI / Worlds / International**) and generates subscribable `.ics` calendar files that work in **Apple Calendar, Google Calendar, Outlook**, and any client supporting iCalendar (`.ics`) subscriptions. Refreshed hourly by GitHub Actions and hosted on GitHub Pages. **Pure standard library, zero dependencies.**

Calendar content is available in Chinese / English / Korean (see below).

## Subscription links

Copy a link below to subscribe (calendar content is in **English**). Want Chinese or Korean? Use the **简体中文 / 한국어** switch at the top of this page.

| Region | Subscription URL |
|--------|------------------|
| LPL (China) | `https://hh-io.github.io/lol-esports-calendar/dist/en/lpl.ics` |
| LCK (Korea) | `https://hh-io.github.io/lol-esports-calendar/dist/en/lck.ics` |
| LEC (EMEA) | `https://hh-io.github.io/lol-esports-calendar/dist/en/lec.ics` |
| LCP (Pacific) | `https://hh-io.github.io/lol-esports-calendar/dist/en/lcp.ics` |
| LTA (Americas) | `https://hh-io.github.io/lol-esports-calendar/dist/en/lta.ics` |
| International (MSI/Worlds/First Stand) | `https://hh-io.github.io/lol-esports-calendar/dist/en/intl.ics` |

> When you fork and deploy your own, replace `hh-io` / `lol-esports-calendar` with your username / repo.

> Match times are stored in UTC; Apple Calendar automatically displays them in your local time zone.

## Subscribing in Apple Calendar

**macOS**: Calendar app → menu **File** → **New Calendar Subscription…** → paste the URL → set "Auto-refresh" to "Every hour" or "Every day".

**iPhone/iPad**: Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar → paste the URL.

Replacing `https://` with `webcal://` lets you open the calendar app directly from the link.

## Google Calendar / Outlook

The same `.ics` URL works in other clients too:

- **Google Calendar** (web): "Other calendars" → "+" → "From URL" → paste the URL.
- **Outlook**: "Add calendar" → "Subscribe from web" → paste the URL.

## Run locally

```bash
python3 src/main.py      # generates dist/*.ics plus dist/en, dist/ko variants
```

## Deployment

1. Push this repo to GitHub.
2. **Settings → Pages**: Source = `Deploy from a branch`, branch `main`, folder `/ (root)`. Subscription path is then `https://<user>.github.io/<repo>/dist/lpl.ics`.
3. **Settings → Actions → General**: ensure the workflow has `Read and write permissions`.
4. Go to **Actions**, run `Update LoL calendars` → `Run workflow` once to confirm it generates and commits. It auto-updates hourly afterward (scores appear ~1–2 h after a match ends).

## Structure

```
src/fetch.py   resolves league IDs via getLeagues, paginates getSchedule, normalizes events (hl controls language)
src/ics.py     events → RFC 5545 .ics text (stable UID, CRLF, 75-byte folding, multilingual static labels)
src/main.py    outputs .ics per language × subscription group; on any fetch failure, keeps old files
.github/workflows/update.yml   scheduled + manual trigger, commits only on change
dist/          Chinese .ics; dist/en, dist/ko hold English / Korean (served by Pages)
```

## Data source & risks

Data comes from the unofficial endpoint lolesports.com itself uses (`esports-api.lolesports.com/persisted/gw`, with a fixed public `x-api-key` — not a secret). It is unofficial and Riot may change it at any time. The script is defensive:

- `leagueId` is resolved from `getLeagues` on every run (matched by slug, never hardcoded).
- On network/API failure it exits and **keeps the previous `.ics`**, never overwriting a subscription with an empty file.
- During the off-season a region with no upcoming matches yields an empty calendar (normal — events reappear when new schedules are published).

Add or remove regions in `OUTPUTS`, and languages in `LANGS`, in `src/main.py` (slugs come from `getLeagues`).

## License

The **code** in this project is released under the [MIT](LICENSE) license.

Schedule data comes from lolesports and is owned by Riot Games and related parties; this project only reformats it, claims no rights over the data, and is neither affiliated with nor endorsed by Riot Games.
