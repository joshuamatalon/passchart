"""Static checks for Pass Chart. Run: python tools/check.py

Extracts the inline <script> from index.html and syntax-checks it with node,
then checks sw.js, then greps for a few mistakes that are easy to make in a
single-file app and invisible until runtime.
"""
import io, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "index.html")
SW = os.path.join(ROOT, "sw.js")

fails = []


def node_check(code, label):
    fd, path = tempfile.mkstemp(suffix=".js")
    os.close(fd)
    io.open(path, "w", encoding="utf-8").write(code)
    try:
        r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
        if r.returncode != 0:
            fails.append("%s: SYNTAX ERROR\n%s" % (label, r.stdout + r.stderr))
            return False
        print("  OK   %s parses (%d bytes)" % (label, len(code)))
        return True
    finally:
        os.unlink(path)


html = io.open(APP, encoding="utf-8").read()
print("index.html: %d bytes" % len(html))

scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
if len(scripts) != 1:
    fails.append("expected exactly 1 inline <script>, found %d" % len(scripts))
else:
    node_check(scripts[0], "index.html inline script")

node_check(io.open(SW, encoding="utf-8").read(), "sw.js")

# --- structural checks -------------------------------------------------
def want(cond, msg):
    if not cond:
        fails.append(msg)
    else:
        print("  OK   %s" % msg)


js = scripts[0] if len(scripts) == 1 else ""

want(js.count("function viewSession") == 1, "exactly one viewSession definition")
want(js.count("function boot") == 1, "exactly one boot definition")
want("window.PC" in js, "PC test surface is exposed")

# every function called from an onclick/handler must actually exist
defined = set(re.findall(r"function\s+([A-Za-z_$][\w$]*)", js))
defined |= set(re.findall(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(", js))
for name in ["setQuick", "refreshQuick", "tapGrade", "undoLast", "bump",
             "confirmDelete", "photoPanel", "runQueue", "openModal", "closeModal",
             "buildCSV", "download", "exportCSV", "matchPlayer", "imageToJpeg",
             "callReader", "sheetPrompt", "render", "commit", "flushNow", "paintBadge"]:
    want(name in defined, "%s() is defined" % name)

# the CSS the new session view depends on
for cls in ["chipstrip", "quick", "quickon", "ptap", "prow.active"]:
    want(cls in html, "css .%s present" % cls)

# icons referenced by the manifest must exist on disk
import json
man = json.load(io.open(os.path.join(ROOT, "manifest.webmanifest"), encoding="utf-8"))
for ic in man["icons"]:
    want(os.path.exists(os.path.join(ROOT, ic["src"])), "icon exists: " + ic["src"])
want(os.path.exists(os.path.join(ROOT, "icons", "apple-touch-icon.png")), "apple-touch-icon exists")

# things that would silently break offline
want("api.anthropic.com" in io.open(SW, encoding="utf-8").read()
     or "anthropic.com" in io.open(SW, encoding="utf-8").read(),
     "sw.js refuses to cache the vision API")
want("navigator.onLine" in js, "app checks navigator.onLine before calling out")

print()
if fails:
    print("FAILED (%d):" % len(fails))
    for f in fails:
        print(" - " + f)
    sys.exit(1)
print("ALL CHECKS PASSED")
