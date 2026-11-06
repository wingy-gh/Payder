import re

js = open("_design_ref/app.js", "r", encoding="utf-8", errors="replace").read()
print("js len", len(js))

# Cyrillic strings
ru = re.findall(r'"([^"\\]*[\u0400-\u04FF][^"\\]*)"', js)
print("RU quoted", len(ru))
for s in ru:
    print("RU:", s[:200])

print("\n--- TEMPLATE-ISH ---\n")
# look for likely UI identifiers
for pat in ["screen", "profile", "stats", "create", "feed", "requisites", "Paynder", "Payder", "navItems", "requests"]:
    idxs = [m.start() for m in re.finditer(pat, js, re.I)]
    print(pat, "count", len(idxs))

print("\n--- SAMPLE AROUND requests ---\n")
for m in re.finditer(r"requests", js):
    i = m.start()
    print(js[max(0, i-80): i+180].replace("\n", " ")[:260])
    print("---")
    break

# extract object-like JSON with PD-
ids = re.findall(r"PD-\d+", js)
print("IDs", ids[:20], "n=", len(ids))
