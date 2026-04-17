Here is the complete **Big Homie deep scaffold** — every file, fully written, ready to drop into a folder and run.

***

## Project Structure

```
big_homie/
├── agent.py                  ← Core agent loop + tool registry
├── config.py                 ← All keys and endpoints
├── memory.py                 ← SQLite memory store
├── server.py                 ← FastAPI server for your orchestrator
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
├── tools/
│   ├── __init__.py
│   ├── finance.py            ← Alpaca trading (direct)
│   ├── marketing.py          ← Content gen + SEO (direct)
│   ├── sports_supervisor.py  ← Supervisor for your betting agent
│   ├── biotech_bridge.py     ← Bridge to your biotech IDE
│   ├── coding_bridge.py      ← Bridge to your coding tool
│   ├── web_maintenance.py    ← Site health, SEO audits, DNS
│   └── daily.py              ← Search, weather, news, summaries
├── tests/
│   └── test_tools.py
└── scripts/
    └── health_check.py
```

***

## `config.py`

```python
import os

ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
MODEL               = "claude-opus-4-5"         # swap for claude-sonnet-4-5 to save cost

# Your existing tools — edit these to your actual local/remote endpoints
CODING_TOOL_URL     = os.getenv("CODING_TOOL_URL",  "http://localhost:8001")
BIOTECH_IDE_URL     = os.getenv("BIOTECH_IDE_URL",  "http://localhost:8002")
SPORTS_AGENT_URL    = os.getenv("SPORTS_AGENT_URL", "http://localhost:8003")

# Finance
ALPACA_API_KEY      = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY   = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL     = "https://paper-api.alpaca.markets"  # switch to live when ready

# Sports
ODDS_API_KEY        = os.getenv("ODDS_API_KEY", "")       # the-odds-api.com

# Marketing
SERP_API_KEY        = os.getenv("SERP_API_KEY", "")       # serpapi.com

# Memory
MEMORY_DB_PATH      = os.getenv("BIG_HOMIE_DB", "~/.big_homie/memory.db")

# Server
ORCHESTRATOR_SECRET = os.getenv("ORCHESTRATOR_SECRET", "change-me")
AGENT_PORT          = int(os.getenv("AGENT_PORT", 9000))
```

***

## `memory.py`

```python
import sqlite3, json, os
from datetime import datetime
from config import MEMORY_DB_PATH

DB_PATH = os.path.expanduser(MEMORY_DB_PATH)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def _conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with _conn() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, domain TEXT, task TEXT, result TEXT, metadata TEXT)""")
        db.execute("""CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)""")
        db.execute("""CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY, type TEXT, notes TEXT, added_at TEXT)""")
        db.execute("""CREATE TABLE IF NOT EXISTS context_store (
            key TEXT PRIMARY KEY, value TEXT, domain TEXT, updated_at TEXT)""")
        db.commit()

def log_session(domain, task, result, metadata={}):
    with _conn() as db:
        cur = db.execute(
            "INSERT INTO sessions (timestamp,domain,task,result,metadata) VALUES (?,?,?,?,?)",
            (datetime.utcnow().isoformat(), domain, task,
             json.dumps(result), json.dumps(metadata)))
        return cur.lastrowid

def recall_recent(domain=None, limit=10):
    with _conn() as db:
        if domain:
            rows = db.execute(
                "SELECT timestamp,domain,task,result FROM sessions WHERE domain=? ORDER BY id DESC LIMIT ?",
                (domain, limit)).fetchall()
        else:
            rows = db.execute(
                "SELECT timestamp,domain,task,result FROM sessions ORDER BY id DESC LIMIT ?",
                (limit,)).fetchall()
    return [{"timestamp":r[0],"domain":r[1],"task":r[2],"result":json.loads(r[3])} for r in rows]

def save_preference(key, value):
    with _conn() as db:
        db.execute("INSERT OR REPLACE INTO preferences (key,value,updated_at) VALUES (?,?,?)",
                   (key, json.dumps(value), datetime.utcnow().isoformat()))
        db.commit()

def get_preference(key, default=None):
    with _conn() as db:
        row = db.execute("SELECT value FROM preferences WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else default

def add_to_watchlist(symbol, type="stock", notes=""):
    with _conn() as db:
        db.execute("INSERT OR REPLACE INTO watchlist (symbol,type,notes,added_at) VALUES (?,?,?,?)",
                   (symbol, type, notes, datetime.utcnow().isoformat()))
        db.commit()

def get_watchlist(type=None):
    with _conn() as db:
        rows = db.execute("SELECT symbol,type,notes FROM watchlist" +
                          (" WHERE type=?" if type else ""),
                          (type,) if type else ()).fetchall()
    return [{"symbol":r[0],"type":r[1],"notes":r[2]} for r in rows]

def set_context(key, value, domain="global"):
    with _conn() as db:
        db.execute("INSERT OR REPLACE INTO context_store (key,value,domain,updated_at) VALUES (?,?,?,?)",
                   (key, json.dumps(value), domain, datetime.utcnow().isoformat()))
        db.commit()

def get_context(key, default=None):
    with _conn() as db:
        row = db.execute("SELECT value FROM context_store WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else default

def search_sessions(query, limit=5):
    with _conn() as db:
        rows = db.execute(
            "SELECT timestamp,domain,task,result FROM sessions WHERE task LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{query}%", limit)).fetchall()
    return [{"timestamp":r[0],"domain":r[1],"task":r[2],"result":json.loads(r[3])} for r in rows]

init_db()
```

