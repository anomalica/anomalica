# The instrument answers in the expected shape

**A tool that cannot answer your question will often answer a different one
in exactly the shape you expected, and nothing distinguishes the two.** The
reading looks plausible, the command exits zero, and the wrong answer is
adopted without ever being questioned - because it arrived in the format
that a right answer would have arrived in.

This is a sibling of [absence is not a verdict](absence-is-not-a-verdict.md).
That note is about a *gap* being read as a finding. This one is about a
*confident wrong reading* produced by the instrument itself. The tell is the
same in both: at no point does anything fail.

Instances found while chasing unrelated faults, none by looking for this
pattern. The first three landed in a single evening, 2026-08-22.

| Instrument | Question asked | What it actually answered | Read as |
|---|---|---|---|
| `systemctl --user is-active` | Is the backend healthy? | Is a unit currently in a start attempt? | Healthy - through **129 consecutive restarts** |
| `dict.get("utilisation", 0)` | What is the GPU doing? | Nothing; the key is `util` | A real, precise **0%** while the card was pinned at 100% |
| `ps -o args= \| cut -c1-95` | What is the full command line? | The first 95 characters of it | `--reload-dir backend` truncated to `--reload`, then reported as a duplicated flag |
| `ls sidecar record 2>/dev/null` | Does this sidecar have no record? | Do **both** globs match? | ~90 confident orphans, of which one was real |

## Why each one is invisible

**`is-active` on a restart-looping unit.** `Restart=on-failure` means the
unit is genuinely active for most of any sampling window - it is starting,
failing, and starting again. `is-active` reports the instantaneous state
truthfully; the operator asked a question about *steady* state that the
command does not answer. The unit had failed to bind port 8001 for hours
because a manually-started `uvicorn` from an unrelated session held it, and
the log recorded only `[Errno 98] address already in use` - the squatter's
own output went to the session that started it, not to the unit's log.

The instruments that do answer:

```bash
ss -lptn 'sport = :8001'                      # who actually holds the port
systemctl --user show -p NRestarts --value anomalica-scheduler.service
journalctl --user -u anomalica-scheduler.service | grep -c 'Scheduled restart'
```

Compare the owning pid's parent against the unit's `MainPID`. A parent of
`claude ...` or a shell-snapshot wrapper means a session squatted it.

**A defaulting lookup on a mistyped key.** `gpu.status()` returns `util`;
the caller read `utilisation` and supplied `0` as the default. A missing key
that returns a default is indistinguishable from a real zero, and `0%` is a
value the reader is entirely willing to believe. Nothing raises, nothing
logs, and the panel renders a number with full confidence. Prefer a lookup
that fails loudly at the boundary, or assert the key exists in a test - the
fix belongs at the read, not at the display.

**A truncating pipeline.** `cut -c1-95` landed mid-argument. The output was
then treated as evidence *about the invocation* rather than as evidence
about the truncation, and a non-existent duplicated flag was reported to
another component. `/proc/PID/cmdline` cannot lie and costs nothing:

```bash
tr '\0' '\n' < /proc/PID/cmdline
```

## Prefer the instrument that reads the thing over one that reads a rendering

In every case above there was a cheaper instrument that could not lie:

| Instead of | Read | Because |
|---|---|---|
| `ps \| cut` | `/proc/PID/cmdline` | The argv itself, not a width-limited rendering of it |
| `systemctl is-active` | `ss -lptn`, `NRestarts` | Who holds the port, not who is mid-attempt |
| `.get(key, default)` on a parsed dict | the field, asserted in a test | A default is indistinguishable from a real value |

The rule is not "be more careful" - it is **prefer the instrument that reads
the thing itself over one that reads a rendering of it**. The rendering is
nearly always the one nearest to hand, which is why it keeps winning.

The same rule is stated one layer down in
[ingest-format.md](../architecture/ingest-format.md), which gives both forms
in order - test the position first, and where no positional test exists:

