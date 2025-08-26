import os
import re
import requests
import google.generativeai as genai
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

# --- Gemini Integration ---
import google.generativeai as genai

API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise RuntimeError("A Google Gemini API key is required. Please set the API_KEY environment variable.")
genai.configure(api_key=API_KEY)

def extract_keywords_gemini(user_query: str) -> str:
    prompt = f"Extract the most relevant keywords for a NASA Earth science data search from the following user request: '{user_query}'. Return a short, relevant, comma-separated list of 2-5 keywords. Do not add any introductory text, titles, or explanations. Just return the keywords."
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        keywords = response.text.strip().replace('keywords:', '').strip()
        return keywords
    except Exception as e:
        print(f"Gemini API error during keyword extraction: {e}")
        return user_query

def search_nasa_cmr(keywords: str):
    params = {
        'keyword': keywords,
        'page_size': '20',
    }
    try:
        resp = requests.get(CMR_BASE, params=params, timeout=20)
        if not resp.ok:
            print(f"NASA CMR API Error Response: {resp.text}")
            raise Exception(f"NASA CMR API responded with status: {resp.status_code}")
        data = resp.json()
        entries = data.get('feed', {}).get('entry', [])
        datasets = []
        for ds in entries:
            time_start = ds.get('time_start', None)
            if time_start:
                try:
                    from datetime import datetime
                    time_start = datetime.strptime(time_start, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
                except Exception:
                    pass
            else:
                time_start = 'N/A'
            datasets.append({
                'id': ds.get('id', 'N/A'),
                'title': ds.get('title', 'No title available'),
                'summary': ds.get('summary', 'No summary available.'),
                'dataCenter': ds.get('data_center', 'Unknown'),
                'timeStart': time_start
            })
        return datasets
    except Exception as e:
        print(f"NASA CMR API request failed: {e}")
        raise Exception("Failed to fetch data from NASA. The service may be temporarily unavailable.")

# --- Gemini Search Endpoint ---
@app.route("/search", methods=["GET", "POST"])
def gemini_search():
    if request.method == "POST":
        data = request.get_json()
        user_query = data.get('query', '').strip() if data else ''
    else:
        user_query = request.args.get('query', '').strip()
    if not user_query:
        return jsonify({'error': 'Query is required.'}), 400
    try:
        keywords = extract_keywords_gemini(user_query)
        if not keywords:
            datasets = search_nasa_cmr(user_query)
            result = {
                'originalQuery': user_query,
                'extractedKeywords': user_query,
                'datasets': datasets,
            }
        else:
            datasets = search_nasa_cmr(keywords)
            result = {
                'originalQuery': user_query,
                'extractedKeywords': keywords,
                'datasets': datasets,
            }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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


# --- AI Chat Assistant Endpoint ---
@app.route("/chat", methods=["POST"])
def chat_assistant():
    data = request.get_json()
    user_query = data.get('query', '').strip()
    if not user_query:
        return jsonify({'error': 'Query is required.'}), 400

    # Step 1: Extract keywords/intents
    keywords = extract_keywords_gemini(user_query)
    datasets = search_nasa_cmr(keywords)

    # Step 2: Summarize answer using Gemini
    context = "\n".join([f"{ds['title']}: {ds['summary']}" for ds in datasets[:5]])
    prompt = (
        f"User asked: '{user_query}'.\n"
        f"Here are some relevant NASA datasets:\n{context}\n"
        "Based on these, answer the user's question in a helpful, concise way. "
        "If no relevant datasets, say so."
    )
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        answer = response.text.strip()
    except Exception as e:
        answer = "Sorry, I couldn't generate an answer due to an error."

    return jsonify({
        "answer": answer,
        "datasets": datasets
    })

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5001)),debug=True)