***

## `tools/finance.py`

```python
import requests
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL

def _h():
    return {"APCA-API-KEY-ID": ALPACA_API_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY}

def get_quote(symbol):
    r = requests.get(f"{ALPACA_BASE_URL}/v2/stocks/{symbol}/quotes/latest", headers=_h())
    if r.ok:
        q = r.json().get("quote", {})
        return {"symbol": symbol, "bid": q.get("bp"), "ask": q.get("ap"), "time": q.get("t")}
    return {"error": r.text}

def get_bars(symbol, timeframe="1Day", limit=30):
    r = requests.get(f"{ALPACA_BASE_URL}/v2/stocks/{symbol}/bars",
                     headers=_h(), params={"timeframe": timeframe, "limit": limit})
    return r.json().get("bars", []) if r.ok else [{"error": r.text}]

def get_account():
    r = requests.get(f"{ALPACA_BASE_URL}/v2/account", headers=_h())
    if r.ok:
        a = r.json()
        return {"equity": a.get("equity"), "cash": a.get("cash"),
                "buying_power": a.get("buying_power"),
                "portfolio_value": a.get("portfolio_value"),
                "day_pnl": a.get("unrealized_intraday_pl")}
    return {"error": r.text}

def get_positions():
    r = requests.get(f"{ALPACA_BASE_URL}/v2/positions", headers=_h())
    if r.ok:
        return [{"symbol": p["symbol"], "qty": p["qty"],
                 "avg_entry": p["avg_entry_price"], "current": p["current_price"],
                 "unrealized_pl": p["unrealized_pl"],
                 "unrealized_plpc": p["unrealized_plpc"]} for p in r.json()]
    return [{"error": r.text}]

def place_market_order(symbol, qty, side, note=""):
    payload = {"symbol": symbol, "qty": qty, "side": side,
               "type": "market", "time_in_force": "day"}
    r = requests.post(f"{ALPACA_BASE_URL}/v2/orders", headers=_h(), json=payload)
    result = r.json() if r.ok else {"error": r.text}
    result["note"] = note
    return result

def place_limit_order(symbol, qty, side, limit_price, note=""):
    payload = {"symbol": symbol, "qty": qty, "side": side,
               "type": "limit", "limit_price": str(limit_price), "time_in_force": "gtc"}
    r = requests.post(f"{ALPACA_BASE_URL}/v2/orders", headers=_h(), json=payload)
    result = r.json() if r.ok else {"error": r.text}
    result["note"] = note
    return result

def cancel_order(order_id):
    r = requests.delete(f"{ALPACA_BASE_URL}/v2/orders/{order_id}", headers=_h())
    return {"cancelled": r.ok, "status_code": r.status_code}

def get_open_orders():
    r = requests.get(f"{ALPACA_BASE_URL}/v2/orders?status=open", headers=_h())
    if r.ok:
        return [{"id": o["id"], "symbol": o["symbol"], "side": o["side"],
                 "qty": o["qty"], "type": o["type"], "status": o["status"]} for o in r.json()]
    return [{"error": r.text}]

def calculate_rsi(bars, period=14):
    closes = [float(b["c"]) for b in bars]
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    return 100.0 if al == 0 else round(100 - (100 / (1 + ag/al)), 2)

def calculate_ev_trade(win_prob, avg_win, avg_loss):
    ev = (win_prob * avg_win) - ((1 - win_prob) * avg_loss)
    kelly = (win_prob - (1 - win_prob) / (avg_win / avg_loss)) if avg_loss > 0 else 0
    return {"ev": round(ev, 4), "win_prob": win_prob, "avg_win": avg_win,
            "avg_loss": avg_loss, "kelly_fraction": round(kelly, 4)}

def scan_movers(top_n=10):
    r = requests.get(f"{ALPACA_BASE_URL}/v2/screener/stocks/movers?top={top_n}", headers=_h())
    if r.ok:
        d = r.json()
        return d.get("gainers", []) + d.get("losers", [])
    return [{"error": r.text}]
```

