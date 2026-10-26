import re, json, time, threading
from collections import deque
from flask import Flask, request

# --- Try to load the real AI settings; fall back to MOCK mode if missing ---
try:
    from config import BASE_URL, API_KEY, MODEL
    from openai import OpenAI
    MOCK = API_KEY.startswith("your-") or "your-" in MODEL
    client = None if MOCK else OpenAI(base_url=BASE_URL, api_key=API_KEY)
except ImportError:
    MOCK = True
    client = None
print("MODE:", "MOCK (fake AI)" if MOCK else "REAL (Nemotron)")

SAFE_TEMP = (15, 30)
window = deque(maxlen=30)
advice = {"level": "ok", "short": "All normal", "explain": "", "until": 0}
last_call = 0
lock = threading.Lock()
app = Flask(__name__)

SYSTEM = (
    "You monitor a storage cabinet that must stay 15-30 C and below 70% humidity, "
    "using a DHT11 sensor. You get recent readings and what triggered the flag. "
    "Reply ONLY with JSON: "
    '{"severity":"warn" or "alert","short":"max 16 chars","explanation":"2 sentences: likely cause and what to check"}'
)

def detect(w):
    reasons = []
    t, h = w[-1]["t"], w[-1]["h"]
    if len(w) >= 10:
        dt = t - w[-10]["t"]
        dh = h - w[-10]["h"]
        if abs(dt) >= 2:  reasons.append(f"temp changed {dt:+.0f} C in ~20 s")
        if abs(dh) >= 10: reasons.append(f"humidity changed {dh:+.0f}% in ~20 s")
    if not (SAFE_TEMP[0] <= t <= SAFE_TEMP[1]): reasons.append(f"temp {t} C outside safe range")
    if h > 70: reasons.append(f"humidity {h}% too high")
    return reasons

def mock_reply(reasons):
    text = " ".join(reasons)
    if "humidity" in text:
        return {"severity": "warn", "short": "Humidity spike",
                "explanation": "[MOCK] Humidity jumped quickly, likely breath or a leak nearby. Check seals and for water."}
    return {"severity": "alert", "short": "Heat source near",
            "explanation": "[MOCK] Temperature changed fast, likely a heat source or failing fan. Check nearby devices."}

def ask_llm(reasons, w):
    global advice
    try:
        if MOCK:
            j = mock_reply(reasons)
        else:
            data = [(r["t"], r["h"]) for r in list(w)[-15:]]
            prompt = f"Triggers: {reasons}\nLast readings (temp C, hum %), oldest first: {data}"
            r = client.chat.completions.create(
                model=MODEL, temperature=0.2,
                messages=[{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": prompt}])
            text = r.choices[0].message.content
            j = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        with lock:
            advice = {"level": j.get("severity", "warn"),
                      "short": j.get("short", "Check cabinet")[:16],
                      "explain": j.get("explanation", ""),
                      "until": time.time() + 30}
        print("AI:", advice)
    except Exception as e:
        print("AI error:", e)

@app.route("/reading", methods=["POST"])
def reading():
    global last_call
    d = request.get_json()
    window.append({"t": d["t"], "h": d["h"]})
    reasons = detect(window)
    if reasons and time.time() - last_call > 20:
        last_call = time.time()
        threading.Thread(target=ask_llm, args=(reasons, list(window)), daemon=True).start()
    with lock:
        if time.time() > advice["until"]:
            advice.update(level="ok", short="All normal")
        return f'{advice["level"]}|{advice["short"]}'

app.run(host="0.0.0.0", port=8000)

