"""Preflight: lay every design sheet over the others and list unfilled cells and
references that don't resolve. Exit code 1 if anything blocks the build.

  python3 tools/preflight.py            # dev build: MGS paths may still be unverified
  python3 tools/preflight.py --release  # release: every cell must be filled and verified
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELEASE = "--release" in sys.argv


def sheet(name):
    with open(os.path.join(ROOT, "design", name + ".json"), encoding="utf-8") as f:
        return json.load(f)


ks = json.load(open(os.path.join(ROOT, "tools", "ks_names.json"), encoding="utf-8"))
chars = {r["id"]: r for r in sheet("characters")["rows"]}
camos = {r["id"]: r for r in sheet("camos")["rows"]}
reactions = sheet("reactions")["rows"]
scenes = sheet("scenes")["rows"]
codec = {r["id"]: r for r in sheet("codec")["rows"]}
mgs = sheet("mgs_assets")
mgs_rows = {r["key"]: r for r in mgs["rows"]}
hooks = sheet("hooks")["rows"]

errors, pending = [], []
MOODS = ("neutral", "shock", "happy", "angry")
# Cells that are intentionally empty for a row kind (speakers with no KS sprite).
ALLOWED_NULL = {
    "player": {"ks_char_var", "sprite_tag", "neutral", "shock", "happy", "angry", "repeat_line", "signed_var"},
    "codec": {"ks_char_var", "sprite_tag", "neutral", "shock", "happy", "angry", "repeat_line", "signed_var"},
    "girl": {"signed_var"},
    "npc": {"signed_var"},
}
POSITIONS = set(ks["transforms"])


def err(where, msg):
    errors.append("%s: %s" % (where, msg))


def check_text(where, text):
    # Ren'Py interpolates [..] and {..}; a literal [ must be written [[.
    t = text.replace("[[", "")
    if "[" in t or "{" in t:
        err(where, "unescaped [ or { in text: %r" % text)
    if not text.strip():
        err(where, "empty text")


def resolve_expr(who, expr, where):
    if who in ("narr",):
        return
    c = chars.get(who)
    if c is None:
        err(where, "unknown speaker %r" % who)
        return
    if expr is None:
        return
    if c["sprite_tag"] is None:
        err(where, "%s has no sprite but line sets expression %r" % (who, expr))
        return
    e = c[expr] if expr in MOODS else expr
    img = "%s %s" % (c["sprite_tag"], e)
    if img not in ks["images"]:
        err(where, "KS image %r does not exist" % img)


# characters
for cid, c in chars.items():
    for k, v in c.items():
        if v is None and k not in ALLOWED_NULL.get(c["kind"], set()):
            err("characters.%s.%s" % (cid, k), "unfilled")
    if c["ks_char_var"] and c["ks_char_var"] not in ks["character_vars"]:
        err("characters.%s.ks_char_var" % cid, "KS has no Character %r" % c["ks_char_var"])
    if c["signed_var"] and c["signed_var"] not in ks["character_vars"]:
        err("characters.%s.signed_var" % cid, "KS has no Character %r" % c["signed_var"])
    for m in MOODS:
        if c["sprite_tag"] and c[m]:
            resolve_expr(cid, m, "characters.%s.%s" % (cid, m))
    if c["repeat_line"]:
        check_text("characters.%s.repeat_line" % cid, c["repeat_line"])

# camos
if sum(1 for c in camos.values() if c["default"]) != 1:
    err("camos", "exactly one camo must be default")
for cid, c in camos.items():
    for k, v in c.items():
        if v is None:
            err("camos.%s.%s" % (cid, k), "unfilled")
    if c["mgs_asset"] not in mgs_rows:
        err("camos.%s.mgs_asset" % cid, "no mgs_assets row %r" % c["mgs_asset"])

# reactions: every reacting character x every camo, exactly once
reactors = sorted(set(r["who"] for r in reactions))
seen = {}
for i, r in enumerate(reactions):
    where = "reactions[%d](%s,%s)" % (i, r["who"], r["camo"])
    if r["who"] != "none" and r["who"] not in chars:
        err(where, "unknown who")
    if r["camo"] not in camos:
        err(where, "unknown camo")
    if (r["who"], r["camo"]) in seen:
        err(where, "duplicate row")
    seen[(r["who"], r["camo"])] = True
    if not r["lines"]:
        err(where, "no lines")
    for j, (who, expr, text) in enumerate(r["lines"]):
        resolve_expr(who, expr, "%s.lines[%d]" % (where, j))
        check_text("%s.lines[%d]" % (where, j), text)
for who in reactors:
    for cm in camos:
        if (who, cm) not in seen:
            err("reactions", "missing reaction for %s x %s" % (who, cm))

# scenes
reactors_needed = set()
for s in scenes:
    where = "scenes.%s" % s["id"]
    for k in ("id", "title", "bg", "music", "present", "ops"):
        if s.get(k) is None:
            err("%s.%s" % (where, k), "unfilled")
    if "bg " + s["bg"] not in ks["images"]:
        err(where + ".bg", "KS has no 'bg %s'" % s["bg"])
    if s["music"] not in ks["music_aliases"]:
        err(where + ".music", "KS has no music alias %r" % s["music"])
    present = list(s["present"])
    reactors_needed.update(present[:1] or ["none"])
    for j, op in enumerate(s["ops"]):
        w = "%s.ops[%d]" % (where, j)
        kind = op[0]
        if kind == "say":
            resolve_expr(op[1], op[2], w)
            check_text(w, op[3])
        elif kind in ("n", "hint"):
            check_text(w, op[1])
        elif kind == "show":
            resolve_expr(op[1], op[2], w)
            if op[3] not in POSITIONS:
                err(w, "KS has no transform %r" % op[3])
        elif kind == "hide":
            if op[1] not in chars:
                err(w, "unknown character %r" % op[1])
        elif kind == "present":
            for p in op[1]:
                if p not in chars:
                    err(w, "unknown character %r" % p)
            reactors_needed.update(op[1][:1])
        elif kind == "codec":
            if op[1] not in codec:
                err(w, "no codec call %r" % op[1])
        elif kind == "sfx":
            if op[1] not in ks["sfx"]:
                err(w, "KS has no sfx %r" % op[1])
        elif kind == "pause":
            pass
        else:
            err(w, "unknown op %r" % kind)
for who in reactors_needed:
    if who not in reactors:
        err("reactions", "scene reactor %r has no reaction rows" % who)

# codec
for cid, c in codec.items():
    where = "codec.%s" % cid
    for k, v in c.items():
        if v is None:
            err("%s.%s" % (where, k), "unfilled")
    if c["contact"] not in chars or chars[c["contact"]]["kind"] != "codec":
        err(where + ".contact", "not a codec character")
    for k in ("ring_asset", "open_asset", "close_asset"):
        if c[k] not in mgs_rows:
            err("%s.%s" % (where, k), "no mgs_assets row %r" % c[k])
    for j, (who, text) in enumerate(c["lines"]):
        if who not in chars:
            err("%s.lines[%d]" % (where, j), "unknown speaker %r" % who)
        check_text("%s.lines[%d]" % (where, j), text)
for who in ("snake", "zero", "paramedic"):
    if "codec_portrait_" + who not in mgs_rows:
        err("mgs_assets", "missing codec_portrait_%s" % who)

# MGS Delta content: must be confirmed against a real install before release
for k, v in mgs["install"].items():
    if v is None or v is False:
        pending.append("mgs_assets.install.%s: not yet confirmed on a real MGS Delta install" % k)
for key, r in mgs_rows.items():
    if r["source_path"] is None:
        pending.append("mgs_assets.%s.source_path: unfilled (needs a real MGS Delta install)" % key)
    elif not r["verified"]:
        pending.append("mgs_assets.%s.verified: source_path not yet checked" % key)
for h in hooks:
    for k, v in h.items():
        if v is None:
            err("hooks.%s.%s" % (h["id"], k), "unfilled")
    if not h["verified_in_game"]:
        pending.append("hooks.%s.verified_in_game: not yet seen working in a running KS" % h["id"])

print("PREFLIGHT  errors=%d  pending=%d  (%s mode)" % (len(errors), len(pending), "release" if RELEASE else "dev"))
for e in errors:
    print("  ERROR   " + e)
for p in pending:
    print("  PENDING " + p)
blocked = errors or (RELEASE and pending)
sys.exit(1 if blocked else 0)
