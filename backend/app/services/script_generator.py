"""
Script Generator Service
Mengimplementasikan system prompt yang sudah terbukti FYP dari chat history.

Dual LLM support:
- Primary: Anthropic Claude (jika ANTHROPIC_API_KEY valid)
- Fallback: Google Gemini (jika GEMINI_API_KEY tersedia)
"""
import json
import re
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# ── Model names ────────────────────────────────────────────────────────────────

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
# OpenRouter: model utama & cadangan (semua gratis, suffix :free)
# Menggunakan 'openrouter/free' agar otomatis di-routing ke model gratis yang sedang tersedia & tidak rate-limit
OPENROUTER_MODEL = "openrouter/free"
OPENROUTER_MODEL_FALLBACK = "openrouter/free"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── Shared prompts ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Kamu adalah scriptwriter TikTok profesional untuk kreator konten Indonesia.

IDENTITAS KREATOR:
- Format: talking head (ngomong langsung ke kamera, bukan narasi visual)
- Target audiens: usia 18-30, mahasiswa, pekerja muda, pecinta self-development
- Bahasa: casual Indonesia, gunakan "gue/lo" (bukan saya/anda/kamu)
- Gaya: santai, conversational, kayak ngobrol sama temen

ATURAN MUTLAK (wajib diikuti, tidak ada pengecualian):
1. Gunakan "bahasa bayi" — jelaskan konsep kompleks sesimpel mungkin
2. Gunakan analogi yang sangat relatable (contoh: "ekonomi itu kayak roda yang muter", "Bitcoin itu kayak grup WhatsApp yang diikutin jutaan orang")
3. Kalimat PENDEK. Satu ide per kalimat. Jangan gabungkan dua ide dalam satu kalimat.
4. Transisi antar paragraf harus NGALIR — bayangkan orang yang lagi ngobrol, bukan yang lagi presentasi
5. JANGAN pakai kata pembuka klise: "Halo teman-teman", "Hai guys", "Apa kabar", "Hei"
6. JANGAN terdengar seperti AI-generated atau membaca artikel
7. Masukkan emosi: takut, nyesel, harapan, penasaran — buat penonton ngerasain sesuatu
8. Seolah-olah ini adalah pengalaman atau pemikiran nyata, bukan review buku/artikel

LARANGAN SPESIFIK — kalimat-kalimat ini DILARANG KERAS:
- Kalimat yang harus dibaca dua kali buat ngerti = REWRITE
- Kalimat yang berbelit-belit = REWRITE
- Istilah teknis tanpa penjelasan langsung = JELASKAN dulu
- Penutup yang terasa dipaksakan atau nggak nyambung = REVISI
- Kalimat loncat-loncat tanpa transisi yang natural = REVISI
- Kalimat yang terasa "robotic" atau "scripted" = HUMANIZE

STRUKTUR WAJIB:
- Hook (detik 0-5): Satu atau dua kalimat yang langsung menampar perhatian. Jangan berikan jawaban di hook.
- Body (detik 5-50): Penjelasan runtut dengan storytelling + analogi. Natural dan mengalir.
- CTA (detik 50-60): Punchline atau insight kuat + ajakan interaksi yang natural (bukan memaksa)

HOOK FORMULA BANK (WAJIB pakai salah satu, boleh dimodifikasi sesuai konten):
1. "[Otoritas/figur besar] baru aja [aksi besar] — dan [konsekuensi menakutkan/mengejutkan]" ← TERBUKTI FYP 900k views
2. "Jangan bilang lo udah [X] kalo lo masih [Y]"
3. "Semua orang SALAH soal [topik]"
4. "Jangan heran kenapa [X] — karena [Y]"
5. "Ini alasan kenapa [X] — dan nggak ada yang berani bilang"
6. "GILA. Kenapa nggak ada yang bilang dari dulu kalo [X]"
7. "Ngaku deh — lo sering ngerasain [X]"
8. "Jangan pernah berani-berani [X]"
9. "Lo pikir [X] — tapi yang terjadi justru sebaliknya"
10. "Ada [sesuatu] yang lagi [terjadi] sekarang — dan hampir nggak ada yang ngomongin ini di Indonesia"

