import os
import re
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import json

load_dotenv()
app = Flask(__name__)
CORS(app)

CMR_BASE = "https://cmr.earthdata.nasa.gov/search/collections.json"
CMR_GRANULES = "https://cmr.earthdata.nasa.gov/search/granules.json"

NAMED_BBOX = {
    "india": [68, 6, 97, 36],
    "global": [-180, -90, 180, 90],
    "california": [-125, 32, -113, 43],
    "europe": [-11, 34, 31, 72],
    "indonesia": [95, -11, 141, 6],
}

EVENT_KEYWORDS = [
    "flood", "volcano", "wildfire", "fire", "cyclone", "hurricane",
    "storm", "rainfall", "aerosol", "ash", "landslide", "drought"
]

# --- Gemini Integration ---
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise RuntimeError("A Google Gemini API key is required. Please set the API_KEY environment variable.")
genai.configure(api_key=API_KEY)

# ---- Helper Functions ----
def extract_keywords_gemini(user_query: str) -> str:
    prompt = f"Extract the most relevant keywords for a NASA Earth science data search from the following user request: '{user_query}'. Return a short, comma-separated list of 2-5 keywords only."
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API error during keyword extraction: {e}")
        return user_query

def summarize_data_gemini(datasets: list) -> dict:
    if not datasets:
        return None
    dataset_text = "".join([f"Title: {ds.get('title')}\nSummary: {ds.get('summary')}\n\n" for ds in datasets])
    prompt = f"""
    Summarize these NASA datasets:
    {dataset_text}

    Respond in JSON with:
    {{
      "layman_summary_points": ["point1", "point2"],
      "satellite_data_points": ["point1", "point2"]
    }}
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(response_mime_type="application/json"))
        cleaned = re.search(r'\{.*\}', response.text.strip(), re.DOTALL)
        return json.loads(cleaned.group(0)) if cleaned else {
            'layman_summary_points': ["Summary unavailable"],
            'satellite_data_points': []
        }
    except Exception as e:
        print(f"Gemini summarization error: {e}")
        return {
            'layman_summary_points': ["Summary unavailable"],
            'satellite_data_points': []
        }

def parse_bbox_string(bbox_str):
    """
    Parse a bounding box string into [min_lat, min_lon, max_lat, max_lon].
    Supports both space-separated and comma-separated formats.
    """
    if not bbox_str:
        return None
    try:
        parts = re.split(r'[,\s]+', bbox_str.strip())
        coords = [float(x) for x in parts if x.strip()]
        if len(coords) == 4:
            return coords
    except Exception as e:
        print(f"Error parsing bbox string '{bbox_str}': {e}")
    return None

def fetch_granule_location(collection_id):
    """Fetch more accurate lat/lon from granules of the dataset."""
    try:
        params = {'collection_concept_id': collection_id, 'page_size': 5}
        resp = requests.get(CMR_GRANULES, params=params, timeout=15)
        if not resp.ok:
            return None

        granules = resp.json().get('feed', {}).get('entry', [])
        if not granules:
            return None

        granule = granules[0]

        # --- Handle boxes ---
        if 'boxes' in granule and granule['boxes']:
            box = granule['boxes'][0]
            if isinstance(box, list):
                box = box[0]
            if isinstance(box, str):
                coords = list(map(float, box.split(",")))
                return round((coords[0] + coords[2]) / 2, 6), round((coords[1] + coords[3]) / 2, 6)

        # --- Handle polygons ---
        elif 'polygons' in granule and granule['polygons']:
            poly = granule['polygons'][0]
            if isinstance(poly, list):
                poly = poly[0]
            if isinstance(poly, str):
                pts = poly.strip().split(' ')[0].split(',')
                return float(pts[0]), float(pts[1])

        return None

    except Exception as e:
        print(f"Granule location fetch failed for {collection_id}: {e}")
        return None


def search_nasa_cmr(keywords: str):
    params = {'keyword': keywords, 'page_size': '20'}
    try:
        resp = requests.get(CMR_BASE, params=params, timeout=20)
        resp.raise_for_status()
        entries = resp.json().get('feed', {}).get('entry', [])
        datasets = []

        for idx, ds in enumerate(entries):
            time_start = ds.get('time_start', 'N/A')
            try:
                if time_start != 'N/A':
                    from datetime import datetime
                    time_start = datetime.strptime(time_start, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
            except:
                pass

            lat, lon = None, None

            # --- Handle collection-level boxes ---
            if ds.get("boxes"):
                try:
                    box = ds["boxes"][0]
                    if isinstance(box, list):
                        box = box[0]
                    if isinstance(box, str):
                        coords = parse_bbox_string(box)
                        if coords:
                            lat = round((coords[0] + coords[2]) / 2, 6)
                            lon = round((coords[1] + coords[3]) / 2, 6)
                except Exception as e:
                    print(f"Error parsing collection bounding box for {ds.get('id')}: {e}")

            # --- Use granule-level location for more precision ---
            if ds.get('id'):
                loc = fetch_granule_location(ds['id'])
                if loc:
                    lat, lon = loc

            # --- Fallback if no coords found ---
            if lat is None or lon is None:
                lat = (idx * 10) % 90
                lon = (idx * 20) % 180

            datasets.append({
                'id': ds.get('id', 'N/A'),
                'title': ds.get('title', 'No title available'),
                'summary': ds.get('summary', 'No summary available.'),
                'dataCenter': ds.get('data_center', 'Unknown'),
                'timeStart': time_start,
                'latitude': lat,
                'longitude': lon
            })
        return datasets

    except Exception as e:
        print(f"NASA CMR API request failed: {e}")
        raise Exception("Failed to fetch data from NASA.")


def parse_query(q):
    ql = q.lower()
    keyword = next((w for w in EVENT_KEYWORDS if w in ql), q)
    year = re.search(r"\b(19\d{2}|20\d{2})\b", ql)
    year = year.group(1) if year else None
    region = next((name for name in NAMED_BBOX if name in ql), None)
    return keyword, year, region

def build_temporal(year):
    return f"{year}-01-01T00:00:00Z,{year}-12-31T23:59:59Z" if year else None

# ---- Routes ----
@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/api/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "missing q"}), 400
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


# --- Gemini-powered Search Endpoint ---
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
        datasets = search_nasa_cmr(keywords)
        result = {
            'originalQuery': user_query,
            'extractedKeywords': keywords,
            'datasets': datasets,
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Gemini-powered Chat Assistant Endpoint ---
@app.route("/chat", methods=["POST"])
def chat_assistant():
    data = request.get_json()
    user_query = data.get('query', '').strip()
    if not user_query:
        return jsonify({'error': 'Query is required.'}), 400

    keywords = extract_keywords_gemini(user_query)
    datasets = search_nasa_cmr(keywords)

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
    except Exception:
        answer = "Sorry, I couldn't generate an answer due to an error."

    return jsonify({
        "answer": answer,
        "datasets": datasets
    })

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5001)),debug=True)