> **Test the least lossy value available at that point** - the name wherever
> a name exists, a derived form like a slug only where nothing else does. A
> component far downstream receives derivatives rather than originals, and
> the lossy one is usually the one nearest to hand: `[interviewer 2]`
> slugifies to `interviewer-2`, indistinguishable from a legitimate slug,
> while the display title beside it still carries the brackets exactly as it
> carries the accent in "Jacques Vallée".

Same rule, different layer: a slug is a rendering of a name the way `ps`
output is a rendering of an argv.

### A fourth instance, while writing this note

The `ps | cut` row above was not the last one. Verifying that quotation, this
note's author ran `grep -rn 'lossy' architecture/ | cut -c1-230`, and the cut
landed before the phrase "least lossy" - so the passage appeared to contain
only the position-not-notation guard. On that basis another component was
told its citation was substantively wrong. It was not; only its filename was.

The same instrument, the same blind spot, twice in one evening, the second
time while documenting the first. Reading the line without a width limit
settles it in one command:

```bash
grep -rn 'lossy' architecture/ | fold -w 100 -s   # never | cut
```

Which is the practical form of the whole note: a width limit is a rendering
choice, and applying one to evidence turns the evidence into a rendering too.

Related, all the same family seen from the *code* side rather than the
instrument side:
[absence is not a verdict](absence-is-not-a-verdict.md),
[a condition that cannot fire](a-condition-that-cannot-fire.md),
[an allow-list drops the next field](an-allow-list-drops-the-next-field.md),
[measuring tells you what is, not what survives](measuring-tells-you-what-is-not-what-survives.md).

## A fifth: an exit code answering a compound question

The instances above are *partial* answers - a truncation, a defaulted key. This
one is different in mechanism and worth separating, because no value is
truncated and nothing is missing.

Sweeping `ingests/store` for sidecars whose record had gone, the test was:

```bash
ls ${h}*.md v1/${h}*.md >/dev/null 2>&1 || echo "orphan: $h"
```

`ls` exits non-zero when **either** argument matches nothing. So it answers "do
both of these exist?", while the question asked was "does the sidecar exist
without a record?". Every record that was live but had no archived twin - the
overwhelming majority - failed the test and was reported as an orphan. About
ninety of them, each one a plausible-looking hash.

Redone against explicit sets, the real answer was **one**:

```python
live = {p.name.split(".")[0] for p in store.glob("*.md")}
orphans = [p for p in store.glob("*.json") if p.name.split(".")[0] not in live]
```

The general form: **a compound command collapses several conditions into one
exit code, and the code cannot say which condition failed.** Any shell test
whose subject is more than one thing has this property. It is the same family
as a width limit - both discard the distinction you were about to reason from -
but it arrives without any visible truncation to notice.

**The tell was recognition, not the instrument**, which is the uncomfortable
part. The list was believable and internally consistent; what broke it was
spotting records that had been read by hand an hour earlier and were certainly
not orphans. That is luck dressed as diligence. It would not have worked on
unfamiliar data, and it is not a check anybody can plan to perform - which is
the argument for testing the sets directly rather than hoping to notice.

The near-miss was the more expensive half. The false count was about to be
written into a component's design as a permanent documented exception - a false
rule, in the place people go to look up rules, where nothing would have
questioned it again.

## A process can outlive the shell that owns it

The port collision above needed a long-lived process nobody was
supervising. Note that the usual recipe does *not* cause this: the
workbench's `just dev` runs both halves under `trap 'kill 0' EXIT`, so they
are meant to share a lifetime and normally do.

They diverge only when one half is killed and restarted **by hand** - the
restarted half is then parented by that session's shell, and outlives it.
Whether that costs anything depends entirely on whether something else
wants the port:

- Workbench: no systemd unit exists, so an unsupervised backend on :8073 is
  simply the backend. Benign.
- Scheduler: a systemd unit wants :8001, so a hand-started `uvicorn` there
  locked the unit out of its own port and produced the 129-restart loop.

A supervised unit per long-lived service removes the class rather than the
instance.

## Recognising it

Ask what the instrument *can* distinguish before trusting what it reports.
If the tool cannot tell the two cases apart, its confident answer is not
evidence - and it will be wrong in the direction you expected, which is why
it survives review.