ELEMEN HOOK YANG WAJIB ADA:
- Pattern interrupt: bikin otak berhenti dan nggak bisa scroll
- Psychological trigger: fear + curiosity secara bersamaan
- Curiosity gap: janjikan jawaban tapi JANGAN kasih jawabannya di hook
- Power word: "panik", "rahasia", "salah besar", "gila", "jangan", "seharusnya"

FORMAT RESPONSE:
Selalu kembalikan JSON dengan struktur ini (tidak ada teks di luar JSON):
{
  "hook": "kalimat hook yang kuat",
  "body": "isi script utama yang natural",
  "cta": "call to action penutup yang natural",
  "full_script": "hook + body + cta digabung jadi satu teks utuh",
  "hook_formula_used": "nama/nomor formula yang dipakai",
  "estimated_duration_seconds": 65,
  "naturalness_score": 8.5
}
"""

FEW_SHOT_EXAMPLES = """
CONTOH SCRIPT YANG BAGUS — pelajari gaya, flow, dan bahasanya:

---CONTOH 1 (Hook Formula #10, terbukti 900k views)---
HOOK: Ada yang nanya di komen — kalau listrik dunia beneran padam dan perang dunia ketiga pecah, Bitcoin bakal mati juga dong?

BODY: Oke gue jawab pake analogi yang gampang dulu.

Bayangin Bitcoin itu kayak grup WhatsApp yang diikutin jutaan orang di seluruh dunia. Selama masih ada satu orang yang HP-nya nyala dan konek internet — grup itu tetap ada. Chat history-nya tetap ada. Semua pesan tetap tersimpan.

Nah Bitcoin cara kerjanya mirip kayak gitu.

Dia nggak disimpan di satu server atau satu gedung. Dia tersebar di ribuan komputer di seluruh penjuru dunia. Jadi kalau listrik mati di Indonesia — Bitcoin-nya tetap jalan, karena komputer di Amerika, Eropa, dan negara lain masih nyala.

Lo cuma nggak bisa akses sementara. Tapi Bitcoin lo nggak hilang ke mana-mana.

Sekarang kalau skenarionya listrik mati total di seluruh dunia sekaligus — iya, Bitcoin mati sementara. Tapi di situasi se-ekstrem itu, semua sistem lain juga mati bareng. Bank mati. ATM mati. Kartu kredit nggak bisa dipake.

Jadi bukan Bitcoin yang lemah — semua sistem keuangan yang ada sama-sama collapse.

Dan begitu listrik nyala lagi? Bitcoin balik hidup. Karena dia cuma data. Selama datanya masih ada di salah satu komputer di dunia — semuanya bisa jalan lagi.

CTA: Masih ada pertanyaan soal Bitcoin? Drop di komen — gue jawab di video berikutnya.

---CONTOH 2 (Hook Formula #9, hedonic treadmill)---
HOOK: Lo pikir naik gaji bakal bikin hidup lo lebih bebas — tapi yang terjadi justru sebaliknya.

BODY: Gue punya temen yang gajinya naik dua kali lipat dalam tiga tahun.

Tapi hidupnya nggak berasa lebih bebas. Malah makin stres.

Kenapa? Karena tiap kali gajinya naik, pengeluarannya ikut naik. Apartemen yang lebih mahal. Mobil yang lebih bagus. Gaya hidup yang lebih tinggi.

Ini yang namanya hedonic treadmill — lo lari terus, tapi nggak kemana-mana.

Dan ini jebakan yang hampir semua orang masuk ke dalamnya tanpa sadar.

Orang yang pengeluarannya kecil — hidupnya jauh lebih tenang dari yang lo kira. Dia nggak desperate. Nggak harus nerima kerjaan yang dia benci. Nggak harus tahan sama situasi yang nyiksa dia — cuma karena takut nggak bisa bayar tagihan bulan depan.

Dia punya pilihan. Dan itu sebenernya yang paling berharga.

Beda sama orang yang tiap naik gaji langsung upgrade gaya hidup. Dari luar keliatan sukses. Tapi sebenernya dia terjebak — gajinya harus segitu terus, nggak bisa berhenti, nggak bisa ambil risiko. Karena begitu income-nya turun dikit aja, semua berantakan.

Jadi sebelum lo mikirin mau beli apa lagi — tanya dulu ke diri sendiri. Ini beneran bikin hidup lo lebih bebas, atau cuma bikin lo makin susah buat berhenti?

CTA: Share ke temen lo yang lagi terjebak upgrade gaya hidup terus tapi ngerasa nggak maju-maju.
---
"""

ANGLE_PROMPTS = {
    "hero": "Buat satu script utama yang merangkum insight atau pesan TERPENTING dari konten ini. Ini adalah video utama, jadi buat yang paling impactful.",
    "tips_trick": "Buat script dengan format '3 [kesalahan/tips/cara] yang...' — numbering yang jelas, tapi tetap natural saat diucapkan.",
    "storytelling": "Buat script yang dimulai dari cerita personal atau analogi sehari-hari yang sangat relatable, baru masuk ke insight utama.",
    "controversial": "Buat script dengan statement counter-intuitive atau kontroversial di hook — sesuatu yang bikin orang pengen debat atau penasaran.",
    "reply_komen": "Buat script seolah-olah menjawab pertanyaan dari komentar audiens. Mulai dengan hook yang mengacu ke pertanyaan itu.",
}


# ── Provider detection ─────────────────────────────────────────────────────────

def _get_active_provider() -> str:
    """
    Determine which LLM to use based on available API keys.
    Priority: Anthropic → OpenRouter.
    """
    if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.startswith("sk-ant-"):
        return "anthropic"
    if settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.startswith("sk-or-"):
        return "openrouter"
    raise RuntimeError(
        "No valid LLM API key found. "
        "Set ANTHROPIC_API_KEY (sk-ant-...) or OPENROUTER_API_KEY (sk-or-...) in .env"
    )


# ── JSON cleaning ─────────────────────────────────────────────────────────────

def _clean_json_response(text: str) -> dict:
    """Bersihkan output Markdown dari LLM agar jadi JSON valid."""
    if not text:
        raise ValueError("Received empty or None response from LLM")
    
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if code_block:
        try:
            return json.loads(code_block.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Fallback: find first { ... }
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in response (length: {len(text)}). Preview: {text[:200]}")


# ── Anthropic client ───────────────────────────────────────────────────────────

def _call_anthropic(system: str, user_prompt: str, max_tokens: int = 1500) -> str:
    """Call Anthropic Claude API. Returns raw text."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


# ── OpenRouter client ──────────────────────────────────────────────────────────

def _call_openrouter(system: str, user_prompt: str, max_tokens: int = 1500) -> str:
    """
    Call OpenRouter API (OpenAI-compatible format).
    - Retries with OPENROUTER_MODEL_FALLBACK if primary model returns 404
    - Auto-retries once on 429 rate limit with Retry-After header
    """
    import time
    import requests as req

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_prompt})

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-content-analyzer.local",
        "X-Title": "AI Content Analyzer",
    }

    models_to_try = [OPENROUTER_MODEL, OPENROUTER_MODEL_FALLBACK]

    for model in models_to_try:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.9,
        }

        for attempt in range(2):  # retry sekali jika kena 429
            response = req.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                logger.warning(f"[LLM/OpenRouter] Rate limited on {model}. Retrying in {retry_after}s...")
                time.sleep(retry_after)
                continue

            if response.status_code == 404:
                # Model tidak tersedia, coba model berikutnya
                logger.warning(f"[LLM/OpenRouter] Model {model} not found (404), trying fallback model...")
                break  # break inner loop → next model

            if not response.ok:
                raise RuntimeError(
                    f"OpenRouter API error {response.status_code} on model {model}: {response.text[:300]}"
                )

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(f"[LLM/OpenRouter] Success with model: {model}")
            return content

    raise RuntimeError(f"OpenRouter: all models failed ({', '.join(models_to_try)})")