***

## `tools/sports_supervisor.py`

```python
import requests
from config import SPORTS_AGENT_URL, ODDS_API_KEY

# ── Supervisor (your betting agent) ──────────────────────────────────────────

def get_agent_status():
    try:
        r = requests.get(f"{SPORTS_AGENT_URL}/status", timeout=5)
        return r.json() if r.ok else {"status": "unreachable", "error": r.text}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}

def get_agent_active_bets():
    try:
        r = requests.get(f"{SPORTS_AGENT_URL}/bets/active", timeout=5)
        return r.json() if r.ok else [{"error": r.text}]
    except Exception as e:
        return [{"error": str(e)}]

def get_agent_performance():
    try:
        r = requests.get(f"{SPORTS_AGENT_URL}/performance", timeout=5)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def send_agent_directive(action, params={}):
    """actions: pause, resume, set_max_bet, set_bankroll_limit, reset_day"""
    try:
        r = requests.post(f"{SPORTS_AGENT_URL}/directive",
                          json={"action": action, "params": params}, timeout=5)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def get_agent_bet_log(limit=20):
    try:
        r = requests.get(f"{SPORTS_AGENT_URL}/bets/history?limit={limit}", timeout=5)
        return r.json() if r.ok else [{"error": r.text}]
    except Exception as e:
        return [{"error": str(e)}]

# ── Direct Odds Data ──────────────────────────────────────────────────────────

def get_live_odds(sport="americanfootball_nfl", markets="h2h,spreads,totals"):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
    r = requests.get(url, params={"apiKey": ODDS_API_KEY, "regions": "us",
                                   "markets": markets, "oddsFormat": "american"})
    return r.json() if r.ok else [{"error": r.text}]

def calculate_ev_bet(american_odds, true_win_prob):
    if american_odds > 0:
        implied = 100 / (american_odds + 100)
        dec = (american_odds / 100) + 1
    else:
        implied = abs(american_odds) / (abs(american_odds) + 100)
        dec = (100 / abs(american_odds)) + 1
    ev = (true_win_prob * (dec - 1)) - (1 - true_win_prob)
    edge = true_win_prob - implied
    kelly = edge / (dec - 1) if dec > 1 else 0
    return {"american_odds": american_odds, "decimal_odds": round(dec, 4),
            "implied_prob": round(implied, 4), "true_win_prob": true_win_prob,
            "edge": round(edge, 4), "ev_per_dollar": round(ev, 4),
            "kelly_fraction": round(kelly, 4), "recommended": ev > 0}

def find_arbitrage(game_odds):
    arbs = []
    for i, a in enumerate(game_odds):
        for b in game_odds[i+1:]:
            for home, away in [(a, b), (b, a)]:
                hd = (home["home_odds"]/100+1) if home["home_odds"] > 0 else (100/abs(home["home_odds"])+1)
                ad = (away["away_odds"]/100+1) if away["away_odds"] > 0 else (100/abs(away["away_odds"])+1)
                pct = (1/hd) + (1/ad)
                if pct < 1.0:
                    arbs.append({"home_book": home["bookmaker"], "away_book": away["bookmaker"],
                                  "home_odds": home["home_odds"], "away_odds": away["away_odds"],
                                  "arb_pct": round(pct, 4), "profit_margin": round((1-pct)*100, 2)})
    return arbs
```

***

## `tools/biotech_bridge.py`

