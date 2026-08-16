/**
 * Jan Swasth Map — District Response Agent (Cloudflare Worker).
 *
 * Stateless, grounded-by-input LLM proxy. The static site POSTs verified facts about ONE district
 * (forecast tier/score/trend + the deterministic response plan) plus an optional free-form question;
 * this Worker asks an OpenAI-compatible LLM to reason over ONLY those facts and returns text.
 *
 * Provider-agnostic: set LLM_BASE_URL, LLM_API_KEY, LLM_MODEL as Worker secrets/vars (e.g. MeshAPI).
 * If the LLM errors or is unconfigured, returns {fallback:true} so the client shows its deterministic
 * plan — the demo never breaks.
 *
 * Deploy: paste into a new Worker in the Cloudflare dashboard, add the three vars, Save & Deploy.
 * Verify: curl -X POST <worker-url> -H 'content-type: application/json' -d @sample.json
 */

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "content-type",
};

const SYSTEM = [
  "You are a district public-health response assistant for Indian District Health Officers.",
  "You are given VERIFIED facts about one district as JSON. Ground every statement strictly in those facts.",
  "Never invent numbers, districts, diseases, or dates. If the facts don't cover something, say so plainly.",
  "Do not give individual medical advice. Write concise, operational, decision-first prose — no preamble.",
].join(" ");

function reply(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status, headers: { "content-type": "application/json", ...CORS },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    if (request.method !== "POST") return reply({ error: "POST only" }, 405);

    if (!env.LLM_BASE_URL || !env.LLM_API_KEY || !env.LLM_MODEL) {
      return reply({ fallback: true, reason: "agent not configured" });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return reply({ error: "bad json" }, 400);
    }
    const facts = body.context;
    const question = (body.question || "").toString().slice(0, 500);
    if (!facts || typeof facts !== "object") return reply({ error: "missing context" }, 400);

    const user = question
      ? `Verified facts:\n${JSON.stringify(facts)}\n\nQuestion from the district officer: ${question}`
      : `Verified facts:\n${JSON.stringify(facts)}\n\nWrite a 3-4 sentence operational response brief for the district health officer.`;

    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 20000);
    try {
      const r = await fetch(`${env.LLM_BASE_URL.replace(/\/$/, "")}/chat/completions`, {
        method: "POST",
        headers: { "content-type": "application/json", authorization: `Bearer ${env.LLM_API_KEY}` },
        signal: ctl.signal,
        body: JSON.stringify({
          model: env.LLM_MODEL,
          temperature: 0.3,
          max_tokens: 350,
          messages: [{ role: "system", content: SYSTEM }, { role: "user", content: user }],
        }),
      });
      if (!r.ok) return reply({ fallback: true, reason: `provider ${r.status}` });
      const data = await r.json();
      const text = data?.choices?.[0]?.message?.content?.trim();
      return text ? reply({ text }) : reply({ fallback: true, reason: "empty completion" });
    } catch (e) {
      return reply({ fallback: true, reason: String(e).slice(0, 120) });
    } finally {
      clearTimeout(timer);
    }
  },
};