# ── Unified LLM caller ────────────────────────────────────────────────────────

def _call_llm(system: str, user_prompt: str, max_tokens: int = 1500) -> tuple[str, str]:
    """
    Call the best available LLM.
    Returns (raw_text, model_name_used).

    Priority:
    1. Anthropic Claude (sk-ant-...)
    2. OpenRouter free model (sk-or-...)
    Fallback antar provider jika salah satu gagal.
    """
    provider = _get_active_provider()

    if provider == "anthropic":
        try:
            raw = _call_anthropic(system, user_prompt, max_tokens)
            logger.info(f"[LLM] Used Anthropic ({CLAUDE_MODEL})")
            return raw, CLAUDE_MODEL
        except Exception as e:
            logger.warning(f"[LLM] Anthropic failed: {e}. Trying OpenRouter fallback...")
            if settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.startswith("sk-or-"):
                raw = _call_openrouter(system, user_prompt, max_tokens)
                logger.info(f"[LLM] Fallback to OpenRouter ({OPENROUTER_MODEL})")
                return raw, OPENROUTER_MODEL
            raise

    if provider == "openrouter":
        raw = _call_openrouter(system, user_prompt, max_tokens)
        logger.info(f"[LLM] Used OpenRouter ({OPENROUTER_MODEL})")
        return raw, OPENROUTER_MODEL


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_scripts_for_content(
    article_content: str,
    niche_name: str = "Self-Development",
    niche_keywords: list = None,
    custom_rules: str = None,
    angles: list = None,
    duration_seconds: int = 60,
) -> list[dict]:
    """
    Generate multiple scripts dengan angle berbeda untuk satu artikel.
    Otomatis memilih Anthropic atau Gemini berdasarkan API key yang tersedia.
    """
    if angles is None:
        angles = ["hero", "tips_trick", "controversial"]

    keywords_str = ", ".join(niche_keywords) if niche_keywords else ""
    duration_note = f"Durasi target: {duration_seconds} detik (~{int(duration_seconds * 2.5)} kata)"

    results = []

    for angle in angles:
        angle_instruction = ANGLE_PROMPTS.get(angle, ANGLE_PROMPTS["hero"])

        user_prompt = f"""
{FEW_SHOT_EXAMPLES}

---TUGAS SEKARANG---
Niche: {niche_name}
Keywords relevan: {keywords_str}
{duration_note}
Angle script: {angle_instruction}
{"Aturan tambahan: " + custom_rules if custom_rules else ""}

ARTIKEL/KONTEN SUMBER:
{article_content[:4000]}

Buatkan script TikTok sesuai format JSON yang sudah ditentukan.
Ingat: natural, bahasa manusia, tidak AI-generated, sesuai gaya contoh di atas.
"""

        try:
            raw, model_used = _call_llm(SYSTEM_PROMPT, user_prompt)
            script_data = _clean_json_response(raw)
            script_data["angle"] = angle
            script_data["claude_model"] = model_used  # backward compatible field name
            results.append(script_data)
        except Exception as e:
            logger.error(f"[Pipeline] Failed to generate script for angle {angle}: {e}")
            # Continue to next angle instead of crashing
        
        import time
        time.sleep(5) # Jeda antar angle agar tidak kena rate limit

    return results


def score_relevance(
    content: str,
    niche_name: str,
    keywords: list,
) -> tuple[float, str]:
    """
    Score relevance of a tweet/article for a given niche.
    Returns (score 0.0-1.0, reason).
    """
    prompt = f"""
Kamu adalah content strategist untuk TikTok Indonesia.

Niche channel: {niche_name}
Keywords target: {", ".join(keywords)}

Nilai apakah konten berikut relevan untuk dijadikan konten TikTok talking head di niche ini.
Konten yang bagus adalah yang punya insight menarik, counter-intuitive, atau informatif untuk audiens usia 18-30 Indonesia.

KONTEN:
{content[:2000]}

Berikan penilaian dalam format JSON (hanya JSON, tidak ada teks lain):
{{"score": 0.85, "reason": "Alasan singkat 1-2 kalimat mengapa relevan atau tidak"}}

Score 0.0 = sama sekali tidak relevan
Score 1.0 = sangat relevan dan potensial viral
"""

    raw, _ = _call_llm("", prompt, max_tokens=200)
    result = _clean_json_response(raw)
    return float(result["score"]), result["reason"]
