import json
import re
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Agro & Biosystems Systematic Review Builder",
    page_icon="🌱",
    layout="wide",
)

APP_TITLE = "Agro & Biosystems Systematic Review Builder"
APP_VERSION = "AI Included + TOML Secrets Edition"
SLASHAI_DEFAULT_API_BASE = "https://api.slashai.my.id"
SLASHAI_DEFAULT_MODEL = "slashai/gemini-3-flash"
SLASHAI_HIGH_QUALITY_MODEL = "slashai/gemini-3.1-pro"

ARTICLE_COLUMNS = [
    "id", "title", "authors", "year", "journal", "doi", "country", "study_design",
    "species_or_crop", "intervention", "comparator", "outcome", "abstract", "source_database",
    "duplicate", "picos_relevance_score", "auto_screening_suggestion", "reviewer1_decision",
    "reviewer2_decision", "screening_conflict", "consensus_decision", "screening_decision",
    "exclusion_reason", "full_text_decision", "full_text_exclusion_reason", "notes"
]

EXTRACTION_COLUMNS = [
    "id", "title", "species_or_crop", "intervention", "comparator", "sample_size", "duration",
    "main_outcome", "outcome_unit", "mean_intervention", "sd_intervention", "n_intervention",
    "mean_control", "sd_control", "n_control", "effect_direction", "effect_size", "p_value",
    "key_finding", "limitations", "implication", "novelty_note"
]

QUALITY_COLUMNS = [
    "id", "title", "clear_objective", "appropriate_design", "adequate_sample", "clear_intervention",
    "valid_outcome", "adequate_statistics", "bias_control", "complete_reporting", "selection_bias",
    "performance_bias", "detection_bias", "attrition_bias", "reporting_bias", "other_bias",
    "quality_score", "quality_category", "overall_risk_of_bias", "certainty_of_evidence", "risk_of_bias_note"
]

DOMAIN_PROFILES = {
    "Peternakan": {
        "objects": ["broiler", "poultry", "chicken", "layer", "ruminant", "cattle", "goat", "sheep", "duck"],
        "interventions": ["probiotic", "prebiotic", "synbiotic", "feed additive", "herbal", "black soldier fly", "bsf", "insect meal"],
        "outcomes": ["feed conversion", "fcr", "body weight", "growth", "mortality", "egg production", "milk yield", "methane"],
        "databases": ["Scopus", "Web of Science", "CAB Abstracts", "ScienceDirect", "PubMed", "SpringerLink"],
        "quality_tool": "SYRCLE risk of bias untuk animal experiment, JBI checklist untuk studi observasional, atau checklist eksperimen pakan.",
    },
    "Agro/Agronomi": {
        "objects": ["maize", "corn", "rice", "paddy", "soil", "crop", "wheat", "soybean", "horticulture", "plant"],
        "interventions": ["biochar", "organic fertilizer", "compost", "manure", "irrigation", "mulch", "drought", "precision agriculture"],
        "outcomes": ["yield", "productivity", "soil organic carbon", "nitrogen", "water use efficiency", "biomass"],
        "databases": ["Scopus", "Web of Science", "AGRICOLA", "CAB Abstracts", "ScienceDirect", "SpringerLink"],
        "quality_tool": "ROSES/CEE critical appraisal, JBI adapted checklist, atau checklist eksperimen lapang/greenhouse.",
    },
    "Perikanan/Akuakultur": {
        "objects": ["fish", "shrimp", "tilapia", "catfish", "aquaculture", "feed", "pond", "larvae"],
        "interventions": ["probiotic", "prebiotic", "feed additive", "biofloc", "herbal", "alternative protein", "water quality"],
        "outcomes": ["growth", "survival", "feed conversion", "water quality", "immune response", "disease resistance"],
        "databases": ["Scopus", "Web of Science", "ScienceDirect", "Aquatic Sciences and Fisheries Abstracts", "CAB Abstracts"],
        "quality_tool": "SYRCLE/JBI adapted checklist untuk eksperimen akuakultur dan checklist reporting trial.",
    },
    "Pangan": {
        "objects": ["food", "meat", "milk", "egg", "grain", "rice", "vegetable", "fruit", "processed food"],
        "interventions": ["processing", "fermentation", "packaging", "storage", "preservation", "drying", "edible coating"],
        "outcomes": ["quality", "shelf life", "nutrition", "sensory", "antioxidant", "microbial", "safety"],
        "databases": ["Scopus", "Web of Science", "ScienceDirect", "PubMed", "Wiley", "SpringerLink"],
        "quality_tool": "JBI checklist, ROBINS-I, atau checklist metodologi pangan sesuai desain penelitian.",
    },
    "Lingkungan": {
        "objects": ["ecosystem", "soil", "water", "biodiversity", "land use", "climate", "agroecosystem"],
        "interventions": ["conservation", "restoration", "management", "mitigation", "adaptation", "biochar", "agroforestry"],
        "outcomes": ["emission", "carbon", "biodiversity", "water quality", "soil health", "resilience", "sustainability"],
        "databases": ["Scopus", "Web of Science", "Environmental Evidence", "ScienceDirect", "SpringerLink"],
        "quality_tool": "ROSES dan Collaboration for Environmental Evidence/CEE critical appraisal.",
    },
    "Teknik Pertanian dan Biosistem": {
        "objects": ["agricultural machinery", "farm machinery", "irrigation", "greenhouse", "postharvest", "drying", "sensor", "iot", "remote sensing", "precision agriculture", "biosystem", "soil", "crop"],
        "interventions": ["smart irrigation", "automated irrigation", "precision agriculture", "mechanization", "controlled traffic", "dryer", "solar dryer", "greenhouse technology", "sensor", "iot", "drone", "remote sensing", "decision support", "renewable energy"],
        "outcomes": ["water use efficiency", "crop yield", "energy efficiency", "labor productivity", "drying rate", "product quality", "soil compaction", "irrigation efficiency", "system performance", "cost", "adoption", "emission"],
        "databases": ["Scopus", "Web of Science", "CAB Abstracts", "AGRICOLA", "ASABE Technical Library", "ScienceDirect", "IEEE Xplore", "SpringerLink"],
        "quality_tool": "ROSES/CEE critical appraisal, JBI adapted checklist, serta checklist rekayasa untuk validasi alat, performa, simulasi-model, dan sensor/IoT.",
    },
}

