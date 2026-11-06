import re, json

js = open("_design_ref/app.js", "r", encoding="utf-8", errors="replace").read()

# backtick strings
bt = re.findall(r"`([^`\\]{2,400})`", js)
ru = [s for s in bt if re.search(r"[\u0400-\u04FF]", s)]
out = open("_design_ref/strings.txt", "w", encoding="utf-8")
out.write(f"backtick total {len(bt)}\nRU {len(ru)}\n\n")
for s in ru:
    out.write("RU: " + s.replace("\n", " | ") + "\n")

# also quoted with backticks around russian mixed
# extract around PD-
for pid in ["PD-24081", "PD-24082", "PD-24083", "PD-24084"]:
    i = js.find(pid)
    out.write(f"\n\n==== {pid} idx={i} ====\n")
    out.write(js[max(0, i-400): i+800])

# find currentUser / mock data
for key in ["currentUser", "mockRequests", "helpRequests", "bankName", "Сбер", "Тинькофф", "phone", "feed", "profile", "stats", "create"]:
    i = js.find(key)
    out.write(f"\n\n==== KEY {key} idx={i} ====\n")
    if i >= 0:
        out.write(js[max(0, i-200): i+500])

out.close()
print("wrote strings.txt")