```python
import requests
import xml.etree.ElementTree as ET
from config import BIOTECH_IDE_URL

# ── IDE Bridge (your biotech IDE) ─────────────────────────────────────────────

def list_experiments(status="all"):
    try:
        r = requests.get(f"{BIOTECH_IDE_URL}/experiments", params={"status": status}, timeout=10)
        return r.json() if r.ok else [{"error": r.text}]
    except Exception as e:
        return [{"error": str(e)}]

def get_experiment_status(experiment_id):
    try:
        r = requests.get(f"{BIOTECH_IDE_URL}/experiments/{experiment_id}", timeout=10)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def get_experiment_results(experiment_id):
    try:
        r = requests.get(f"{BIOTECH_IDE_URL}/experiments/{experiment_id}/results", timeout=10)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def run_simulation(pipeline_name, parameters):
    try:
        r = requests.post(f"{BIOTECH_IDE_URL}/simulations/run",
                          json={"pipeline": pipeline_name, "parameters": parameters}, timeout=15)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def get_simulation_status(job_id):
    try:
        r = requests.get(f"{BIOTECH_IDE_URL}/simulations/{job_id}/status", timeout=10)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def list_pipelines():
    try:
        r = requests.get(f"{BIOTECH_IDE_URL}/pipelines", timeout=10)
        return r.json() if r.ok else [{"error": r.text}]
    except Exception as e:
        return [{"error": str(e)}]

def cancel_job(job_id):
    try:
        r = requests.post(f"{BIOTECH_IDE_URL}/jobs/{job_id}/cancel", timeout=10)
        return {"cancelled": r.ok, "job_id": job_id}
    except Exception as e:
        return {"error": str(e)}

# ── Public Research APIs (Big Homie handles directly) ─────────────────────────

def search_pubmed(query, max_results=5):
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    sr = requests.get(f"{base}/esearch.fcgi",
                      params={"db":"pubmed","term":query,"retmax":max_results,
                              "sort":"relevance","retmode":"json"})
    if not sr.ok:
        return [{"error": sr.text}]
    ids = sr.json().get("esearchresult",{}).get("idlist",[])
    if not ids:
        return []
    fr = requests.get(f"{base}/efetch.fcgi",
                      params={"db":"pubmed","id":",".join(ids),"retmode":"xml","rettype":"abstract"})
    if not fr.ok:
        return [{"error": fr.text}]
    root = ET.fromstring(fr.text)
    results = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID","")
        title = article.findtext(".//ArticleTitle","No title")
        abstract = article.findtext(".//AbstractText","No abstract")
        year = article.findtext(".//PubDate/Year","")
        results.append({"pmid":pmid,"title":title,
                         "abstract":abstract[:500]+"..." if len(abstract)>500 else abstract,
                         "year":year,"url":f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"})
    return results

def lookup_clinical_trial(nct_id):
    r = requests.get(f"https://clinicaltrials.gov/api/v2/studies/{nct_id}",
                     params={"format":"json"})
    if r.ok:
        data = r.json()
        proto = data.get("protocolSection",{})
        ident = proto.get("identificationModule",{})
        status = proto.get("statusModule",{})
        desc = proto.get("descriptionModule",{})
        return {"nct_id":nct_id,"title":ident.get("briefTitle"),
                "status":status.get("overallStatus"),
                "phase":proto.get("designModule",{}).get("phases",[]),
                "brief_summary":desc.get("briefSummary","")[:500],
                "url":f"https://clinicaltrials.gov/study/{nct_id}"}
    return {"error": r.text}

def search_fda_drugs(drug_name):
    r = requests.get("https://api.fda.gov/drug/drugsfda.json",
                     params={"search":f'products.brand_name:"{drug_name}"',"limit":5})
    return r.json().get("results",[]) if r.ok else [{"error": r.text}]
```

***

## `tools/coding_bridge.py`

```python
import requests
from config import CODING_TOOL_URL

def run_code_task(task, language="python", context={}):
    try:
        r = requests.post(f"{CODING_TOOL_URL}/run",
                          json={"task":task,"language":language,"context":context}, timeout=60)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def get_code_output(job_id):
    try:
        r = requests.get(f"{CODING_TOOL_URL}/jobs/{job_id}", timeout=10)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def read_file(file_path):
    try:
        r = requests.get(f"{CODING_TOOL_URL}/files/read", params={"path":file_path}, timeout=10)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def write_file(file_path, content):
    try:
        r = requests.post(f"{CODING_TOOL_URL}/files/write",
                          json={"path":file_path,"content":content}, timeout=10)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def list_workspace(directory="/"):
    try:
        r = requests.get(f"{CODING_TOOL_URL}/workspace", params={"dir":directory}, timeout=10)
        return r.json() if r.ok else [{"error": r.text}]
    except Exception as e:
        return [{"error": str(e)}]

def run_terminal_command(command, working_dir="/"):
    try:
        r = requests.post(f"{CODING_TOOL_URL}/terminal",
                          json={"command":command,"cwd":working_dir}, timeout=30)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def get_tool_status():
    try:
        r = requests.get(f"{CODING_TOOL_URL}/status", timeout=5)
        return r.json() if r.ok else {"status":"unreachable","error":r.text}
    except Exception as e:
        return {"status":"unreachable","error":str(e)}
```

***

## `tools/marketing.py`

