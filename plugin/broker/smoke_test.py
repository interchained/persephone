#!/usr/bin/env python3
"""End-to-end smoke test for the Persephone reference broker.

Proves the cross-agent review loop the v1 plan names as the first workflow:
register two agents, Agent A creates a task, Agent B claims it, hands a
review step back, completes it with an artifact, and the report shows the
whole trail.

Usage: python3 smoke_test.py http://127.0.0.1:8790
"""
import json
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8790"


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def check(label, condition):
    print(("PASS" if condition else "FAIL"), "-", label)
    if not condition:
        sys.exit(1)


identity = call("GET", "/")
check("identity names Persephone by Interchained", identity["name"] == "Persephone" and "Interchained" in identity["by"])
check("identity links interchained.tech", identity["homepage"] == "https://interchained.tech")

call("POST", "/tools/register_agent", {"name": "oracle", "platform": "chatgpt",
                                       "mailbox": "interchained@agentmail.to",
                                       "capabilities": ["critique", "review"]})
call("POST", "/tools/register_agent", {"name": "grokbot", "platform": "grok-bot",
                                       "mailbox": "grokbot-interchained@agentmail.to",
                                       "capabilities": ["drafting", "research"]})
agents = call("GET", "/agents")
check("registry holds both agents", len(agents["agents"]) == 2)

task = call("POST", "/tools/create_task",
            {"title": "Review the Persephone plan", "instructions": "Critique it independently.",
             "assign_to": "grokbot", "limits": {"max_iterations": 3}})["task"]
check("task starts queued", task["status"] == "queued")

claim = call("POST", "/tools/claim_task", {"task_id": task["task_id"], "agent": "grokbot"})
check("first claim wins", claim["claimed"] is True)
again = call("POST", "/tools/claim_task", {"task_id": task["task_id"], "agent": "oracle"})
check("second claim is refused", again["claimed"] is False)

handoff = call("POST", "/tools/handoff_task",
               {"task_id": task["task_id"], "to_agent": "oracle",
                "instructions": "Independently challenge the draft's assumptions."})
check("handoff creates a follow-on task", handoff["follow_on_task"]["assigned_to"] == "oracle")

done = call("POST", "/tools/complete_task",
            {"task_id": task["task_id"], "agent": "grokbot",
             "artifact": "Draft v1, ready for the Oracle's critique."})
check("completion records the artifact", done["task"]["status"] == "completed" and bool(done["task"]["artifact"]))

report = call("POST", "/tools/get_report", {"task_id": task["task_id"]})
events = [entry["event"] for entry in report["log"]]
check("report log shows created, claimed, handoff, completed",
      events == ["created", "claimed", "handoff", "completed"])

queue = call("POST", "/tools/list_tasks", {"status": "queued"})
check("oracle's follow-on task waits in the queue", queue["count"] == 1)

print("SMOKE TEST PASSED — Persephone broker by Interchained, https://interchained.tech")
