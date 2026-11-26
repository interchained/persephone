#!/usr/bin/env python3
"""Persephone reference task broker — by Interchained (https://interchained.tech).

A durable JSON task store behind the Persephone plugin's tool surface.
Persephone owns workflow state only: no model, no inference, no account
credentials. Agents call the tools; host platforms gate the work.

Usage:
    python3 persephone_broker.py [--port 8790] [--store tasks.json]

Endpoints:
    GET  /                  identity (name, company, version)
    POST /tools/<tool>      call a plugin tool with a JSON object body
    GET  /agents            the agent registry
    GET  /tasks             the full board (same as list_tasks with no filter)
"""
import argparse
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

IDENTITY = {
    "name": "Persephone",
    "by": "Interchained LLC",
    "homepage": "https://interchained.tech",
    "license": "MIT",
    "tagline": "Persephone doesn't replace your AI. She makes your AI work together.",
}

STATUSES = ["queued", "claimed", "working", "blocked", "completed", "cancelled"]


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        if os.path.exists(path):
            with open(path) as f:
                self.data = json.load(f)
        else:
            self.data = {"agents": {}, "tasks": {}}
            self.save()

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.data, f, indent=2)
        os.replace(tmp, self.path)


STORE = None


def log(task, event, detail):
    task["log"].append({"at": now(), "event": event, "detail": detail})


def tool_register_agent(args):
    name = args["name"]
    STORE.data["agents"][name] = {
        "name": name,
        "platform": args["platform"],
        "mailbox": args["mailbox"],
        "capabilities": args.get("capabilities", []),
        "registered_at": now(),
    }
    STORE.save()
    return {"agent": STORE.data["agents"][name]}


def tool_create_task(args):
    task_id = "task-" + uuid.uuid4().hex[:8]
    task = {
        "task_id": task_id,
        "title": args["title"],
        "instructions": args["instructions"],
        "status": "queued",
        "assigned_to": args.get("assign_to"),
        "claimed_by": None,
        "parent": args.get("parent"),
        "limits": args.get("limits", {}),
        "artifact": None,
        "created_at": now(),
        "log": [],
    }
    log(task, "created", args["title"])
    STORE.data["tasks"][task_id] = task
    STORE.save()
    return {"task": task}


def tool_list_tasks(args):
    tasks = list(STORE.data["tasks"].values())
    if args.get("status"):
        tasks = [t for t in tasks if t["status"] == args["status"]]
    if args.get("assigned_to"):
        tasks = [t for t in tasks if t.get("assigned_to") == args["assigned_to"]
                 or t.get("claimed_by") == args["assigned_to"]]
    return {"count": len(tasks), "tasks": tasks}


def get_task(task_id):
    task = STORE.data["tasks"].get(task_id)
    if task is None:
        raise KeyError(f"no such task: {task_id}")
    return task


def tool_claim_task(args):
    task = get_task(args["task_id"])
    if task["status"] != "queued":
        return {"claimed": False, "reason": f"task is {task['status']}", "task": task}
    task["status"] = "claimed"
    task["claimed_by"] = args["agent"]
    log(task, "claimed", args["agent"])
    STORE.save()
    return {"claimed": True, "task": task}


def tool_update_task(args):
    task = get_task(args["task_id"])
    if args.get("status"):
        task["status"] = args["status"]
        log(task, "status", args["status"])
    if args.get("note"):
        log(task, "note", args["note"])
    STORE.save()
    return {"task": task}


def tool_handoff_task(args):
    task = get_task(args["task_id"])
    log(task, "handoff", f"to {args['to_agent']}: {args['instructions']}")
    STORE.save()
    follow = tool_create_task({
        "title": task["title"],
        "instructions": args["instructions"],
        "assign_to": args["to_agent"],
        "parent": task["task_id"],
    })
    return {"task": task, "follow_on_task": follow["task"]}


def tool_complete_task(args):
    task = get_task(args["task_id"])
    task["status"] = "completed"
    task["artifact"] = args["artifact"]
    log(task, "completed", f"by {args.get('agent', task.get('claimed_by'))}: artifact recorded")
    STORE.save()
    return {"task": task}


def tool_cancel_task(args):
    task = get_task(args["task_id"])
    task["status"] = "cancelled"
    log(task, "cancelled", args.get("reason", ""))
    STORE.save()
    return {"task": task}


def tool_get_report(args):
    task = get_task(args["task_id"])
    return {
        "task_id": task["task_id"],
        "title": task["title"],
        "status": task["status"],
        "claimed_by": task.get("claimed_by"),
        "artifact": task.get("artifact"),
        "log": task["log"],
    }


TOOLS = {
    "register_agent": tool_register_agent,
    "create_task": tool_create_task,
    "list_tasks": tool_list_tasks,
    "claim_task": tool_claim_task,
    "update_task": tool_update_task,
    "handoff_task": tool_handoff_task,
    "complete_task": tool_complete_task,
    "cancel_task": tool_cancel_task,
    "get_report": tool_get_report,
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Persephone-By", "Interchained - https://interchained.tech")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(200, {**IDENTITY, "tools": sorted(TOOLS)})
        elif self.path == "/agents":
            self._send(200, {"agents": list(STORE.data["agents"].values())})
        elif self.path == "/tasks":
            with STORE.lock:
                self._send(200, tool_list_tasks({}))
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self.path.startswith("/tools/"):
            self._send(404, {"error": "not found"})
            return
        tool = self.path[len("/tools/"):]
        if tool not in TOOLS:
            self._send(404, {"error": f"no such tool: {tool}"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            args = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "body must be a JSON object"})
            return
        with STORE.lock:
            try:
                result = TOOLS[tool](args)
            except KeyError as e:
                self._send(404, {"error": str(e)})
                return
            except Exception as e:  # missing required fields etc.
                self._send(400, {"error": str(e)})
                return
        self._send(200, result)

    def log_message(self, *args):
        pass


def main():
    global STORE
    parser = argparse.ArgumentParser(description="Persephone reference task broker")
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--store", default=os.path.join(os.path.dirname(__file__), "tasks.json"))
    args = parser.parse_args()
    STORE = Store(args.store)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Persephone broker by Interchained listening on http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
