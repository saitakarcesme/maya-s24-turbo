"""Small correctness probe: questions with checkable answers, thinking on, temp 0.6. Prints score."""
import json, re, sys, time, urllib.request
URL = "http://127.0.0.1:8091/v1/chat/completions"
Q = [
 ("What is 17 * 23? Answer with the number only.", r"\b391\b"),
 ("What is 1234 + 5678? Answer with the number only.", r"\b6912\b"),
 ("A train goes 60 km/h for 2.5 hours. How many km? Number only.", r"\b150\b"),
 ("If x + 7 = 19, what is x? Number only.", r"\b12\b"),
 ("What is the capital of Australia? One word.", r"canberra"),
 ("Which planet is known as the Red Planet? One word.", r"mars"),
 ("Who wrote Pride and Prejudice? Name only.", r"austen"),
 ("What is the chemical symbol for gold? Symbol only.", r"\bau\b"),
 ("How many sides does a hexagon have? Number only.", r"\b6\b|six"),
 ("I have 3 boxes with 4 apples each, I eat 5 apples. How many are left? Number only.", r"\b7\b"),
 ("What does this Python print: print(sum(range(5)))? Output only.", r"\b10\b"),
 ("What is the square root of 144? Number only.", r"\b12\b"),
]
ok = 0; t0 = time.time(); toks = 0
for q, pat in Q:
    body = {"model": "glm-5.3-flash", "max_tokens": 1500, "temperature": 0.6,
            "messages": [{"role": "user", "content": q}]}
    r = json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(),
        {"Content-Type": "application/json"}), timeout=900))
    a = r["choices"][0]["message"].get("content") or ""
    toks += r.get("usage", {}).get("completion_tokens", 0)
    good = bool(re.search(pat, a, re.I)); ok += good
    print(("PASS" if good else "FAIL"), repr(a.strip()[:80]), flush=True)
print(f"[{sys.argv[1] if len(sys.argv)>1 else run}] SCORE {ok}/{len(Q)}  ({toks} tokens, {time.time()-t0:.0f}s)")
