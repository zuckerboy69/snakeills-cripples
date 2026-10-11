"""Static checks for the generated + handwritten .rpy files, for when no Ren'Py
runtime is available: every python line/block compiles, every call/jump target
exists, every speaker used is defined by KS or the mod, and no unescaped [ in text."""
import ast, glob, json, os, re, sys, textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ks = json.load(open(os.path.join(ROOT, "tools", "ks_names.json"), encoding="utf-8"))
files = sorted(glob.glob(os.path.join(ROOT, "mod", "snake_eater", "*.rpy")))
errors = []
labels, calls, speakers = set(), [], set()
MOD_SPEAKERS = {"sk_snake", "sk_zero", "sk_para", "centered"}
SAY = re.compile(r'^(\s*)(?:([A-Za-z_]\w*)\s+)?"((?:[^"\\]|\\.)*)"\s*$')

for path in files:
    name = os.path.basename(path)
    lines = open(path, encoding="utf-8").read().split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        where = "%s:%d" % (name, i + 1)
        if "\t" in ln:
            errors.append(where + ": tab indentation")
        m = re.match(r"^(\s*)(init(?: -?\d+)? python|python early)\s*:", ln)
        if m:
            ind = len(m.group(1))
            block = []
            i += 1
            while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > ind):
                block.append(lines[i]); i += 1
            try:
                ast.parse(textwrap.dedent("\n".join(block)))
            except SyntaxError as e:
                errors.append("%s: python block: %s" % (where, e))
            for d in re.findall(r"^\s*(\w+)\s*=\s*Character\(", "\n".join(block), re.M):
                MOD_SPEAKERS.add(d)
            continue
        if s.startswith("$ "):
            try:
                ast.parse(s[2:])
            except SyntaxError as e:
                errors.append("%s: $ line: %s" % (where, e))
        lm = re.match(r"^label (\w+)", s)
        if lm:
            labels.add(lm.group(1))
        cm = re.match(r"^(call|jump) (\w+)\s*$", s)
        if cm and cm.group(2) not in ("screen", "expression"):
            calls.append((where, cm.group(2)))
        if s.startswith(("if ", "elif ")):
            try:
                ast.parse(s.split(" ", 1)[1].rstrip(":"))
            except SyntaxError as e:
                errors.append("%s: condition: %s" % (where, e))
        sm = SAY.match(ln)
        if sm and not s.startswith(("text ", "textbutton ", "key ", "add ", "label ", "use ")) and name != "sk_core.rpy" or (sm and name == "sk_core.rpy" and sm.group(2) in (None, "centered")):
            who, text = sm.group(2), sm.group(3)
            if who:
                speakers.add((where, who))
            t = text.replace("[[", "")
            if "[" in t:
                errors.append(where + ": unescaped [ in say text")
        i += 1

for where, target in calls:
    if target not in labels:
        errors.append("%s: call/jump target %r not defined" % (where, target))
known = set(ks["character_vars"]) | MOD_SPEAKERS
for where, who in speakers:
    if who not in known:
        errors.append("%s: speaker %r is not defined by KS or the mod" % (where, who))
# every reaction label the picker can build must exist
data = open(os.path.join(ROOT, "mod", "snake_eater", "sk_data.rpy"), encoding="utf-8").read()
ns = {}
exec(textwrap.dedent(data.split("init -2 python:\n", 1)[1]), ns)
for who in ns["SK_REACTORS"]:
    for camo in ns["SK_CAMO_ORDER"]:
        if "sk_react_%s_%s" % (who, camo) not in labels:
            errors.append("missing reaction label sk_react_%s_%s" % (who, camo))
for cid in ns["SK_CODEC"]:
    if "sk_codec_" + cid not in labels:
        errors.append("missing codec label sk_codec_" + cid)

print("LINT %d files, %d labels, %d errors" % (len(files), len(labels), len(errors)))
for e in errors:
    print("  " + e)
sys.exit(1 if errors else 0)
