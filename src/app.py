import os
import json
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, Body
from fastapi.responses import HTMLResponse
import requests
from bs4 import BeautifulSoup
from .shl.indexer import load_catalog
from .shl.recommender import Recommender


app = FastAPI()
catalog_items = 0
rec = None


def jd_from_url(u: str) -> str:
    hdrs = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(u, headers=hdrs, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        for s in soup(["script", "style", "noscript"]):
            s.decompose()
        txt = " ".join(soup.get_text(separator=" ").split())
        return txt[:5000]
    except Exception:
        return ""


@app.on_event("startup")
def on_startup():
    global catalog_items, rec
    catalog_items = len(load_catalog())
    rec = Recommender()


@app.get("/health")
def health():
    return {"status": "ok", "catalog_items": catalog_items, "embedding_model": "all-MiniLM-L6-v2"}

@app.get("/", response_class=HTMLResponse)
def index():
    html = """
    <!doctype html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>SHL Recommendations</title>
    </head>
    <body>
    <h1>SHL Recommendations</h1>
    <div>
      <label>Input Type</label>
      <select id="input_type">
        <option value="text">text</option>
        <option value="jd_text">jd_text</option>
        <option value="jd_url">jd_url</option>
      </select>
    </div>
    <div>
      <textarea id="query" rows="8" cols="80" placeholder="Enter query or JD text or URL"></textarea>
    </div>
    <button onclick="send()">Recommend</button>
    <table border="1" id="tbl"><thead><tr><th>Name</th><th>URL</th><th>Type</th></tr></thead><tbody></tbody></table>
    <script>
    async function send(){
      const input_type = document.getElementById('input_type').value;
      const query = document.getElementById('query').value;
      const r = await fetch('/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input_type,query,top_k:10})});
      const j = await r.json();
      const tb = document.querySelector('#tbl tbody');
      tb.innerHTML = '';
      for(const it of j.items){
        const tr = document.createElement('tr');
        const td1 = document.createElement('td'); td1.textContent = it.name;
        const td2 = document.createElement('td'); const a = document.createElement('a'); a.href=it.url; a.textContent=it.url; a.target='_blank'; td2.appendChild(a);
        const td3 = document.createElement('td'); td3.textContent = it.type || '';
        tr.appendChild(td1); tr.appendChild(td2); tr.appendChild(td3);
        tb.appendChild(tr);
      }
    }
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/recommend")
def recommend(payload: Dict[str, Any] = Body(...)):
    input_type = payload.get("input_type", "text")
    query = payload.get("query", "") or ""
    top_k = int(payload.get("top_k", 10))
    if input_type == "jd_url":
        q = jd_from_url(query)
        if q:
            query = q
    if input_type == "jd_text":
        query = query
    items = rec.recommend(query=query, k=max(5, min(10, top_k)))
    out = [{"name": it["name"], "url": it["url"], "type": it.get("type", "")} for it in items]
    return {"items": out}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.app:app", host="0.0.0.0", port=port, reload=False)
