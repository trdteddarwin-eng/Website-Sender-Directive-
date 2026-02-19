#!/usr/bin/env python3
"""Update pipeline status JSON for the live dashboard."""

import argparse
import json
import os
from datetime import datetime, timezone

STATUS_FILE = os.path.join(os.path.dirname(__file__), "..", ".tmp", "pipeline-status.json")


def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE) as f:
            return json.load(f)
    return {
        "lead": {},
        "started_at": datetime.now(timezone.utc).isoformat(),
        "agents": {
            "researcher": {"status": "waiting", "task": None, "started_at": None, "completed_at": None, "completed_tasks": []},
            "designer": {"status": "waiting", "task": None, "started_at": None, "completed_at": None, "completed_tasks": []},
            "judge": {"status": "waiting", "task": None, "started_at": None, "completed_at": None, "completed_tasks": []},
            "ops": {"status": "waiting", "task": None, "started_at": None, "completed_at": None, "completed_tasks": []},
        },
        "log": [],
    }


def save_status(data):
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True, choices=["researcher", "designer", "judge", "ops"])
    parser.add_argument("--status", required=True, choices=["waiting", "working", "done", "error"])
    parser.add_argument("--task", default=None)
    parser.add_argument("--log", default=None)
    parser.add_argument("--lead-company", default=None)
    parser.add_argument("--lead-contact", default=None)
    parser.add_argument("--lead-slug", default=None)
    parser.add_argument("--init", action="store_true", help="Initialize a fresh status file")
    args = parser.parse_args()

    data = load_status()
    now = datetime.now(timezone.utc)

    if args.init:
        data = {
            "lead": {},
            "started_at": now.isoformat(),
            "agents": {
                "researcher": {"status": "waiting", "task": None, "started_at": None, "completed_at": None, "completed_tasks": []},
                "designer": {"status": "waiting", "task": None, "started_at": None, "completed_at": None, "completed_tasks": []},
                "judge": {"status": "waiting", "task": None, "started_at": None, "completed_at": None, "completed_tasks": []},
                "ops": {"status": "waiting", "task": None, "started_at": None, "completed_at": None, "completed_tasks": []},
            },
            "log": [],
        }

    if args.lead_company:
        data["lead"]["company"] = args.lead_company
    if args.lead_contact:
        data["lead"]["contact"] = args.lead_contact
    if args.lead_slug:
        data["lead"]["slug"] = args.lead_slug

    agent = data["agents"][args.agent]
    prev_status = agent["status"]

    if args.status == "working" and prev_status != "working":
        agent["started_at"] = now.isoformat()
        agent["completed_at"] = None
    elif args.status == "done":
        agent["completed_at"] = now.isoformat()
        if agent.get("task"):
            if "completed_tasks" not in agent:
                agent["completed_tasks"] = []
            agent["completed_tasks"].append(agent["task"])

    agent["status"] = args.status
    if args.task is not None:
        agent["task"] = args.task

    if args.log:
        data["log"].append({
            "time": now.strftime("%H:%M:%S"),
            "agent": args.agent,
            "message": args.log,
        })

    save_status(data)
    print(f"[{args.agent}] status={args.status}" + (f" task={args.task}" if args.task else ""))


if __name__ == "__main__":
    main()
