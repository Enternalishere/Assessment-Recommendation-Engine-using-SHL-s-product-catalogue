export default async function handler(req, res) {
  try {
    if (req.method !== "POST") {
      res.setHeader("Allow", "POST");
      return res.status(405).json({ error: "Method Not Allowed" });
    }
    const base = process.env.API_BASE;
    if (!base) return res.status(500).json({ error: "API_BASE not configured" });
    const r = await fetch(`${base}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body || {}),
    });
    const j = await r.json();
    res.setHeader("Access-Control-Allow-Origin", "*");
    return res.status(200).json(j);
  } catch (e) {
    return res.status(500).json({ error: String(e) });
  }
}