EXAMPLES = {
    ("Peternakan", "PICOS"): {
        "title": "Effects of Probiotic Supplementation on Growth Performance and Feed Conversion Ratio in Broiler Chickens: A Systematic Review and Meta-Analysis",
        "population": "broiler chickens", "intervention": "probiotic supplementation", "comparator": "control diet or non-supplemented diet", "outcome": "growth performance; feed conversion ratio; body weight gain; mortality", "study_design": "experimental studies or feeding trials",
    },
    ("Agro/Agronomi", "PICOS"): {
        "title": "Effects of Biochar Application on Maize Yield and Soil Organic Carbon in Tropical Agriculture: A Systematic Review and Meta-Analysis",
        "population": "maize crops or tropical agricultural soils", "intervention": "biochar application", "comparator": "no biochar or conventional fertilization", "outcome": "maize yield; soil organic carbon; nutrient availability; water use efficiency", "study_design": "field trials and greenhouse experiments",
    },
    ("Perikanan/Akuakultur", "PICOS"): {
        "title": "Effects of Probiotic Supplementation on Growth Performance and Survival of Nile Tilapia: A Systematic Review and Meta-Analysis",
        "population": "Nile tilapia or cultured fish", "intervention": "probiotic supplementation", "comparator": "control feed or non-supplemented diet", "outcome": "growth performance; survival rate; feed conversion ratio; immune response", "study_design": "aquaculture feeding trials and controlled experiments",
    },
    ("Pangan", "PICO"): {
        "title": "Edible Coating for Extending Shelf Life of Fresh Fruits: A Systematic Review",
        "population": "fresh fruits", "intervention": "edible coating", "comparator": "uncoated control or conventional packaging", "outcome": "shelf life; weight loss; firmness; microbial quality", "study_design": "controlled postharvest experiments",
    },
    ("Lingkungan", "PECO"): {
        "title": "Effects of Land-Use Change Exposure on Soil Carbon and Biodiversity in Agroecosystems: A Systematic Review",
        "population": "agroecosystems or agricultural landscapes", "intervention": "land-use change exposure", "comparator": "unchanged land use or reference ecosystem", "outcome": "soil carbon; biodiversity; ecosystem services; soil quality", "study_design": "observational studies and comparative ecological studies",
    },
    ("Teknik Pertanian dan Biosistem", "PICOS"): {
        "title": "Smart Irrigation Technologies for Improving Water Use Efficiency and Crop Yield in Agricultural Systems: A Systematic Review",
        "population": "agricultural cropping systems or irrigated farms", "intervention": "smart irrigation technologies or automated irrigation systems", "comparator": "conventional irrigation or farmer-managed irrigation", "outcome": "water use efficiency; crop yield; irrigation water productivity; energy use; system performance", "study_design": "field trials, controlled experiments, and simulation-validation studies",
    },
    ("Teknik Pertanian dan Biosistem", "PICO"): {
        "title": "Solar Drying Technologies for Improving Drying Performance and Quality of Agricultural Products: A Systematic Review",
        "population": "agricultural products or postharvest commodities", "intervention": "solar drying technologies or hybrid dryers", "comparator": "open sun drying or conventional drying methods", "outcome": "drying rate; energy efficiency; product quality; moisture reduction; microbial safety", "study_design": "laboratory experiments, prototype performance tests, and postharvest trials",
    },
    ("Teknik Pertanian dan Biosistem", "PECO"): {
        "title": "Effects of Agricultural Machinery Traffic Exposure on Soil Compaction and Crop Performance: A Systematic Review",
        "population": "agricultural soils or cropping systems", "intervention": "agricultural machinery traffic exposure", "comparator": "no traffic, controlled traffic, or low-intensity machinery traffic", "outcome": "soil compaction; bulk density; penetration resistance; crop yield; soil physical quality", "study_design": "field studies, controlled traffic experiments, and observational studies",
    },
}


def default_project() -> Dict[str, Any]:
    return {
        "title": "",
        "domain": "Teknik Pertanian dan Biosistem",
        "framework": "PICOS",
        "target_quartile": "Q2",
        "population": "",
        "intervention": "",
        "comparator": "",
        "outcome": "",
        "study_design": "",
        "research_question": "",
        "protocol_notes": "",
    }


