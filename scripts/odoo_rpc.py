#!/usr/bin/env python3
"""Thin Odoo JSON-RPC client for the ODOO-functional-skills examples.

Stdlib only (no `odoo` package needed). Works against Odoo Online and on-prem /
Odoo.sh. Authenticates once per invocation and forwards one model method call.

Credentials come from the environment (never hardcode them):

    ODOO_URL       base URL, e.g. https://mycompany.odoo.com
    ODOO_DB        database name
    ODOO_USER      login (email)
    ODOO_PASSWORD  API key (preferred) or password

Usage:

    # generic call: --args / --kwargs take JSON
    python odoo_rpc.py call --model sale.order --method search_read \
        --args '[[["state","=","draft"]]]' \
        --kwargs '{"fields":["name","amount_total"],"limit":5}'

    # convenience: search_read with a domain and optional fields
    python odoo_rpc.py search --model res.partner --domain '[["name","ilike","Acme"]]' \
        --fields name,email --limit 5

    # list a model's fields
    python odoo_rpc.py fields --model sale.order --attrs string,type,required
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error


def _env() -> tuple[str, str, str, str]:
    url = os.environ.get("ODOO_URL", "").rstrip("/")
    db = os.environ.get("ODOO_DB", "")
    user = os.environ.get("ODOO_USER", "")
    pwd = os.environ.get("ODOO_PASSWORD", "")
    missing = [k for k, v in {
        "ODOO_URL": url, "ODOO_DB": db,
        "ODOO_USER": user, "ODOO_PASSWORD": pwd,
    }.items() if not v]
    if missing:
        sys.exit(f"error: missing env var(s): {', '.join(missing)}")
    return url, db, user, pwd


def _rpc(url: str, params: dict):
    payload = json.dumps({
        "jsonrpc": "2.0", "method": "call", "params": params, "id": 1,
    }).encode()
    req = urllib.request.Request(
        f"{url}/jsonrpc", data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        sys.exit(f"error: cannot reach {url}: {exc}")
    if "error" in body:
        err = body["error"]
        msg = err.get("data", {}).get("message") or err.get("message")
        sys.exit(f"odoo error: {msg}")
    return body.get("result")


def _login(url: str, db: str, user: str, pwd: str) -> int:
    uid = _rpc(url, {
        "service": "common", "method": "login",
        "args": [db, user, pwd],
    })
    if not uid:
        sys.exit("error: authentication failed (check ODOO_DB / ODOO_USER / key)")
    return uid


def _json_arg(raw: str, default):
    return json.loads(raw) if raw is not None else default


def cmd_call(args) -> None:
    url, db, user, pwd = _env()
    uid = _login(url, db, user, pwd)
    result = _rpc(url, {
        "service": "object", "method": "execute_kw",
        "args": [db, uid, pwd, args.model, args.method,
                 _json_arg(args.args, []), _json_arg(args.kwargs, {})],
    })
    print(json.dumps(result, indent=2, default=str))


def cmd_search(args) -> None:
    url, db, user, pwd = _env()
    uid = _login(url, db, user, pwd)
    fields = [f.strip() for f in args.fields.split(",")] if args.fields else []
    result = _rpc(url, {
        "service": "object", "method": "execute_kw",
        "args": [db, uid, pwd, args.model, "search_read",
                 [_json_arg(args.domain, [])],
                 {"fields": fields, "limit": args.limit}],
    })
    print(json.dumps(result, indent=2, default=str))


def cmd_fields(args) -> None:
    url, db, user, pwd = _env()
    uid = _login(url, db, user, pwd)
    attrs = [a.strip() for a in args.attrs.split(",")]
    all_fields = _rpc(url, {
        "service": "object", "method": "execute_kw",
        "args": [db, uid, pwd, args.model, "fields_get", [], ["string", "type", "required", "relation", "selection"]],
    })
    out = {k: {a: v.get(a) for a in attrs} for k, v in sorted(all_fields.items())}
    print(json.dumps(out, indent=2, default=str))


def main() -> None:
    p = argparse.ArgumentParser(description="Odoo JSON-RPC client")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("call", help="call any model method (execute_kw)")
    c.add_argument("--model", required=True)
    c.add_argument("--method", required=True)
    c.add_argument("--args", help="JSON list of positional args, e.g. '[[123]]'")
    c.add_argument("--kwargs", help="JSON object of keyword args")
    c.set_defaults(func=cmd_call)

    s = sub.add_parser("search", help="search_read convenience")
    s.add_argument("--model", required=True)
    s.add_argument("--domain", help="JSON domain, e.g. '[[\"state\",\"=\",\"draft\"]]'")
    s.add_argument("--fields", help="comma-separated field names")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_search)

    f = sub.add_parser("fields", help="list model fields with selected attributes")
    f.add_argument("--model", required=True)
    f.add_argument("--attrs", default="string,type,required,relation")
    f.set_defaults(func=cmd_fields)

    args = p.parse_args()
    try:
        args.func(args)
    except json.JSONDecodeError as exc:
        sys.exit(f"error: invalid JSON argument: {exc}")


if __name__ == "__main__":
    main()
