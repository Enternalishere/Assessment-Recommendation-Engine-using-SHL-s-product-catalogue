export default async function handler(req, res) {
  try {
    const base = process.env.API_BASE;
    if (!base) return res.status(500).json({ error: "API_BASE not configured" });
    const r = await fetch(`${base}/health`, { method: "GET" });
    const j = await r.json();
    res.setHeader("Access-Control-Allow-Origin", "*");
    return res.status(200).json(j);
  } catch (e) {
    return res.status(500).json({ error: String(e) });
  }
}
