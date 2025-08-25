# Flask API for NASA CMR dataset discovery
import os
import re
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)
CORS(app)

CMR_BASE = "https://cmr.earthdata.nasa.gov/search/collections.json"
NAMED_BBOX = {
    "india": [68, 6, 97, 36],
    "global": [-180, -90, 180, 90],
    "california": [-125, 32, -113, 43],
    "europe": [-11, 34, 31, 72],
    "indonesia": [95, -11, 141, 6],
}
EVENT_KEYWORDS = [
    "flood","volcano","wildfire","fire","cyclone","hurricane",
    "storm","rainfall","aerosol","ash","landslide","drought"
]

def parse_query(q):
    ql = q.lower()
    keyword = next((w for w in EVENT_KEYWORDS if w in ql), q)
    year = re.search(r"\b(19\d{2}|20\d{2})\b", ql)
    year = year.group(1) if year else None
    region = next((name for name in NAMED_BBOX if name in ql), None)
    return keyword, year, region

def build_temporal(year):
    if not year:
        return None
    return f"{year}-01-01T00:00:00Z,{year}-12-31T23:59:59Z"

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/api/search")
def search():
    q = request.args.get("q","").strip()
    if not q:
        return jsonify({"error":"missing q"}),400
    keyword, year, region = parse_query(q)
    params = {"keyword": keyword, "page_size": 10}
    if year:
        params["temporal"] = build_temporal(year)
    if region:
        params["bounding_box"] = ",".join(map(str, NAMED_BBOX[region]))
    r=requests.get(CMR_BASE,params=params,timeout=20)
    data=r.json()
    entries=data.get("feed",{}).get("entry",[])
    results=[]
    for e in entries:
        link = None
        for L in e.get("links", []):
            if "href" in L:
                link = L["href"]
                break
        results.append({
            "id": e.get("id"),
            "title": e.get("title"),
            "summary": e.get("summary"),
            "link": link
        })
    return jsonify({"query":{"raw":q,"keyword":keyword,"year":year,"region":region,"params_sent":params},
                    "results":results})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5001)),debug=True)