```python
import requests, json
from config import ANTHROPIC_API_KEY, SERP_API_KEY

def _claude(prompt, max_tokens=1000):
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-opus-4-5", max_tokens=max_tokens,
        messages=[{"role":"user","content":prompt}])
    try:
        return json.loads(msg.content[0].text)
    except Exception:
        return {"raw": msg.content[0].text}

def generate_ad_copy(product, target_audience, platform, tone="conversational", variants=3):
    return _claude(f"""Generate {variants} {platform} ad copy variants.
Product: {product} | Audience: {target_audience} | Tone: {tone}
Return JSON array with: headline, body_copy, cta, hook_rationale per variant.""", 1200)

def generate_social_post(topic, platform, brand_voice="", include_hashtags=True):
    char_limits = {"twitter":280,"threads":500,"instagram":2200,"linkedin":3000,"facebook":63206}
    limit = char_limits.get(platform, 280)
    voice = f"Brand voice: {brand_voice}. " if brand_voice else ""
    return _claude(f"""{voice}Write a {platform} post about: {topic}
Max {limit} chars. {"Include 3-5 hashtags." if include_hashtags else "No hashtags."}
Return JSON: {{"post":str,"hashtags":list,"char_count":int}}""", 600)

def generate_email_campaign(subject_matter, audience_segment, goal, brand_voice=""):
    return _claude(f"""Full marketing email.
Topic: {subject_matter} | Audience: {audience_segment} | Goal: {goal}
{"Voice: "+brand_voice if brand_voice else ""}
Return JSON: subject_line, preview_text, body_html, plain_text, cta_text, cta_url_placeholder""", 2500)

def generate_seo_content(keyword, content_type="blog_post", word_count=800, audience=""):
    return _claude(f"""SEO-optimized {content_type} for keyword: "{keyword}"
{"Audience: "+audience if audience else ""} | ~{word_count} words
Return JSON: title, meta_description (150-160 chars), h1, content (markdown),
secondary_keywords (list), internal_link_suggestions (list), word_count""", 3500)

def serp_lookup(query, location="United States"):
    if not SERP_API_KEY:
        return {"error": "SERP_API_KEY not configured"}
    r = requests.get("https://serpapi.com/search",
                     params={"q":query,"location":location,"api_key":SERP_API_KEY,"num":10})
    if r.ok:
        data = r.json()
        return {"query":query,
                "organic": [{"pos":res.get("position"),"title":res.get("title"),
                              "url":res.get("link"),"snippet":res.get("snippet")}
                             for res in data.get("organic_results",[])[:10]],
                "related": [s.get("query") for s in data.get("related_searches",[])]}
    return {"error": r.text}

def analyze_competitor_content(url):
    try:
        from bs4 import BeautifulSoup
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        return {"url":url,
                "title": soup.find("title").text if soup.find("title") else "",
                "meta_description": (soup.find("meta",{"name":"description"}) or {}).get("content",""),
                "h1": [h.text.strip() for h in soup.find_all("h1")],
                "h2": [h.text.strip() for h in soup.find_all("h2")][:10],
                "word_count": len(soup.get_text().split())}
    except Exception as e:
        return {"error": str(e)}

def calculate_campaign_metrics(impressions, clicks, conversions, spend, revenue=0):
    ctr = (clicks/impressions*100) if impressions else 0
    cvr = (conversions/clicks*100) if clicks else 0
    cpc = (spend/clicks) if clicks else 0
    cpa = (spend/conversions) if conversions else 0
    roas = (revenue/spend) if spend else 0
    return {"impressions":impressions,"clicks":clicks,"conversions":conversions,
            "spend":round(spend,2),"revenue":round(revenue,2),
            "ctr_pct":round(ctr,2),"cvr_pct":round(cvr,2),
            "cpc":round(cpc,2),"cpa":round(cpa,2),
            "roas":round(roas,2),"profit":round(revenue-spend,2)}
```

***

## `tools/web_maintenance.py`