def init_state() -> None:
    defaults = {
        "project": default_project(),
        "criteria": {"inclusion": [], "exclusion": []},
        "terms": {"population_terms": "", "intervention_terms": "", "comparator_terms": "", "outcome_terms": "", "study_terms": "", "boolean_search": ""},
        "articles": pd.DataFrame(columns=ARTICLE_COLUMNS),
        "quality": pd.DataFrame(columns=QUALITY_COLUMNS),
        "extraction": pd.DataFrame(columns=EXTRACTION_COLUMNS),
        "notes": "",
        "ai_outputs": {},
        "reset_confirmed": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def safe_str(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return str(value)


def clean_terms(value: str) -> List[str]:
    text = safe_str(value).lower()
    parts = re.split(r"[;,\n/|]+", text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


def sanitize_api_key(value: str) -> str:
    key = safe_str(value).strip()
    key = re.sub(r"^authorization:\s*", "", key, flags=re.I).strip()
    key = re.sub(r"^bearer\s+", "", key, flags=re.I).strip()
    return key


def normalize_api_base_url(value: str) -> str:
    base = safe_str(value).strip() or SLASHAI_DEFAULT_API_BASE
    base = base.rstrip("/")
    base = re.sub(r"/v1/chat/completions$", "", base)
    base = re.sub(r"/chat/completions$", "", base)
    base = re.sub(r"/v1$", "", base)
    return base


def chat_completions_url(base_url: str) -> str:
    return normalize_api_base_url(base_url) + "/v1/chat/completions"


def get_ai_secrets() -> Dict[str, Any]:
    """Membaca konfigurasi AI dari .streamlit/secrets.toml atau Secrets Streamlit Cloud."""
    try:
        ai = st.secrets.get("ai", {})
    except Exception:
        ai = {}
    return {
        "enabled": bool(ai.get("enabled", False)),
        "api_base_url": normalize_api_base_url(ai.get("api_base_url", SLASHAI_DEFAULT_API_BASE)),
        "api_key": sanitize_api_key(ai.get("api_key", "")),
        "default_model": safe_str(ai.get("default_model", SLASHAI_DEFAULT_MODEL)) or SLASHAI_DEFAULT_MODEL,
        "high_quality_model": safe_str(ai.get("high_quality_model", SLASHAI_HIGH_QUALITY_MODEL)) or SLASHAI_HIGH_QUALITY_MODEL,
    }


def get_system_api_key() -> str:
    return get_ai_secrets().get("api_key", "")


def get_system_api_base_url() -> str:
    return get_ai_secrets().get("api_base_url", SLASHAI_DEFAULT_API_BASE)


def get_effective_api_key() -> str:
    system_key = get_system_api_key()
    if system_key and "MASUKKAN" not in system_key.upper() and "GANTI" not in system_key.upper():
        return system_key
    return sanitize_api_key(st.session_state.get("manual_api_key", ""))


def get_effective_base_url() -> str:
    if get_system_api_base_url():
        return get_system_api_base_url()
    return normalize_api_base_url(st.session_state.get("manual_api_base_url", SLASHAI_DEFAULT_API_BASE))


def get_selected_model() -> str:
    secrets = get_ai_secrets()
    mode = st.session_state.get("ai_model_mode", "Hemat biaya")
    if mode == "Kualitas tinggi":
        return secrets.get("high_quality_model", SLASHAI_HIGH_QUALITY_MODEL)
    if mode == "Manual":
        return st.session_state.get("manual_model", secrets.get("default_model", SLASHAI_DEFAULT_MODEL)) or SLASHAI_DEFAULT_MODEL
    return secrets.get("default_model", SLASHAI_DEFAULT_MODEL)


def title_score(title: str) -> Tuple[int, List[str]]:
    score = 20
    issues = []
    t = safe_str(title).lower()
    if len(title.split()) >= 10:
        score += 20
    else:
        issues.append("Judul masih terlalu pendek; tambahkan population, intervention/exposure, outcome, dan jenis review.")
    if "systematic review" in t:
        score += 20
    else:
        issues.append("Tambahkan frasa 'systematic review' agar jenis naskah jelas.")
    if "meta-analysis" in t or "meta analysis" in t:
        score += 10
    if any(word in t for word in ["effect", "impact", "improving", "association", "pengaruh", "dampak"]):
        score += 10
    else:
        issues.append("Rumusan hubungan/intervensi belum terlihat kuat.")
    if ":" in title:
        score += 10
    if len(t) > 160:
        score -= 10
        issues.append("Judul cukup panjang; pertimbangkan memadatkan agar lebih tajam.")
    return max(0, min(100, score)), issues


def generate_research_question(p: Dict[str, Any]) -> str:
    framework = p.get("framework", "PICOS")
    pop = p.get("population") or "target population"
    inter = p.get("intervention") or "intervention/exposure"
    comp = p.get("comparator") or "comparator/control"
    out = p.get("outcome") or "main outcomes"
    if framework == "PECO":
        return f"How does {inter} exposure affect {out} in {pop} compared with {comp}?"
    return f"How does {inter} affect {out} in {pop} compared with {comp}?"


def generate_protocol(p: Dict[str, Any]) -> Tuple[List[str], List[str], Dict[str, str]]:
    framework = p.get("framework", "PICOS")
    inclusion = [
        f"Studi membahas {p.get('population') or 'population yang sesuai'}.",
        f"Studi menguji/mengkaji {p.get('intervention') or 'intervention/exposure yang sesuai'}.",
        f"Studi melaporkan outcome terkait {p.get('outcome') or 'outcome utama'}.",
        "Artikel jurnal/prosiding ilmiah dengan informasi metode yang dapat ditelusuri.",
        "Data tersedia cukup untuk proses screening, quality assessment, dan ekstraksi.",
    ]
    if framework == "PICOS":
        inclusion.append(f"Desain studi sesuai: {p.get('study_design') or 'desain eksperimental/observasional yang relevan'}.")
    exclusion = [
        "Artikel duplikat, editorial, opini, poster tanpa data lengkap, atau abstrak konferensi tanpa full paper.",
        "Studi tidak relevan dengan population/intervention/exposure/outcome yang telah ditentukan.",
        "Studi tidak menyediakan data hasil yang dapat diekstraksi.",
        "Artikel non-ilmiah atau sumber yang tidak dapat diverifikasi.",
    ]
    terms = {
        "population_terms": p.get("population", ""),
        "intervention_terms": p.get("intervention", ""),
        "comparator_terms": p.get("comparator", ""),
        "outcome_terms": p.get("outcome", ""),
        "study_terms": p.get("study_design", "") if framework == "PICOS" else "observational study; experimental study; field study",
    }
    terms["boolean_search"] = make_boolean_search(terms)
    return inclusion, exclusion, terms


def make_boolean_search(terms: Dict[str, str]) -> str:
    groups = []
    for key in ["population_terms", "intervention_terms", "comparator_terms", "outcome_terms", "study_terms"]:
        values = clean_terms(terms.get(key, ""))
        if values:
            groups.append("(" + " OR ".join([f'"{v}"' for v in values]) + ")")
    return " AND ".join(groups)


def normalize_articles(df: pd.DataFrame) -> pd.DataFrame:
    normalized = pd.DataFrame(columns=ARTICLE_COLUMNS)
    rename_map = {
        "Title": "title", "Authors": "authors", "Year": "year", "Source title": "journal", "Journal": "journal",
        "DOI": "doi", "Abstract": "abstract", "Source": "source_database", "Keywords": "notes",
    }
    df = df.rename(columns={c: rename_map.get(c, c.lower().strip().replace(" ", "_")) for c in df.columns})
    for col in ARTICLE_COLUMNS:
        normalized[col] = df[col] if col in df.columns else ""
    normalized["id"] = [f"S{i+1:03d}" for i in range(len(normalized))]
    normalized["duplicate"] = normalized.duplicated(subset=["doi"], keep="first") | normalized.duplicated(subset=["title"], keep="first")
    return auto_score_articles(normalized)


def parse_ris(uploaded) -> pd.DataFrame:
    text = uploaded.read().decode("utf-8", errors="ignore")
    records, current = [], {}
    tag_map = {"TI": "title", "T1": "title", "AU": "authors", "PY": "year", "Y1": "year", "JO": "journal", "JF": "journal", "DO": "doi", "AB": "abstract"}
    for raw in text.splitlines():
        if raw.startswith("TY  -"):
            current = {}
        elif raw.startswith("ER  -"):
            if current:
                records.append(current)
            current = {}
        elif "  - " in raw:
            tag, value = raw.split("  - ", 1)
            col = tag_map.get(tag.strip())
            if col:
                if col == "authors" and current.get(col):
                    current[col] = current[col] + "; " + value.strip()
                else:
                    current[col] = value.strip()
    return normalize_articles(pd.DataFrame(records))


def auto_score_articles(df: pd.DataFrame) -> pd.DataFrame:
    p = st.session_state.project
    wanted = clean_terms(";".join([p.get("population", ""), p.get("intervention", ""), p.get("outcome", "")]))
    suggestions = []
    scores = []
    for _, row in df.iterrows():
        text = " ".join([safe_str(row.get("title")), safe_str(row.get("abstract")), safe_str(row.get("species_or_crop")), safe_str(row.get("intervention")), safe_str(row.get("outcome"))]).lower()
        hits = sum(1 for term in wanted if term in text)
        score = int(min(100, hits * 20)) if wanted else 0
        if row.get("duplicate"):
            suggestion = "Exclude - Duplicate"
        elif score >= 60:
            suggestion = "Include"
        elif score >= 30:
            suggestion = "Maybe"
        else:
            suggestion = "Exclude"
        scores.append(score)
        suggestions.append(suggestion)
    df["picos_relevance_score"] = scores
    df["auto_screening_suggestion"] = suggestions
    df["screening_decision"] = df["screening_decision"].replace("", np.nan).fillna(df["auto_screening_suggestion"])
    return df


def ensure_quality_from_articles() -> None:
    included = st.session_state.articles[st.session_state.articles.get("screening_decision", "").astype(str).str.contains("Include", case=False, na=False)] if len(st.session_state.articles) else pd.DataFrame()
    rows = []
    for _, r in included.iterrows():
        existing = st.session_state.quality[st.session_state.quality.get("id", "") == r.get("id")] if len(st.session_state.quality) else pd.DataFrame()
        if len(existing):
            rows.append(existing.iloc[0].to_dict())
        else:
            rows.append({
                "id": r.get("id"), "title": r.get("title"), "clear_objective": True, "appropriate_design": True,
                "adequate_sample": False, "clear_intervention": True, "valid_outcome": True, "adequate_statistics": False,
                "bias_control": False, "complete_reporting": False, "selection_bias": "Unclear", "performance_bias": "Unclear",
                "detection_bias": "Unclear", "attrition_bias": "Unclear", "reporting_bias": "Unclear", "other_bias": "Unclear",
                "quality_score": 0, "quality_category": "", "overall_risk_of_bias": "Unclear", "certainty_of_evidence": "Moderate", "risk_of_bias_note": "",
            })
    df = pd.DataFrame(rows, columns=QUALITY_COLUMNS)
    if len(df):
        bool_cols = ["clear_objective", "appropriate_design", "adequate_sample", "clear_intervention", "valid_outcome", "adequate_statistics", "bias_control", "complete_reporting"]
        df["quality_score"] = df[bool_cols].apply(lambda row: int(sum(bool(x) for x in row) / len(bool_cols) * 100), axis=1)
        df["quality_category"] = pd.cut(df["quality_score"], bins=[-1, 49, 74, 100], labels=["Low", "Moderate", "High"]).astype(str)
        df["overall_risk_of_bias"] = df["quality_category"].map({"High": "Low", "Moderate": "Unclear", "Low": "High"}).fillna("Unclear")
    st.session_state.quality = df


def ensure_extraction_from_articles() -> None:
    included = st.session_state.articles[st.session_state.articles.get("screening_decision", "").astype(str).str.contains("Include", case=False, na=False)] if len(st.session_state.articles) else pd.DataFrame()
    rows = []
    for _, r in included.iterrows():
        existing = st.session_state.extraction[st.session_state.extraction.get("id", "") == r.get("id")] if len(st.session_state.extraction) else pd.DataFrame()
        if len(existing):
            rows.append(existing.iloc[0].to_dict())
        else:
            rows.append({"id": r.get("id"), "title": r.get("title"), "species_or_crop": r.get("species_or_crop"), "intervention": r.get("intervention"), "comparator": r.get("comparator"), "main_outcome": r.get("outcome")})
    st.session_state.extraction = pd.DataFrame(rows, columns=EXTRACTION_COLUMNS)


def prisma_counts() -> Dict[str, int]:
    df = st.session_state.articles
    total = len(df)
    dup = int(df["duplicate"].sum()) if total and "duplicate" in df else 0
    screened = max(0, total - dup)
    included = int(df.get("screening_decision", pd.Series(dtype=str)).astype(str).str.contains("Include", case=False, na=False).sum()) if total else 0
    excluded = int(df.get("screening_decision", pd.Series(dtype=str)).astype(str).str.contains("Exclude", case=False, na=False).sum()) if total else 0
    maybe = int(df.get("screening_decision", pd.Series(dtype=str)).astype(str).str.contains("Maybe", case=False, na=False).sum()) if total else 0
    return {"records_identified": total, "duplicates_removed": dup, "records_screened": screened, "records_excluded": excluded, "full_text_assessed": included + maybe, "studies_included": included}


def project_context() -> Dict[str, Any]:
    return {
        "project": st.session_state.project,
        "criteria": st.session_state.criteria,
        "terms": st.session_state.terms,
        "prisma": prisma_counts(),
        "articles_preview": st.session_state.articles.head(15).to_dict(orient="records"),
        "quality_preview": st.session_state.quality.head(15).to_dict(orient="records"),
        "extraction_preview": st.session_state.extraction.head(15).to_dict(orient="records"),
        "notes": st.session_state.notes,
    }


def make_ai_prompt(task: str) -> str:
    return f"""Anda adalah asisten metodologi systematic review bidang agro, peternakan, biosistem, pangan, lingkungan, dan akuakultur.

Tugas: {task}

Gunakan data project berikut dan jangan mengarang angka atau referensi baru yang tidak tersedia.

```json
{json.dumps(project_context(), ensure_ascii=False, indent=2, default=str)}
```

Format jawaban:
1. Ringkasan diagnosis
2. Insight utama
3. Kelemahan yang perlu diperbaiki
4. Rekomendasi langkah praktis
5. Catatan kehati-hatian agar kesimpulan tidak berlebihan

Gunakan Bahasa Indonesia formal, akademik, jelas, dan langsung bisa dipakai untuk memperbaiki naskah systematic review.
"""


def call_ai(prompt: str) -> Tuple[bool, str]:
    api_key = get_effective_api_key()
    if not api_key:
        return False, "API key belum tersedia. Isi `.streamlit/secrets.toml` pada bagian [ai].api_key atau masukkan key sementara di sidebar."
    model = get_selected_model()
    url = chat_completions_url(get_effective_base_url())
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Anda adalah asisten akademik untuk systematic review dan naskah jurnal bereputasi."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "model": model}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code >= 400:
            return False, f"Gagal memanggil API ({response.status_code}): {response.text[:1200]}"
        data = response.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return True, text or json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as exc:
        return False, f"Gagal koneksi API: {exc}"


def dataframe_to_xlsx_bytes(sheets: Dict[str, pd.DataFrame]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe_name = re.sub(r"[^A-Za-z0-9 _-]", "", name)[:31] or "Sheet1"
            df.to_excel(writer, sheet_name=safe_name, index=False)
    return buffer.getvalue()


def make_project_zip() -> bytes:
    buffer = BytesIO()
    context = project_context()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project_state.json", json.dumps(context, ensure_ascii=False, indent=2, default=str))
        zf.writestr("protocol_and_search_strategy.md", build_protocol_markdown())
        zf.writestr("ai_prompt.txt", make_ai_prompt("Novelty & Gap Insight"))
        xlsx = dataframe_to_xlsx_bytes({
            "articles_screening": st.session_state.articles,
            "quality_assessment": st.session_state.quality,
            "data_extraction": st.session_state.extraction,
            "prisma_counts": pd.DataFrame([prisma_counts()]),
        })
        zf.writestr("review_tables.xlsx", xlsx)
    return buffer.getvalue()


def build_protocol_markdown() -> str:
    p = st.session_state.project
    return f"""# Protocol and Search Strategy

## Title
{p.get('title')}

## Framework
{p.get('framework')} - {p.get('domain')}

## Research Question
{p.get('research_question')}

## Components
- Population: {p.get('population')}
- Intervention/Exposure: {p.get('intervention')}
- Comparator: {p.get('comparator')}
- Outcome: {p.get('outcome')}
- Study Design: {p.get('study_design')}

## Inclusion Criteria
{chr(10).join([f'- {x}' for x in st.session_state.criteria.get('inclusion', [])])}

## Exclusion Criteria
{chr(10).join([f'- {x}' for x in st.session_state.criteria.get('exclusion', [])])}

## Boolean Search
```text
{st.session_state.terms.get('boolean_search', '')}
```

## Notes
{st.session_state.notes}
"""


def completion_status() -> Tuple[Dict[str, bool], int]:
    p = st.session_state.project
    checks = {
        "Judul & framework": bool(p.get("title") and p.get("framework")),
        "P/I/E/C/O terisi": bool(p.get("population") and p.get("intervention") and p.get("comparator") and p.get("outcome")),
        "Protocol & search": bool(st.session_state.terms.get("boolean_search")),
        "Artikel import": len(st.session_state.articles) > 0,
        "Screening": len(st.session_state.articles) > 0 and "screening_decision" in st.session_state.articles,
        "Quality assessment": len(st.session_state.quality) > 0,
        "Data extraction": len(st.session_state.extraction) > 0,
    }
    pct = int(sum(checks.values()) / len(checks) * 100)
    return checks, pct


def reset_project() -> None:
    for key in ["project", "criteria", "terms", "articles", "quality", "extraction", "notes", "ai_outputs", "manual_api_key", "manual_model", "ai_model_mode"]:
        st.session_state.pop(key, None)
    init_state()


def render_sidebar() -> str:
    checks, pct = completion_status()
    st.sidebar.title("Workflow")
    st.sidebar.progress(pct / 100)
    st.sidebar.caption(f"Progress: {pct}%")
    for label, ok in checks.items():
        st.sidebar.write(("✅" if ok else "⬜") + " " + label)
    st.sidebar.divider()

    with st.sidebar.expander("🤖 AI Sistem + API TOML", expanded=True):
        secrets = get_ai_secrets()
        system_key = get_system_api_key()
        system_ready = bool(system_key) and "MASUKKAN" not in system_key.upper() and "GANTI" not in system_key.upper()
        if system_ready:
            st.success("AI sistem aktif dari `.streamlit/secrets.toml`.")
        else:
            st.warning("API sistem belum aktif. Isi `api_key` di `.streamlit/secrets.toml` atau Secrets Streamlit Cloud.")
            st.text_input("API Key sementara", type="password", key="manual_api_key", help="Fallback sementara bila secrets.toml belum diisi.")
        st.caption(f"API Base: `{secrets.get('api_base_url')}`")
        st.radio("Mode model", ["Hemat biaya", "Kualitas tinggi", "Manual"], key="ai_model_mode", horizontal=False)
        if st.session_state.get("ai_model_mode") == "Manual":
            st.text_input("Model manual", value=secrets.get("default_model", SLASHAI_DEFAULT_MODEL), key="manual_model")
        st.caption(f"Model aktif: `{get_selected_model()}`")

    page = st.sidebar.radio(
        "Menu",
        ["Panduan Workflow", "1. Judul & PICOS/PECO", "2. Protocol & Search", "3. Import & Screening", "4. PRISMA & Quality", "5. Data Extraction", "6. AI Insight", "7. Export", "⚠️ Reset"],
    )
    st.sidebar.caption(APP_VERSION)
    return page


def page_workflow() -> None:
    st.title(f"🌱 {APP_TITLE}")
    st.caption(APP_VERSION)
    st.info("Sistem ini menyatukan alur systematic review: judul → PICOS/PECO → protocol → search strategy → screening → PRISMA → quality assessment → data extraction → AI insight → export.")
    cols = st.columns(4)
    counts = prisma_counts()
    cols[0].metric("Artikel", counts["records_identified"])
    cols[1].metric("Duplikat", counts["duplicates_removed"])
    cols[2].metric("Include", counts["studies_included"])
    cols[3].metric("Progress", f"{completion_status()[1]}%")
    steps = [
        ("1", "Judul & PICOS/PECO", "Menentukan bidang, framework, komponen riset, dan kelayakan judul."),
        ("2", "Protocol & Search", "Membuat inclusion-exclusion criteria, keyword, dan Boolean search."),
        ("3", "Import & Screening", "Mengunggah artikel XLSX/XLS/CSV/RIS, deduplikasi, dan skor relevansi."),
        ("4", "PRISMA & Quality", "Menghitung PRISMA dan menilai kualitas/risk of bias."),
        ("5", "Data Extraction", "Mengisi outcome, effect direction, effect size, temuan, limitasi, dan implikasi."),
        ("6", "AI Insight", "Membuat analisis novelty, gap, discussion, reviewer simulation, dan improvement plan."),
        ("7", "Export", "Mengunduh project ZIP, XLSX, protocol, prompt AI, dan project state."),
    ]
    for no, title, desc in steps:
        with st.container(border=True):
            st.subheader(f"Langkah {no}. {title}")
            st.write(desc)


def page_title_protocol() -> None:
    st.header("1. Judul, PICOS/PICO/PECO, dan Kelayakan Naskah")
    p = st.session_state.project
    c1, c2, c3 = st.columns(3)
    with c1:
        p["domain"] = st.selectbox("Bidang", list(DOMAIN_PROFILES.keys()), index=list(DOMAIN_PROFILES.keys()).index(p.get("domain", "Teknik Pertanian dan Biosistem")))
    with c2:
        p["framework"] = st.selectbox("Framework", ["PICOS", "PICO", "PECO"], index=["PICOS", "PICO", "PECO"].index(p.get("framework", "PICOS")))
    with c3:
        p["target_quartile"] = st.selectbox("Target jurnal", ["Q1", "Q2", "Q3", "Q4", "Nasional/Sinta"], index=["Q1", "Q2", "Q3", "Q4", "Nasional/Sinta"].index(p.get("target_quartile", "Q2")))

    if st.button("Isi contoh sesuai bidang & framework", use_container_width=True):
        ex = EXAMPLES.get((p["domain"], p["framework"])) or EXAMPLES.get((p["domain"], "PICOS")) or next(iter(EXAMPLES.values()))
        p.update(ex)
        p["research_question"] = generate_research_question(p)
        st.rerun()

    p["title"] = st.text_area("Judul systematic review", value=p.get("title", ""), height=80)
    c1, c2 = st.columns(2)
    with c1:
        p["population"] = st.text_input("P - Population/Problem", value=p.get("population", ""))
        label_i = "E - Exposure" if p.get("framework") == "PECO" else "I - Intervention"
        p["intervention"] = st.text_input(label_i, value=p.get("intervention", ""))
        p["comparator"] = st.text_input("C - Comparator", value=p.get("comparator", ""))
    with c2:
        p["outcome"] = st.text_input("O - Outcome", value=p.get("outcome", ""))
        p["study_design"] = st.text_input("S - Study Design", value=p.get("study_design", ""), disabled=p.get("framework") != "PICOS")
        if st.button("Generate Research Question", use_container_width=True):
            p["research_question"] = generate_research_question(p)
    p["research_question"] = st.text_area("Research question", value=p.get("research_question") or generate_research_question(p), height=80)

    score, issues = title_score(p.get("title", ""))
    st.metric("Skor kesiapan judul", f"{score}/100")
    if issues:
        st.warning("\n".join([f"- {x}" for x in issues]))
    else:
        st.success("Judul sudah cukup kuat untuk dikembangkan ke protocol systematic review.")

    profile = DOMAIN_PROFILES[p["domain"]]
    with st.expander("Contoh database dan quality tool sesuai bidang", expanded=True):
        st.write("**Database disarankan:** " + ", ".join(profile["databases"]))
        st.write("**Quality tool:** " + profile["quality_tool"])


def page_protocol_search() -> None:
    st.header("2. Protocol & Search Strategy")
    if st.button("Generate / Sinkronkan dari Judul & PICOS/PECO", use_container_width=True):
        inclusion, exclusion, terms = generate_protocol(st.session_state.project)
        st.session_state.criteria = {"inclusion": inclusion, "exclusion": exclusion}
        st.session_state.terms = terms
        st.success("Protocol dan search strategy berhasil diperbarui.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Inclusion Criteria")
        inclusion_text = st.text_area("Satu kriteria per baris", value="\n".join(st.session_state.criteria.get("inclusion", [])), height=220)
        st.session_state.criteria["inclusion"] = [x.strip() for x in inclusion_text.splitlines() if x.strip()]
    with c2:
        st.subheader("Exclusion Criteria")
        exclusion_text = st.text_area("Satu kriteria per baris", value="\n".join(st.session_state.criteria.get("exclusion", [])), height=220)
        st.session_state.criteria["exclusion"] = [x.strip() for x in exclusion_text.splitlines() if x.strip()]

    st.subheader("Search Terms")
    cols = st.columns(5)
    keys = ["population_terms", "intervention_terms", "comparator_terms", "outcome_terms", "study_terms"]
    labels = ["Population", "Intervention/Exposure", "Comparator", "Outcome", "Study"]
    for col, key, label in zip(cols, keys, labels):
        with col:
            st.session_state.terms[key] = st.text_area(label, value=st.session_state.terms.get(key, ""), height=120)
    if st.button("Buat Boolean Search", use_container_width=True):
        st.session_state.terms["boolean_search"] = make_boolean_search(st.session_state.terms)
    st.text_area("Boolean search strategy", value=st.session_state.terms.get("boolean_search", ""), height=120, key="boolean_search_editor")
    st.session_state.terms["boolean_search"] = st.session_state.boolean_search_editor
    st.download_button("Download Protocol Markdown", build_protocol_markdown().encode("utf-8"), "protocol_and_search_strategy.md", "text/markdown", use_container_width=True)


def page_import_screening() -> None:
    st.header("3. Import Artikel & Screening")
    st.caption("Mendukung XLSX, XLS, CSV, dan RIS. Output ekspor utama tetap XLSX.")
    uploaded = st.file_uploader("Upload file artikel", type=["xlsx", "xls", "csv", "ris"])
    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".ris"):
                df = parse_ris(uploaded)
            elif uploaded.name.lower().endswith(".csv"):
                df = normalize_articles(pd.read_csv(uploaded))
            else:
                df = normalize_articles(pd.read_excel(uploaded))
            st.session_state.articles = df
            st.success(f"Berhasil import {len(df)} artikel.")
        except Exception as exc:
            st.error(f"Gagal membaca file: {exc}")

    if len(st.session_state.articles):
        if st.button("Refresh skor relevansi PICOS/PECO", use_container_width=True):
            st.session_state.articles = auto_score_articles(st.session_state.articles)
        edited = st.data_editor(st.session_state.articles, use_container_width=True, num_rows="dynamic", height=430)
        st.session_state.articles = edited
        counts = prisma_counts()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Records", counts["records_identified"])
        c2.metric("Duplikat", counts["duplicates_removed"])
        c3.metric("Screened", counts["records_screened"])
        c4.metric("Include", counts["studies_included"])
        st.download_button("Download screening XLSX", dataframe_to_xlsx_bytes({"articles_screening": st.session_state.articles}), "articles_screening.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        st.info("Belum ada artikel. Pakai template di folder `templates/import_template.xlsx` atau upload file RIS/XLSX dari database.")


def page_prisma_quality() -> None:
    st.header("4. PRISMA & Quality Assessment")
    counts = prisma_counts()
    cols = st.columns(6)
    for col, (k, v) in zip(cols, counts.items()):
        col.metric(k.replace("_", " ").title(), v)

    st.subheader("Quality Assessment / Risk of Bias")
    if st.button("Buat/refresh tabel quality dari artikel Include", use_container_width=True):
        ensure_quality_from_articles()
    if len(st.session_state.quality):
        st.session_state.quality = st.data_editor(st.session_state.quality, use_container_width=True, num_rows="dynamic", height=420)
        st.download_button("Download quality assessment XLSX", dataframe_to_xlsx_bytes({"quality_assessment": st.session_state.quality}), "quality_assessment.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        st.info("Klik tombol refresh setelah artikel Include tersedia.")


def page_extraction() -> None:
    st.header("5. Data Extraction & Evidence Matrix")
    if st.button("Buat/refresh tabel ekstraksi dari artikel Include", use_container_width=True):
        ensure_extraction_from_articles()
    if len(st.session_state.extraction):
        st.session_state.extraction = st.data_editor(st.session_state.extraction, use_container_width=True, num_rows="dynamic", height=480)
        st.download_button("Download data extraction XLSX", dataframe_to_xlsx_bytes({"data_extraction": st.session_state.extraction}), "data_extraction.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        st.info("Belum ada data ekstraksi. Pastikan artikel Include sudah tersedia.")
    st.session_state.notes = st.text_area("Catatan sintesis / insight manual", value=st.session_state.notes, height=160)


def page_ai_insight() -> None:
    st.header("6. AI Insight")
    st.info("AI sudah include di sistem. API dibaca otomatis dari `.streamlit/secrets.toml` atau Secrets Streamlit Cloud. Tanpa API, prompt tetap bisa diunduh dan ditempel ke ChatGPT Web.")
    task = st.selectbox("Jenis insight", ["Novelty & Gap Insight", "Discussion Draft", "Reviewer Simulation", "Manuscript Improvement Plan", "Meta-analysis Advice"])
    prompt = make_ai_prompt(task)
    st.text_area("Prompt siap copy", value=prompt, height=300)
    st.download_button("Download prompt AI", prompt.encode("utf-8"), f"prompt_{task.lower().replace(' ', '_')}.txt", "text/plain", use_container_width=True)
    if st.button("Buat AI Insight Online", use_container_width=True):
        with st.spinner("Memanggil API dari TOML/secrets..."):
            ok, result = call_ai(prompt)
        if ok:
            st.session_state.ai_outputs[task] = result
            st.success("AI insight berhasil dibuat.")
        else:
            st.error(result)
    if st.session_state.ai_outputs:
        st.subheader("Hasil AI Insight")
        for name, text in st.session_state.ai_outputs.items():
            with st.expander(name, expanded=name == task):
                st.markdown(text)
                st.download_button(f"Download {name}.md", text.encode("utf-8"), f"ai_{name.lower().replace(' ', '_')}.md", "text/markdown", use_container_width=True)


def page_export() -> None:
    st.header("7. Export Project")
    st.write("Unduh seluruh hasil review dalam satu paket ZIP.")
    st.download_button("Download Project ZIP", make_project_zip(), "systematic_review_project_export.zip", "application/zip", use_container_width=True)
    st.download_button("Download Project State JSON", json.dumps(project_context(), ensure_ascii=False, indent=2, default=str).encode("utf-8"), "project_state.json", "application/json", use_container_width=True)
    st.download_button("Download Semua Tabel XLSX", dataframe_to_xlsx_bytes({
        "articles_screening": st.session_state.articles,
        "quality_assessment": st.session_state.quality,
        "data_extraction": st.session_state.extraction,
        "prisma_counts": pd.DataFrame([prisma_counts()]),
    }), "systematic_review_tables.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


def page_reset() -> None:
    st.header("⚠️ Reset Data Project")
    st.warning("Tindakan ini menghapus data sementara di session: judul, protocol, artikel, screening, PRISMA, quality, extraction, catatan, dan hasil AI.")
    confirm = st.checkbox("Saya paham data sementara akan dihapus.")
    text = st.text_input("Ketik RESET")
    if st.button("Hapus data dan kembali ke awal", disabled=not (confirm and text.strip().upper() == "RESET"), use_container_width=True):
        reset_project()
        st.success("Data project sudah direset.")
        st.rerun()


def main() -> None:
    init_state()
    page = render_sidebar()
    if page == "Panduan Workflow":
        page_workflow()
    elif page == "1. Judul & PICOS/PECO":
        page_title_protocol()
    elif page == "2. Protocol & Search":
        page_protocol_search()
    elif page == "3. Import & Screening":
        page_import_screening()
    elif page == "4. PRISMA & Quality":
        page_prisma_quality()
    elif page == "5. Data Extraction":
        page_extraction()
    elif page == "6. AI Insight":
        page_ai_insight()
    elif page == "7. Export":
        page_export()
    elif page == "⚠️ Reset":
        page_reset()


if __name__ == "__main__":
    main()
