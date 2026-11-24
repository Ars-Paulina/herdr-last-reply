#!/usr/bin/env python3
"""Put the time of each agent's last reply next to it in herdr's Agents list.

When a pane's agent goes from "working" to anything else (done, idle, blocked), the pane and
its workspace get a `$last` metadata token with the clock time, e.g. "4:12 PM". Show it with a
`{ token = "$last" }` entry in [ui.sidebar.agents] and [ui.sidebar.spaces] rows.

One-shot: herdr runs this on startup and on every pane.agent_status_changed event.
The last seen status per pane lives in state.json, so a transition is caught even though
the event payload is not read. Flag: --test (self-check).
"""
import fcntl, json, os, socket, sys, time

SOCK = os.environ.get("HERDR_SOCKET_PATH") or os.path.expanduser("~/.config/herdr/herdr.sock")
HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.environ.get("HERDR_PLUGIN_STATE_DIR") or HERE
STATE = os.path.join(STATE_DIR, "state.json")
SOURCE = "last-reply"


def call(method, params=None):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(5)
        s.connect(SOCK)
        s.sendall((json.dumps({"id": "lr", "method": method, "params": params or {}}) + "\n").encode())
        r = json.loads(s.makefile().readline())
    if "error" in r:
        raise RuntimeError(r["error"])
    return r["result"]


def stamp(t=None):
    # ponytail: clock time only; a reply from an earlier day shows its weekday instead of a date
    t = time.localtime(t)
    now = time.localtime()
    hm = time.strftime("%I:%M %p", t).lstrip("0")
    return hm if t[:3] == now[:3] else time.strftime("%a ", t) + hm


def changes(panes, seen):
    """Return ({pane_id: status} to save, [pane_id that just finished a turn])."""
    status = {p["pane_id"]: p.get("agent_status") for p in panes if p.get("agent")}
    finished = [pid for pid, s in status.items() if seen.get(pid) == "working" and s != "working"]
    return status, finished


def main():
    if "--test" in sys.argv:
        panes = [{"pane_id": "a", "agent": "claude", "agent_status": "done"},
                 {"pane_id": "b", "agent": "claude", "agent_status": "working"},
                 {"pane_id": "c", "agent": "claude", "agent_status": "idle"},
                 {"pane_id": "d", "agent": None, "agent_status": None}]
        status, finished = changes(panes, {"a": "working", "b": "working", "c": "idle", "gone": "working"})
        assert finished == ["a"], finished  # only working -> not working counts
        assert status == {"a": "done", "b": "working", "c": "idle"}, status  # closed and agent-less panes dropped
        assert stamp(time.time()).endswith(("AM", "PM")) and " " in stamp(time.time() - 3 * 86400)
        return print("ok")
    with open(os.path.join(STATE_DIR, "last-reply.lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # events come in bursts: one run at a time
        try:
            with open(STATE) as f:
                seen = json.load(f)
        except (OSError, ValueError):
            seen = {}
        panes = call("pane.list")["panes"]
        status, finished = changes(panes, seen)
        workspace = {p["pane_id"]: p.get("workspace_id") for p in panes}
        for pid in finished:
            now = stamp()
            call("pane.report_metadata", {"pane_id": pid, "source": SOURCE, "tokens": {"last": now}})
            if workspace.get(pid):  # the latest reply of any agent in the space
                call("workspace.report_metadata", {"workspace_id": workspace[pid], "source": SOURCE, "tokens": {"last": now}})
        with open(STATE + ".tmp", "w") as f:
            json.dump(status, f)
        os.replace(STATE + ".tmp", STATE)


if __name__ == "__main__":
    main()