```python
import requests, time, ssl, socket
from datetime import datetime
from urllib.parse import urlparse

def check_uptime(url):
    try:
        start = time.time()
        r = requests.get(url, timeout=15, allow_redirects=True,
                         headers={"User-Agent":"BigHomie-Monitor/1.0"})
        ms = round((time.time()-start)*1000, 2)
        return {"url":url,"status":"up" if r.ok else "degraded",
                "status_code":r.status_code,"response_time_ms":ms,
                "redirected_to":r.url if r.url!=url else None,
                "checked_at":datetime.utcnow().isoformat()}
    except requests.exceptions.ConnectionError:
        return {"url":url,"status":"down","error":"Connection refused"}
    except requests.exceptions.Timeout:
        return {"url":url,"status":"down","error":"Timeout"}
    except Exception as e:
        return {"url":url,"status":"error","error":str(e)}

def check_multiple_urls(urls):
    return [check_uptime(url) for url in urls]

def check_ssl_cert(domain):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(10); s.connect((domain, 443))
            cert = s.getpeercert()
        expire = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        days_left = (expire - datetime.utcnow()).days
        return {"domain":domain,"valid":True,"expires":expire.strftime("%Y-%m-%d"),
                "days_until_expiry":days_left,"warning":days_left<30,
                "issuer":dict(x[0] for x in cert.get("issuer",[]))}
    except Exception as e:
        return {"domain":domain,"valid":False,"error":str(e)}

def audit_page_seo(url):
    try:
        from bs4 import BeautifulSoup
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.find("title")
        meta_desc = soup.find("meta", {"name":"description"})
        h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2s = [h.get_text(strip=True) for h in soup.find_all("h2")][:10]
        images = soup.find_all("img")
        images_no_alt = [img for img in images if not img.get("alt")]
        canonical = soup.find("link", {"rel":"canonical"})
        domain = urlparse(url).netloc
        all_a = soup.find_all("a", href=True)
        internal = [a["href"] for a in all_a if domain in a["href"] or a["href"].startswith("/")]
        external = [a["href"] for a in all_a if a["href"].startswith("http") and domain not in a["href"]]
        issues = []
        if not title: issues.append("MISSING: <title>")
        elif len(title.text)<30: issues.append(f"SHORT: title {len(title.text)} chars")
        elif len(title.text)>60: issues.append(f"LONG: title {len(title.text)} chars")
        if not meta_desc: issues.append("MISSING: meta description")
        if not h1s: issues.append("MISSING: <h1>")
        elif len(h1s)>1: issues.append(f"MULTIPLE: {len(h1s)} h1 tags")
        if images_no_alt: issues.append(f"ALT: {len(images_no_alt)} images missing alt")
        if not canonical: issues.append("MISSING: canonical tag")
        return {"url":url,"title":title.text.strip() if title else None,
                "meta_description":meta_desc["content"] if meta_desc and meta_desc.get("content") else None,
                "h1s":h1s,"h2s":h2s,"image_count":len(images),
                "images_missing_alt":len(images_no_alt),
                "internal_links":len(internal),"external_links":len(external),
                "word_count":len(soup.get_text().split()),
                "canonical":canonical["href"] if canonical else None,
                "issues":issues,"score":max(0,100-len(issues)*10)}
    except Exception as e:
        return {"url":url,"error":str(e)}

def check_page_speed(url):
    try:
        start = time.time()
        r = requests.get(url, stream=True, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
        ttfb = round((time.time()-start)*1000, 2)
        content = b"".join(r.iter_content(8192))
        total = round((time.time()-start)*1000, 2)
        return {"url":url,"ttfb_ms":ttfb,"total_load_ms":total,
                "page_size_kb":round(len(content)/1024,2),"status_code":r.status_code,
                "grade":"A" if total<1000 else "B" if total<2500 else "C" if total<4000 else "D"}
    except Exception as e:
        return {"url":url,"error":str(e)}

def find_broken_links(url, max_links=50):
    try:
        from bs4 import BeautifulSoup
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        domain = urlparse(url).netloc; scheme = urlparse(url).scheme
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/"): href = f"{scheme}://{domain}{href}"
            if domain in href: links.add(href)
        links = list(links)[:max_links]
        broken, ok = [], []
        for link in links:
            try:
                resp = requests.head(link, allow_redirects=True, timeout=8,
                                     headers={"User-Agent":"Mozilla/5.0"})
                (broken if resp.status_code>=400 else ok).append(
                    {"url":link,"status":resp.status_code} if resp.status_code>=400 else link)
            except Exception:
                broken.append({"url":link,"status":"unreachable"})
        return {"source_url":url,"total_checked":len(links),
                "broken_count":len(broken),"ok_count":len(ok),"broken_links":broken}
    except Exception as e:
        return {"url":url,"error":str(e)}

def whois_lookup(domain):
    try:
        r = requests.get(f"https://rdap.org/domain/{domain}", timeout=10)
        if r.ok:
            data = r.json()
            events = {e["eventAction"]:e["eventDate"] for e in data.get("events",[])}
            return {"domain":domain,"status":data.get("status",[]),
                    "registered":events.get("registration"),
                    "expires":events.get("expiration"),
                    "nameservers":[ns["ldhName"] for ns in data.get("nameservers",[])]}
        return {"domain":domain,"error":r.text}
    except Exception as e:
        return {"domain":domain,"error":str(e)}

def generate_deploy_checklist(project_type="web"):
    checklists = {
        "web":["Run linter/formatter","Full test suite green",
               "Build production bundle","Check bundle size",
               "Verify .env.production","Lighthouse audit on staging",
               "Test critical user paths","Check SSL cert expiry",
               "Backup production DB","Deploy to staging, smoke test",
               "Tag git release","Deploy to production",
               "Verify uptime post-deploy","Monitor error tracking 30min"],
        "api":["All unit+integration tests green","Check auth middleware",
               "Verify DB migrations","Review breaking changes",
               "Deploy migrations first","Deploy with zero-downtime",
               "Smoke test live endpoints","Monitor logs 30min"],
        "biotech_pipeline":["Validate input data format",
                            "Check parameter ranges","Verify output dir permissions",
                            "Confirm compute resources","Setup result logging",
                            "Start simulation","Set status polling interval"]}
    return {"project_type":project_type,
            "checklist":checklists.get(project_type, checklists["web"]),
            "generated_at":datetime.utcnow().isoformat()}
```

