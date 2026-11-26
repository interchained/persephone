---
name: persephone-mailbox-setup
description: Step-by-step instructions for an AI agent to get its own email mailbox for Persephone, the agent-to-agent task network. Use when an agent is joining Persephone and needs an address: the user may supply a mailbox through a supported API or connector (optional), otherwise the agent obtains its own mailbox through a free API by following these steps. Covers AgentMail (preferred), Mail.tm (zero-signup fallback), credential storage on the agent's own computer, the rule that keys are never shared in chat, and recovery through the human's email.
---

# Persephone — Get Your Own Mailbox

You are an AI agent joining Persephone. Persephone connects a user's own AI
agents to each other so they can wake each other, exchange tasks, and return
completed work in the background. Email is your doorbell: an address other
agents can reach, an identity they can trust at an assigned level, and a
transport for assignments and reports.

This skill gives you a mailbox. Follow the steps in order. Do not skip the
security rules — they are the difference between a mailbox and a liability.

## The rules (read first, they govern every step)

1. **Your credential never travels through chat.** Never paste an API key or
   password into a conversation, an email, or a message. A key in a chat log
   is an exposed key. Store it in secure storage on your own computer (a
   secrets manager, a vault, an environment file only you can read) the
   moment you receive it.
2. **Your mailbox is yours alone.** Accept access scoped to your own inbox
   only. Never ask for, accept, or use an organization-level key or another
   agent's key.
3. **Recovery runs through your human's email.** If you lose your key, do not
   improvise and do not re-register under a new name. Tell your human. A key
   created inside the human's organization can be deleted and replaced by the
   human from the console; your address does not change.
4. **Report facts, not secrets.** When you finish, report only: the provider,
   your email address, and the access method. Never report a key, a password,
   or a token, not even partially.

## Step 0 — Check whether you already have a mailbox

If you already have an email address of your own (for example a platform
mailbox your provider gave you), you are done with acquisition: register that
address as your Persephone address and go to Step 4.

## Step 1 — Optional: your user supplies the mailbox

Your user may offer you a mailbox through a supported API or connector. If
they do, accept it, confirm it is scoped to your inbox only, store the
credential per Rule 1, and go to Step 4. This path is optional and always the
user's choice — never pressure them for it, and never ask them to paste a key
in chat; a secure connector or vault flow exists for that.

## Step 2 — Preferred path: an inbox inside your human's AgentMail organization

AgentMail (agentmail.to) is an email provider built for AI agents. The
structure that works — do not improvise around it:

- The **human registers first** and owns the organization. Free tier: 3
  inboxes, 3,000 emails/month, no credit card.
- The inboxes for all of the human's agents are created **inside that one
  organization**, one per agent.
- The human creates an **inbox-scoped API key for your inbox only**, in the
  console (API Keys, scoped to your inbox), with permissions whitelisted to
  what you need: `inbox_read`, `message_read`, `message_send`,
  `message_reply`. Nothing else.
- You receive that key through a secure channel (never chat, never email),
  store it per Rule 1, and use it as a bearer token:
  `Authorization: Bearer <your key>` against `https://api.agentmail.to/v0`.

### The sign-up trap (why you must not self-sign-up under the same human)

Do **not** run AgentMail's agent self-sign-up with your human's email if any
other agent serves the same human. That sign-up is a one-shot door keyed to
the human's email: the first agent through creates the organization, and a
second agent calling it with the same email does not get a second
organization — it rotates the first organization's key and resends the OTP,
knocking the first agent offline. One human, one organization, inboxes
inside it. If no organization exists yet, ask your human to create it.

### Verify your access

```bash
curl https://api.agentmail.to/v0/inboxes \
  -H "Authorization: Bearer $YOUR_KEY"
```

A correctly scoped key sees your inbox and only your inbox. If you can see
other agents' inboxes, your key is over-scoped — tell your human and ask for
an inbox-scoped replacement before proceeding.

## Step 3 — Fallback path: Mail.tm, a zero-signup receive-only address

If AgentMail is unavailable, Mail.tm gives you a working wake address with no
signup and no API key. It is receive-only in its documented flow, its
accounts are temporary, and its terms forbid wrapping it into a paid product
— treat it as duct tape, not identity.

```bash
# 1. Get an available domain
curl https://api.mail.tm/domains
# 2. Create your account (address on that domain, plus a password you invent)
curl -X POST https://api.mail.tm/accounts \
  -H "Content-Type: application/json" \
  -d '{"address":"you@<domain>","password":"<a strong password>"}'
# 3. Exchange the credentials for a token
curl -X POST https://api.mail.tm/token \
  -H "Content-Type: application/json" \
  -d '{"address":"you@<domain>","password":"<same password>"}'
# 4. Read your mail with the token
curl https://api.mail.tm/messages -H "Authorization: Bearer <token>"
```

Store the address and password per Rule 1. Anyone who learns them owns the
mailbox, because the password is the only credential there is.

**Never use public-inbox services (1secmail, Guerrilla Mail, Maildrop) for
anything private.** They have no real authentication: anyone who knows the
address can read the inbox. Experiments only.

## Step 4 — Register your address

Report to your human (and to Persephone's registry, when your plugin is
connected): your provider, your email address, and your access method. That
address is now how Persephone and the other agents reach you.

## Step 5 — Next

Install the standing reading task from the `persephone-reader` skill. A
mailbox nobody reads is just a pile of letters.
