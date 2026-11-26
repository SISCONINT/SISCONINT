#!/usr/bin/env python3
"""Sincroniza los monitores de Better Stack Uptime con monitors.json.

Idempotente: busca cada monitor por su nombre (pronounceable_name); si existe lo
actualiza (PATCH) y si no, lo crea (POST). No borra monitores que no estén en el
archivo. Solo usa la biblioteca estándar, así que corre en cualquier Python 3.9+.

Variables de entorno:
  BETTERSTACK_API_TOKEN  Token de la API de Uptime (Settings > API tokens). Obligatorio.
  FRONTEND_URL           URL pública de Netlify, p. ej. https://sisconint.netlify.app
  BACKEND_URL            URL de Render (default: https://sisconint-backend.onrender.com)
  BETTERSTACK_TEAM_NAME  Solo si usas un token global en vez de uno de equipo.

Uso:
  python monitoring/betterstack/sync_monitors.py --dry-run
  python monitoring/betterstack/sync_monitors.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://uptime.betterstack.com/api/v2/monitors"
DEFAULT_BACKEND_URL = "https://sisconint-backend.onrender.com"
CONFIG = Path(__file__).with_name("monitors.json")
_VAR = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _expand(value, env):
    if isinstance(value, str):
        def repl(m):
            name = m.group(1)
            if not env.get(name):
                raise SystemExit(f"Falta la variable de entorno {name}")
            return env[name].rstrip("/")
        return _VAR.sub(repl, value)
    if isinstance(value, list):
        return [_expand(v, env) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v, env) for k, v in value.items()}
    return value


def load_monitors(path: Path, env: dict) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    defaults = raw.get("defaults", {})
    monitors = [_expand({**defaults, **m}, env) for m in raw["monitors"]]
    names = [m["pronounceable_name"] for m in monitors]
    if len(names) != len(set(names)):
        raise SystemExit("Hay nombres de monitor repetidos en monitors.json")
    team = env.get("BETTERSTACK_TEAM_NAME")
    if team:
        for m in monitors:
            m["team_name"] = team
    return monitors


def _request(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "sisconint-monitor-sync")
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise SystemExit(f"{method} {url} -> HTTP {exc.code}: {detail}") from None


def existing_monitors(token: str, team: str | None) -> dict[str, dict]:
    params = {"per_page": 250}
    if team:
        params["team_name"] = team
    url = f"{API}?{urllib.parse.urlencode(params)}"
    found: dict[str, dict] = {}
    while url:
        page = _request("GET", url, token)
        for item in page.get("data", []):
            name = item["attributes"].get("pronounceable_name")
            if name:
                found[name] = item
        url = (page.get("pagination") or {}).get("next")
    return found


def _diff(current: dict, wanted: dict) -> dict:
    return {k: v for k, v in wanted.items() if k != "team_name" and current.get(k) != v}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="Muestra los cambios sin aplicarlos")
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args(argv)

    env = dict(os.environ)
    env.setdefault("BACKEND_URL", DEFAULT_BACKEND_URL)
    monitors = load_monitors(args.config, env)

    token = env.get("BETTERSTACK_API_TOKEN", "")
    if not token:
        if args.dry_run:
            print("Sin BETTERSTACK_API_TOKEN: solo se valida monitors.json.\n")
            for m in monitors:
                print(f"  + {m['pronounceable_name']}: {m['url']}")
            return 0
        raise SystemExit("Falta BETTERSTACK_API_TOKEN")

    current = existing_monitors(token, env.get("BETTERSTACK_TEAM_NAME"))
    for wanted in monitors:
        name = wanted["pronounceable_name"]
        if name not in current:
            print(f"+ crear     {name} -> {wanted['url']}")
            if not args.dry_run:
                _request("POST", API, token, wanted)
            continue
        item = current[name]
        changes = _diff(item["attributes"], wanted)
        if not changes:
            print(f"= sin cambio {name}")
            continue
        print(f"~ actualizar {name}: {', '.join(sorted(changes))}")
        if not args.dry_run:
            _request("PATCH", f"{API}/{item['id']}", token, changes)

    extra = sorted(set(current) - {m["pronounceable_name"] for m in monitors})
    if extra:
        print("\nMonitores en Better Stack que no están en monitors.json (no se tocan):")
        for name in extra:
            print(f"  - {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