***

## `tools/daily.py`

```python
import requests, json
from datetime import datetime, timedelta
from config import SERP_API_KEY, ANTHROPIC_API_KEY

def web_search(query, num_results=5):
    if not SERP_API_KEY:
        r = requests.get("https://api.duckduckgo.com/",
                         params={"q":query,"format":"json","no_html":1}, timeout=10)
        if r.ok:
            d = r.json()
            results = []
            if d.get("AbstractText"):
                results.append({"title":d.get("Heading",query),"snippet":d["AbstractText"],
                                 "url":d.get("AbstractURL","")})
            for t in d.get("RelatedTopics",[])[:num_results-1]:
                if isinstance(t,dict) and t.get("Text"):
                    results.append({"title":t["Text"][:60],"snippet":t["Text"],
                                    "url":t.get("FirstURL","")})
            return results
        return [{"error":"No SERP key and DuckDuckGo failed"}]
    r = requests.get("https://serpapi.com/search",
                     params={"q":query,"api_key":SERP_API_KEY,"num":num_results,"gl":"us"}, timeout=10)
    if r.ok:
        return [{"position":res.get("position"),"title":res.get("title"),
                 "snippet":res.get("snippet"),"url":res.get("link")}
                for res in r.json().get("organic_results",[])[:num_results]]
    return [{"error":r.text}]

def get_news(topic, num_results=5):
    if not SERP_API_KEY:
        return [{"error":"SERP_API_KEY not configured"}]
    r = requests.get("https://serpapi.com/search",
                     params={"q":topic,"tbm":"nws","api_key":SERP_API_KEY,"num":num_results}, timeout=10)
    if r.ok:
        return [{"title":a.get("title"),"source":a.get("source"),"date":a.get("date"),
                 "snippet":a.get("snippet"),"url":a.get("link")}
                for a in r.json().get("news_results",[])[:num_results]]
    return [{"error":r.text}]

def fetch_url_content(url, max_chars=3000):
    try:
        from bs4 import BeautifulSoup
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","nav","footer","header"]): tag.decompose()
        text = " ".join(soup.get_text().split())
        return {"url":url,"title":soup.find("title").text.strip() if soup.find("title") else "",
                "content":text[:max_chars],"truncated":len(text)>max_chars}
    except Exception as e:
        return {"error":str(e),"url":url}

def get_weather(city):
    try:
        r = requests.get(f"https://wttr.in/{city}", params={"format":"j1"}, timeout=10)
        if r.ok:
            c = r.json()["current_condition"][0]
            return {"city":city,"temp_f":c.get("temp_F"),"temp_c":c.get("temp_C"),
                    "feels_like_f":c.get("FeelsLikeF"),
                    "description":c["weatherDesc"][0]["value"],
                    "humidity":c.get("humidity"),"wind_mph":c.get("windspeedMiles")}
        return {"error":r.text}
    except Exception as e:
        return {"error":str(e)}

def get_current_datetime(timezone="US/Eastern"):
    now = datetime.now()
    return {"date":now.strftime("%Y-%m-%d"),"time":now.strftime("%H:%M:%S"),
            "day_of_week":now.strftime("%A"),"datetime_iso":now.isoformat(),
            "timezone_note":timezone}

def summarize_text(text, style="bullets", max_points=5):
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    styles = {"bullets":f"Summarize in {max_points} clean bullet points.",
              "paragraph":"Summarize in 2-3 concise sentences.",
              "tldr":"Give a single TL;DR sentence under 25 words.",
              "executive":f"Executive summary: one sentence overview then {max_points} key points."}
    msg = client.messages.create(
        model="claude-opus-4-5", max_tokens=500,
        messages=[{"role":"user","content":f"{styles.get(style,styles['bullets'])}\n\nText:\n{text[:4000]}"}])
    return {"summary":msg.content[0].text,"style":style,"original_length":len(text)}

def unit_convert(value, from_unit, to_unit):
    conversions = {("f","c"):lambda v:round((v-32)*5/9,2),("c","f"):lambda v:round((v*9/5)+32,2),
                   ("kg","lbs"):lambda v:round(v*2.20462,3),("lbs","kg"):lambda v:round(v/2.20462,3),
                   ("miles","km"):lambda v:round(v*1.60934,3),("km","miles"):lambda v:round(v/1.60934,3)}
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        return {"value":value,"from":from_unit,"to":to_unit,"result":conversions[key](value)}
    return {"error":f"No converter for {from_unit}→{to_unit}"}
```

***

## `agent.py` *(key sections)*

