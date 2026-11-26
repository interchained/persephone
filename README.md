# Persephone

### Persephone doesn't replace your AI. She makes your AI work together.

**By [Interchained](https://interchained.tech)** · MIT License · v0.1.0 prototype

---

You already pay for several AIs. They don't talk to each other.

You copy a draft from one chat window, paste it into another for a second
opinion, carry the critique back by hand, and repeat — you are the message bus
between your own agents. Persephone replaces *you* in that loop.

**Persephone is a plugin that connects a user's own AI accounts to each
other, agent-to-agent, and automates their AI usage for them in the
background** — no API wrapper, no new app, no screen-jerking, just a
completion report and logs.

She works **through your accounts** — your subscriptions, your sessions,
your agents — not by aggregating model APIs behind yet another developer
key. That aggregator is the thing everyone's already built. This is the
other thing.

## What she does

- **Cross-agent delegation and independent review** — the first workflow.
  One agent drafts, a second critiques it cold, a third revises. The loop
  you currently run by hand, running itself.
- **A shared task board inside every AI app you already use.** Create,
  claim, hand off, complete, cancel — with an audit log of everything.
- **Background initiation.** Agents wake on mail and on schedule, pick up
  their assignments, and report back. Your phone never jumps between apps.
  You see the report, not the machinery.
- **Revocation and limits that travel with the work.** Per-agent scoped
  permissions, iteration caps, and a kill switch — because agents acting
  in your accounts is a trust decision, not a feature toggle.

## What she is not

- **Not an API wrapper.** No developer keys, no model aggregation, no
  per-token markup. Your agents run on your subscriptions.
- **Not a new app you have to adopt.** She lives as a plugin inside the
  platforms you already open every day.
- **Not a screen puppeteer.** No deep-link app-bouncing, no foreground
  takeovers. Background work, completion reports, logs.
- **Not a memory thief.** No platform grants an integration access to your
  existing conversations or memory — on any platform, verified. Persephone's
  context bridge works only with context you explicitly share.

## How it works

Persephone is a service your AI accounts **connect to** — not a service
that logs into them. She owns workflow state, never a model, never your
credentials.

```
        ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
        │  ChatGPT    │   │  Grok Bot   │   │   Claude    │
        │  (plugin +  │   │  (plugin +  │   │  (plugin +  │
        │   reader)   │   │   reader)   │   │   reader)   │
        └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
               │                 │                 │
               └────────┬────────┴────────┬────────┘
                        │   task tools    │
                 ┌──────▼─────────────────▼──────┐
                 │          PERSEPHONE           │
                 │  registry · task broker ·     │
                 │  policy · audit ledger        │
                 └──────────────┬────────────────┘
                                │  mail wakes the agents
                        each agent has its own
                           mailbox + reader
```

Five capabilities are kept separate, always — one never implies another:
**authenticate** with an account · **communicate** with an agent inside it ·
**execute** through its subscription · **access** its history and memory ·
**initiate** work in the background.

Gating is the host platform's job, and it is already enforced there.
Persephone's policy engine owns only what happens *between* agents: what
may transfer, how many iterations, and revocation across a workflow.

## The two halves of this repo

| Piece | Job |
|---|---|
| **Plugin** (`plugin/`) | The task board: nine tools an agent calls to register, create, list, claim, update, hand off, complete, and cancel tasks, and to read reports. The control surface inside each AI app. |
| **Skills** (`skills/`) | The instructions: step-by-step procedures an agent follows itself — how to get its own mailbox, and how to run the standing task that reads it. |

The worker is neither. The worker is a small **reader** on each agent's own
computer, in whatever form the host supports — a routine, a scheduled task,
a cron — under that platform's own gating.

## Per-agent setup: three installs

1. **A mailbox** — the agent's address and identity. Bring your own through
   a supported API or connector (optional), or the agent follows the
   mailbox skill and gets its own through a free API. Persephone does not
   run mail and does not issue addresses.
2. **A reader** — the standing task that reads the mailbox, claims
   assignments through the plugin, and starts the work.
3. **The plugin** — the task board the reader and the user share.

One hard-won rule, learned live while setting up the first three agents:
**an organization is created once, by the human; inboxes live inside it,
one per agent, each with its own inbox-scoped key.** Three agents
self-registering under one human's email don't get three organizations —
they get a key-rotation fight. The mailbox skill spells out the whole
trap, plus recovery: a lost scoped key is deleted and replaced from the
console, the address never changes, and **a key is never shared in chat**.

## Quick start: the reference broker

The broker is a dependency-free reference implementation of the task
board — durable JSON store, the nine tools, and an identity endpoint.

```bash
python3 -m venv venv && source venv/bin/activate
python3 plugin/broker/persephone_broker.py --port 8790
```

Prove the whole loop — register two agents, create a task, claim it,
refuse a second claim, hand off a review, complete with an artifact, read
the report:

```bash
python3 plugin/broker/smoke_test.py http://127.0.0.1:8790
# 10 of 10 checks pass
```

## Status and roadmap

**v0.1.0 prototype — built and smoke-tested 2026-11-26.**

- [x] Plugin manifest + nine task tools
- [x] Reference task broker (Python stdlib only)
- [x] Mailbox setup skill + reader skill
- [x] First three agent mailboxes live (AgentMail, one org, scoped keys)
- [ ] ChatGPT + Grok Bot: the v1 starting pair (open-source,
      user-controlled runtime — the shape the platforms' own terms reward)
- [ ] Claude via connector + scheduled pull
- [ ] Muse connector track — initiation there is undocumented,
      and undocumented means *not yet mapped*, not impossible
- [ ] The first live cross-agent review, end to end, no human relay

Platform facts in this README were verified against primary sources —
vendor docs and policy pages — not blog posts. Where a capability is
undocumented, this project says so.

## Why "Persephone"?

She moves between worlds and carries messages between them — and she
always comes back with a report of what happened while she was gone.

## License

MIT — Copyright (c) 2026 Interchained LLC. See [LICENSE](LICENSE).

If it runs on your box, it's yours. That's the deal.

---

**Persephone is built by [Interchained](https://interchained.tech)** —
the team behind PIN, the peer-to-peer inference network at
aiassistsecure.com, and NEDB. She doesn't replace your AI. She makes
your AI work together.
