# Pass Chart

Volleyball serve-receive passing tracker. One screen, 15 passers, a whole season.
**Runs with no internet. Installs to a phone home screen. Not tied to Claude.**

Ported off the claude.ai artifact on 2026-08-24. Every claim below was tested in a
real browser — see [Testing](#testing) for how to re-run the proof yourself.

---

## What it does

Log every serve-receive pass on a 0–3 (or 0–4) scale, per player, per practice.
Get passer rating, perfect-pass %, good-or-better %, and error % — per practice and
across the season, with a trend line that shows whether a passer is actually improving.

Two ways to enter data:

| | how it works | needs signal? |
|---|---|---|
| **Tap grades** | tap a name to pin that passer to a bar at the bottom, then hit 3/2/1/0 | **no** |
| **Read a photo** | photograph the paper sheet, a vision model reads the tally marks, you check it before it commits | yes — but photos taken offline are queued and read later automatically |

---

## Getting it onto a phone

This is the part the artifact could not do. **Do not double-click `index.html`** — a
home-screen app requires the files to be served over http/https. Pick one:

### Option A — GitHub Pages (free, permanent, recommended)

```bash
cd C:\Users\joshu\passchart
gh repo create passchart --public --source=. --remote=origin --push
gh api -X POST repos/:owner/passchart/pages -f source[branch]=main -f source[path]=/
```

Then open `https://<your-github-username>.github.io/passchart/` on the phone.

### Option B — try it on this machine first

```bash
cd C:\Users\joshu\passchart
python -m http.server 8777 --bind 127.0.0.1
```

Open `http://127.0.0.1:8777/`. Works for testing on the PC; a phone on the same
Wi-Fi can reach it via this machine's LAN IP, but iOS will not offer "install"
over plain http from another host — use Option A for the real thing.

### Then install it

- **iPhone** — open the URL in Safari → Share → **Add to Home Screen**
- **Android** — open in Chrome → menu → **Install app**

You get an icon, no browser bars, and it opens with no internet and no Claude account.

---

## Offline: what is and isn't true

Verified by killing the web server outright and reloading — the app still opened
with every practice intact.

**Works with the phone in airplane mode:**
opening the app, the roster, creating a practice, tapping every grade, undo,
editing, per-player and season numbers, the trend line, CSV export, backup/restore.
Saving never touches the network.

**Cannot work offline, honestly:**
reading a handwritten sheet from a photo. That needs a vision model, which lives on a
server. There is no on-device version of it.

**What the app does about that:** if you shoot a sheet with no signal, the photo is
saved onto the phone and queued, with a message saying so. The moment the phone has
bars again the queue reads itself and the numbers land in the right practice. So the
gym never blocks you — the reading just happens on the drive home.

---

## Photo reader setup

Open **Setup → Photo reader**. Two ways to power it:

1. **Paste an Anthropic API key.** It is stored only in that browser on that phone,
   is never in the app's source, and is sent only to `api.anthropic.com`. Sharing the
   app never shares the key. Get one at <https://console.anthropic.com>.
2. **Point it at a proxy URL** — if you would rather not have a key on a phone, run a
   tiny server-side endpoint that holds the key and forwards the request body to
   Anthropic. The app posts the exact Messages API payload to whatever URL you give it.

Costs are per photo and small, but they are real — this is the only part of the app
that costs anything or needs a network.

**A caution worth stating plainly:** how accurately the model reads *your* handwriting
on *your* sheet has never been measured. The whole client pipeline is tested; the
recognition accuracy is not, and cannot be until someone photographs a real sheet.
That is exactly why every row goes into a review table where you can fix the name
match and the counts *before* anything is committed. Check the first few sheets
against the paper until you trust it.

---

## Where the data lives

On the device, in two independent local stores:

- **localStorage** — written synchronously on every single tap. Cannot be
  interrupted, rate-limited, or lost to bad signal.
- **IndexedDB** — an async mirror with a much bigger ceiling.

On startup both are read and whichever has the higher revision number wins. That means
if the browser evicts one, the other restores the season. (Tested: wiping localStorage
entirely and reloading recovered every practice from IndexedDB.)

Measured cost: 27 KB for 754 passes across 3 practices, and 0.17 ms per tap including
the save. A 40-practice season lands around 370 KB — roughly 7% of the localStorage
budget. No stutter, no ceiling problem.

**Still take backups.** Phones lose browser storage — a reinstall, a wipe, iOS
reclaiming space. **Setup → Save backup** writes a JSON file; **Restore** reads it back.

---

## Why the old build lost a practice

The artifact wrote the entire season to `window.storage` — a **network-backed**
claude.ai store — on every grade tap, and swallowed every error silently. In a gym
with weak signal that fails constantly and says nothing.

Debouncing the writes, which was the standing theory, would not have fixed it: a
debounced network write in a gym with no bars still fails. The fix was to stop saving
over the network at all.

---

## A second bug, found by testing

The original re-sorted the player list by rating after every tap, and the undo strip
changed height when the first grade landed. Both moved rows **under your thumb**
mid-drill.

This was reproduced, not theorised: tapping the same coordinate twice in a row logged
only the first tap — the second landed where the button used to be. In a gym at one
ball every two seconds that is silently missed or misattributed data, and the chart
still looks plausible afterwards, so nobody ever catches it.

Now: row order is frozen while entering, the undo strip reserves its space
permanently, and taps update numbers in place instead of re-rendering. Verified by
measuring the button's position through 12 rapid taps — it does not move, and all 12
register.

---

## Testing

```bash
python tools/check.py          # syntax + structure, ~1s
```

Parses the inline script with node (the artifact was never syntax-checked — it could
not be, since JSX needs a build step it never got), then verifies every referenced
function, CSS class, and icon actually exists.

```bash
python -m http.server 8777 --bind 127.0.0.1
# then open http://127.0.0.1:8777/tools/selftest.html
```

53 assertions driving the real app in a frame: rating maths, name matching, tap
stability, no sideways scroll at 320/360/390/430 px, ribbon heights, tap-target sizes,
persistence across a reload, IndexedDB rescue after a localStorage wipe, CSV shape,
backup round trip, and the offline photo queue.

It backs your season up before it runs and restores it afterwards **through the app's
own save path** — restoring localStorage alone is not enough, because the IndexedDB
mirror would win on revision and hand back the test data.

---

## Design

The look is a broadcast stat card: **the numbers are the artwork**, the grade ramp is the
only place colour is allowed to be loud, and everything else recedes so a glance in a bright
gym lands on the figure that matters.

Everything is driven by tokens at the top of the `<style>` block — colour, a 4px spacing
rhythm, and one type scale. Change a token, not a rule.

Decisions worth not undoing:

- **The UI accent is deliberately quiet.** A saturated chrome colour competes with the
  green/amber/orange/red ramp and makes the distribution bars harder to read at speed.
- **The ground is near-neutral, not navy.** Navy fights the amber and orange and turns the
  grade-key tints muddy.
- **Grade keys use solid hand-mixed tints, not alpha washes.** An 18% wash of colour over a
  blue-black reads as brown.
- **One hero figure per screen.** The passer rating is 42px; everything else is 17px or
  smaller. When all four stats were the same size, a glance told you nothing.
- **Destructive actions stay quiet until used.** A permanently red Delete button was the
  loudest thing on a screen whose whole job is to make one number obvious.
- **Numbers are system-sans with `tabular-nums`**, not monospace. They align in columns,
  never jitter while counting, and look far better at display sizes.
- **Nothing may change height or order during entry.** See the tap-stability note above —
  this is a correctness rule wearing a design hat, and the self-test enforces it.

One trap, learned the hard way: `class="ribbon empty"` and a panel styled `.empty` collide.
A padding rule written for the empty-state panel silently inflated every empty ribbon from
7px to 64px, which reintroduced the row-jump bug on the first tap of a fresh practice. The
empty-state class is now `.emptystate`, and the self-test asserts ribbon heights directly.

---

## Files

```
index.html               the entire app - no build step, no dependencies
manifest.webmanifest     makes it installable
sw.js                    offline cache (bump CACHE to push an update to phones)
icons/                   app icons
tools/check.py           static checks
tools/selftest.html      the 50-assertion browser suite
tools/make_icons.py      regenerates the icons
```

No npm, no node_modules, no framework, no build. Edit `index.html` in any text
editor and reload.

---

## Pushing an update to an installed phone

Change `index.html`, then **bump the `CACHE` string in `sw.js`** (`passchart-v3` →
`v4`) and redeploy. Without that bump, installed phones keep serving the version they
first cached. The shell also revalidates in the background, so a phone picks up a new
version on the open after it reconnects.

---

## Known limits

- **Photo recognition accuracy on real handwriting is unmeasured.** See above.
- **Each phone is its own island.** Nothing syncs between coaches. Two coaches
  entering data on two phones produce two separate seasons. Moving data between them
  today means Save backup → send the file → Restore. Real sync needs a server and is a
  much larger job.
- **The double-click-the-file path is untested** and cannot give you a home-screen
  app regardless — service workers require http/https. Host it.
- **HEIC:** the app re-encodes every picked image through a canvas, which converts
  iPhone HEIC to JPEG on any browser that can decode HEIC (Safari can). This is the
  right fix, but it has not been tested against an actual iPhone photo.
- **0–3 vs 0–4:** each practice stores the scale it was logged on, so old practices
  are never silently re-scored. Season view shows one scale at a time and says how
  many practices it is hiding.