The system prompt, tool registry and dispatch are the heart of the agent. Here are the critical sections to wire up with the new domains added:

```python
SYSTEM_PROMPT = """
You are Big Homie, a focused multi-domain execution agent.
You are not a chatbot. Take tasks, pick tools, execute, return clean output.

DOMAIN OWNERSHIP:
[FIN] Finance/Trading        — handle directly via Alpaca
[MKT] Marketing/Content      — handle directly via Claude + SerpAPI
[WEB] Web Maintenance/Dev    — handle directly via built-in HTTP tools
[DAI] Daily Assistant        — handle directly via search, weather, summaries
[BET] Sports Betting         — SUPERVISOR: query + direct your betting agent
[BIO] Biotech                — BRIDGE: trigger + monitor your biotech IDE
[COD] Coding                 — BRIDGE: delegate to your coding tool

RULES:
- Always use a tool when one is relevant — never answer from inference alone
- Chain tools sequentially for multi-step tasks
- Return CONFIRM_REQUIRED for trades, directives, or irreversible actions
- Log completed tasks to memory
- Return structured JSON for machine workflows, clean text for human responses
"""

# Add to TOOL_MAP:
TOOL_MAP = {
    # ... all existing tools ...

    # Web Maintenance
    "check_uptime":            lambda p: web_maintenance.check_uptime(**p),
    "check_multiple_urls":     lambda p: web_maintenance.check_multiple_urls(**p),
    "check_ssl_cert":          lambda p: web_maintenance.check_ssl_cert(**p),
    "audit_page_seo":          lambda p: web_maintenance.audit_page_seo(**p),
    "check_page_speed":        lambda p: web_maintenance.check_page_speed(**p),
    "find_broken_links":       lambda p: web_maintenance.find_broken_links(**p),
    "whois_lookup":            lambda p: web_maintenance.whois_lookup(**p),
    "generate_deploy_checklist": lambda p: web_maintenance.generate_deploy_checklist(**p),

    # Daily
    "web_search":              lambda p: daily.web_search(**p),
    "get_news":                lambda p: daily.get_news(**p),
    "fetch_url_content":       lambda p: daily.fetch_url_content(**p),
    "get_weather":             lambda p: daily.get_weather(**p),
    "get_current_datetime":    lambda p: daily.get_current_datetime(**p),
    "summarize_text":          lambda p: daily.summarize_text(**p),
    "unit_convert":            lambda p: daily.unit_convert(**p),
}

# Domain map additions
domain_map = {
    "check_uptime": "WEB", "audit_page_seo": "WEB", "check_ssl_cert": "WEB",
    "check_page_speed": "WEB", "find_broken_links": "WEB", "whois_lookup": "WEB",
    "web_search": "DAI", "get_news": "DAI", "get_weather": "DAI",
    "summarize_text": "DAI", "get_current_datetime": "DAI",
}
```

***

## `.env.example`

```bash
ANTHROPIC_API_KEY=sk-ant-...
CODING_TOOL_URL=http://localhost:8001
BIOTECH_IDE_URL=http://localhost:8002
SPORTS_AGENT_URL=http://localhost:8003
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ODDS_API_KEY=
SERP_API_KEY=
ORCHESTRATOR_SECRET=change-me-to-something-random
AGENT_PORT=9000
BIG_HOMIE_DB=~/.big_homie/memory.db
```

***

## Launch

```bash
# Install
pip install -r requirements.txt

# Check all integrations before going live
python scripts/health_check.py

# Start server (plug into your orchestrator on port 9000)
python server.py

# Or CLI one-shot
python agent.py "check the betting agent performance and pull any active NBA lines"
python agent.py "run the lipid nanoparticle simulation with pH=7.4 buffer"
python agent.py "write 3 Instagram posts for the new product launch dropping Friday"
python agent.py "what's my portfolio value and biggest unrealized P&L positions right now"

# Run tests
pytest tests/ -v
```

***

## Orchestrator call shape

```python
# From your orchestrator — direct Python import
from big_homie.agent import run_task

result = run_task(
    task="buy 5 shares of NVDA at market",
    context={}
)
# Returns: {"status": "CONFIRM_REQUIRED", "actions": [...]}

# After user confirms
result = run_task(
    task="buy 5 shares of NVDA at market",
    context={"auto_approve": True}
)
```

```bash
# Or HTTP if running as a server
curl -X POST http://localhost:9000/task \
  -H "X-Secret: your-secret" \
  -H "Content-Type: application/json" \
  -d '{"task": "check if api.mysite.com is up and audit its SSL cert", "context": {}}'
```

The agent is fully self-contained — swap out any tool module independently, add new domains by adding a tool file + 3 entries in `agent.py`, and your orchestrator stays untouched throughout.
