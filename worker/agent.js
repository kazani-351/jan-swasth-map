/**
 * Jan Swasth Map — District Response Agent (Cloudflare Worker).
 *
 * Stateless, grounded-by-input LLM proxy. The static site POSTs verified facts about ONE district
 * (forecast tier/score/trend + the deterministic response plan) plus an optional free-form question;
 * this Worker asks an OpenAI-compatible LLM to reason over ONLY those facts and returns text.
 *
 * Provider-agnostic: set as Worker secrets/vars —
 *   LLM_BASE_URL   e.g. https://api.meshapi.ai/v1   (OpenAI-compatible base, before /chat/completions)
 *   LLM_API_KEY    your provider key (Secret)
 *   LLM_MODEL      e.g. openai/gpt-4o-mini
 *   ALLOWED_ORIGIN (optional) your Pages URL, e.g. https://jan-swasth-map.pages.dev — set once the
 *                  site is live to lock this Worker to your own frontend. Unset = open to all.
 *
 * Request size is capped (MAX_BODY) and `context` is rebuilt from a fixed field list. That bounds the cost of
 * ONE request, not the number of requests: add a Cloudflare rate-limiting rule on this route as well.
 *
 * If the LLM errors or is unconfigured, returns {fallback:true} so the client shows its deterministic
 * plan — the demo never breaks. Set a provider spend cap: this endpoint is public.
 *
 * Deploy: paste into a new Worker (dashboard → Start with Hello World → Edit code), add the vars,
 * Deploy. Verify: curl -X POST <worker-url> -H 'content-type: application/json' -d @sample.json
 */

function cors(allow) {
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
  };
}

const SYSTEM = [
  "You are a district public-health response assistant for Indian District Health Officers.",
  "You are given VERIFIED facts about one district as JSON. Ground every statement strictly in those facts.",
  "Never invent numbers, districts, diseases, or dates. If the facts don't cover something, say so plainly.",
  "Do not give individual medical advice. Write concise, operational, decision-first prose — no preamble.",
].join(" ");

function reply(obj, status, headers) {
  return new Response(JSON.stringify(obj), {
    status, headers: { "content-type": "application/json", ...headers },
  });
}

const MAX_BODY = 8192;   // real payloads are ~1 KB; caps what one request can spend on input tokens
const STR = (v, n = 200) => String(v ?? "").slice(0, n);
const list = a => (Array.isArray(a) ? a : []).slice(0, 12).map(x => STR(x));

// Rebuild the facts from the fields the client really sends, so a caller cannot pad the prompt
// (or the bill) with arbitrary keys or long strings.
function cleanFacts(c) {
  const p = c.deterministic_plan && typeof c.deterministic_plan === "object" ? c.deterministic_plan : {};
  return {
    district: STR(c.district), state: STR(c.state), disease: STR(c.disease), month: STR(c.month),
    tier: STR(c.tier, 20), trend: STR(c.trend, 20), confidence: STR(c.confidence, 20),
    expected_cases_this_month: Number(c.expected_cases_this_month) || 0,
    rank: STR(c.rank),
    seasonal_high_months: list(c.seasonal_high_months),
    deterministic_plan: { posture: STR(p.posture), actions: list(p.actions), resources: STR(p.resources, 400) },
  };
}

export default {
  async fetch(request, env) {
    const allowed = env.ALLOWED_ORIGIN || "*";   // set to your Pages URL to restrict; unset = open
    const origin = request.headers.get("Origin") || "";
    const h = cors(allowed);

    if (request.method === "OPTIONS") return new Response(null, { headers: h });
    if (request.method !== "POST") return reply({ error: "POST only" }, 405, h);
    if (allowed !== "*" && origin !== allowed) return reply({ error: "forbidden origin" }, 403, h);

    if (!env.LLM_BASE_URL || !env.LLM_API_KEY || !env.LLM_MODEL) {
      return reply({ fallback: true, reason: "agent not configured" }, 200, h);
    }

    if (Number(request.headers.get("content-length")) > MAX_BODY) return reply({ error: "too large" }, 413, h);
    const raw = await request.text();
    if (raw.length > MAX_BODY) return reply({ error: "too large" }, 413, h);
    let body;
    try {
      body = JSON.parse(raw);
    } catch {
      return reply({ error: "bad json" }, 400, h);
    }
    if (!body || typeof body !== "object") return reply({ error: "bad json" }, 400, h);
    const question = (body.question || "").toString().slice(0, 500);
    if (!body.context || typeof body.context !== "object" || Array.isArray(body.context)) {
      return reply({ error: "missing context" }, 400, h);
    }
    const facts = cleanFacts(body.context);

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
      if (!r.ok) return reply({ fallback: true, reason: `provider ${r.status}` }, 200, h);
      const data = await r.json();
      const text = data?.choices?.[0]?.message?.content?.trim();
      return text ? reply({ text }, 200, h) : reply({ fallback: true, reason: "empty completion" }, 200, h);
    } catch {
      return reply({ fallback: true, reason: "provider error" }, 200, h);
    } finally {
      clearTimeout(timer);
    }
  },
};
