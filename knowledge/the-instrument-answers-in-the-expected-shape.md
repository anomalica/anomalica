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

Three instances found in a single evening, 2026-08-22, each while chasing a
different fault, none found by looking for this pattern.

| Instrument | Question asked | What it actually answered | Read as |
|---|---|---|---|
| `systemctl --user is-active` | Is the backend healthy? | Is a unit currently in a start attempt? | Healthy - through **129 consecutive restarts** |
| `dict.get("utilisation", 0)` | What is the GPU doing? | Nothing; the key is `util` | A real, precise **0%** while the card was pinned at 100% |
| `ps -o args= \| cut -c1-95` | What is the full command line? | The first 95 characters of it | `--reload-dir backend` truncated to `--reload`, then reported as a duplicated flag |

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

The same rule appears one layer down in
[ingest-format.md](../architecture/ingest-format.md), as a guard written
against *position* rather than *notation*: enumerating the notations a
construct might use misses the next one silently, so test the structural
fact instead - a speaker description is the whole value of its comment,
which is what identifies it, not the punctuation it happens to carry.

Related, all the same family seen from the *code* side rather than the
instrument side:
[absence is not a verdict](absence-is-not-a-verdict.md),
[a condition that cannot fire](a-condition-that-cannot-fire.md),
[an allow-list drops the next field](an-allow-list-drops-the-next-field.md),
[measuring tells you what is, not what survives](measuring-tells-you-what-is-not-what-survives.md).

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
