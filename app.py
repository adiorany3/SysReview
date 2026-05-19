import json
import re
import zipfile
from datetime import date
from io import BytesIO

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Agro Systematic Review Builder",
    page_icon="🌾",
    layout="wide",
)

APP_TITLE = "Agro Systematic Review Builder"
APP_VERSION = "Final Integrated Insight Edition"

ARTICLE_COLUMNS = [
    "id", "title", "authors", "year", "journal", "doi", "country", "study_design",
    "species_or_crop", "intervention", "comparator", "outcome", "abstract", "source_database",
    "duplicate", "picos_relevance_score", "auto_screening_suggestion", "screening_decision",
    "exclusion_reason", "full_text_decision", "full_text_exclusion_reason", "notes"
]

QUALITY_COLUMNS = [
    "id", "title", "clear_objective", "appropriate_design", "adequate_sample",
    "clear_intervention", "valid_outcome", "adequate_statistics", "bias_control",
    "complete_reporting", "quality_score", "quality_category", "risk_of_bias_note"
]

EXTRACTION_COLUMNS = [
    "id", "title", "species_or_crop", "intervention", "comparator", "sample_size",
    "duration", "main_outcome", "effect_direction", "effect_size", "p_value",
    "key_finding", "limitations", "implication"
]

DOMAIN_PROFILES = {
    "Peternakan": {
        "objects": ["broiler", "poultry", "chicken", "layer", "ruminant", "cattle", "goat", "sheep", "duck"],
        "interventions": ["probiotic", "prebiotic", "synbiotic", "feed additive", "herbal", "black soldier fly", "bsf", "insect meal", "protein source"],
        "outcomes": ["feed conversion", "fcr", "body weight", "growth", "mortality", "egg production", "milk yield", "disease incidence", "methane"],
        "databases": ["Scopus", "Web of Science", "CAB Abstracts", "ScienceDirect", "PubMed", "SpringerLink", "Wiley"],
        "quality_tool": "SYRCLE risk of bias untuk animal experiment, JBI checklist untuk studi observasional, dan checklist modifikasi untuk feeding/field trial."
    },
    "Agro/Agronomi": {
        "objects": ["maize", "corn", "rice", "paddy", "soil", "crop", "wheat", "soybean", "horticulture", "plant"],
        "interventions": ["biochar", "organic fertilizer", "compost", "manure", "irrigation", "mulch", "drought", "precision agriculture"],
        "outcomes": ["yield", "productivity", "soil organic carbon", "nitrogen", "nutrient uptake", "water use efficiency", "biomass"],
        "databases": ["Scopus", "Web of Science", "AGRICOLA", "CAB Abstracts", "ScienceDirect", "SpringerLink", "Taylor & Francis"],
        "quality_tool": "ROSES/CEE critical appraisal, JBI adapted checklist, atau checklist eksperimen lapang/greenhouse."
    },
    "Perikanan/Akuakultur": {
        "objects": ["fish", "shrimp", "tilapia", "catfish", "aquaculture", "feed", "pond", "larvae"],
        "interventions": ["probiotic", "prebiotic", "feed additive", "biofloc", "herbal", "alternative protein", "water quality"],
        "outcomes": ["growth", "survival", "feed conversion", "water quality", "immune response", "disease resistance"],
        "databases": ["Scopus", "Web of Science", "ScienceDirect", "Aquatic Sciences and Fisheries Abstracts", "CAB Abstracts", "SpringerLink"],
        "quality_tool": "SYRCLE/JBI adapted checklist untuk eksperimen akuakultur dan checklist reporting trial."
    },
    "Pangan": {
        "objects": ["food", "meat", "milk", "egg", "grain", "rice", "vegetable", "fruit", "processed food"],
        "interventions": ["processing", "fermentation", "packaging", "storage", "preservation", "drying", "edible coating"],
        "outcomes": ["quality", "shelf life", "nutrition", "sensory", "antioxidant", "microbial", "safety"],
        "databases": ["Scopus", "Web of Science", "ScienceDirect", "PubMed", "Wiley", "SpringerLink", "Taylor & Francis"],
        "quality_tool": "JBI checklist, ROBINS-I untuk non-randomized studies, atau checklist metodologi pangan sesuai desain penelitian."
    },
    "Lingkungan": {
        "objects": ["ecosystem", "soil", "water", "biodiversity", "land use", "climate", "agroecosystem"],
        "interventions": ["conservation", "restoration", "management", "mitigation", "adaptation", "biochar", "agroforestry"],
        "outcomes": ["emission", "carbon", "biodiversity", "water quality", "soil health", "resilience", "sustainability"],
        "databases": ["Scopus", "Web of Science", "Environmental Evidence", "ScienceDirect", "SpringerLink", "Taylor & Francis"],
        "quality_tool": "ROSES dan Collaboration for Environmental Evidence/CEE critical appraisal."
    },
}

GENERIC_TERMS = ["review", "study", "analysis", "effect", "impact", "influence", "pengaruh", "analisis", "kajian", "systematic"]


def init_state():
    defaults = {
        "project": {
            "title": "Effects of Probiotic Supplementation on Growth Performance in Broiler Chickens: A Systematic Review and Meta-Analysis",
            "domain": "Peternakan",
            "framework": "PICOS",
            "target_level": "Q1/Q2",
            "review_type": "Systematic Review and Meta-Analysis",
            "research_question": "How does probiotic supplementation affect growth performance, feed conversion ratio, and mortality in broiler chickens compared with non-supplemented diets?",
            "population": "broiler chickens",
            "intervention": "probiotic supplementation",
            "comparator": "control diet or non-supplemented diet",
            "outcome": "growth performance; feed conversion ratio; body weight gain; mortality",
            "study_design": "experimental studies or feeding trials",
            "year_range": "2015-2026",
            "language": "English and Bahasa Indonesia",
            "geographical_scope": "Global",
            "date_started": str(date.today()),
        },
        "criteria": {
            "inclusion": "Peer-reviewed empirical studies; relevant to the PICOS/PECO framework; reporting at least one predefined outcome; full text available; published within the selected year range.",
            "exclusion": "Narrative reviews, editorials, duplicated records, irrelevant population/intervention/outcome, incomplete outcome data, inaccessible full text, and studies outside the predefined scope.",
        },
        "terms": {
            "population_terms": "broiler chicken\npoultry\nGallus gallus",
            "intervention_terms": "probiotic\nprebiotic\nsynbiotic",
            "comparator_terms": "control diet\nbasal diet\nnon-supplemented diet",
            "outcome_terms": "growth performance\nfeed conversion ratio\nFCR\nbody weight gain\nmortality",
            "study_terms": "experimental study\nfeeding trial\ncontrolled trial",
        },
        "articles": pd.DataFrame(columns=ARTICLE_COLUMNS),
        "quality": pd.DataFrame(columns=QUALITY_COLUMNS),
        "extraction": pd.DataFrame(columns=EXTRACTION_COLUMNS),
        "prisma_manual": {
            "records_database": 0,
            "records_other": 0,
            "duplicates_removed": 0,
            "records_screened": 0,
            "records_excluded_title_abs": 0,
            "full_text_assessed": 0,
            "full_text_excluded": 0,
            "studies_included": 0,
        },
        "notes": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def tokenize(text: str):
    return set(re.findall(r"[a-zA-Z0-9]+", str(text).lower()))


def split_terms(text: str):
    return [t.strip() for t in str(text).splitlines() if t.strip()]


def boolean_group(text: str) -> str:
    terms = split_terms(text)
    out = []
    for term in terms:
        term = term.strip()
        if not term:
            continue
        if " " in term and not (term.startswith('"') and term.endswith('"')):
            out.append(f'"{term}"')
        else:
            out.append(term)
    return "(" + " OR ".join(out) + ")" if out else ""


def build_search_string(terms: dict) -> str:
    groups = [
        boolean_group(terms.get("population_terms", "")),
        boolean_group(terms.get("intervention_terms", "")),
        boolean_group(terms.get("comparator_terms", "")),
        boolean_group(terms.get("outcome_terms", "")),
        boolean_group(terms.get("study_terms", "")),
    ]
    return "\nAND\n".join([g for g in groups if g])


def infer_domain(project: dict):
    selected = project.get("domain", "Peternakan")
    if selected and selected != "Otomatis":
        return selected
    text = " ".join([project.get(k, "") for k in ["title", "population", "intervention", "outcome"]]).lower()
    scores = {}
    for domain, profile in DOMAIN_PROFILES.items():
        keywords = profile["objects"] + profile["interventions"] + profile["outcomes"]
        scores[domain] = sum(1 for kw in keywords if kw.lower() in text)
    return max(scores, key=scores.get) if scores else "Peternakan"


def suggest_terms_from_project(project: dict):
    domain = infer_domain(project)
    profile = DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["Peternakan"])
    pop = split_semicolon(project.get("population", "")) or profile["objects"][:3]
    inter = split_semicolon(project.get("intervention", "")) or profile["interventions"][:3]
    comp = split_semicolon(project.get("comparator", "")) or ["control", "conventional practice", "no treatment"]
    out = split_semicolon(project.get("outcome", "")) or profile["outcomes"][:4]
    studies = split_semicolon(project.get("study_design", "")) or ["experimental study", "field trial", "controlled trial"]
    return {
        "population_terms": "\n".join(unique_keep_order(pop + profile["objects"][:3])),
        "intervention_terms": "\n".join(unique_keep_order(inter + profile["interventions"][:3])),
        "comparator_terms": "\n".join(unique_keep_order(comp)),
        "outcome_terms": "\n".join(unique_keep_order(out + profile["outcomes"][:4])),
        "study_terms": "\n".join(unique_keep_order(studies)),
    }


def split_semicolon(text: str):
    parts = re.split(r";|,|\n|/", str(text))
    return [p.strip() for p in parts if p.strip()]


def unique_keep_order(items):
    seen = set()
    result = []
    for item in items:
        k = str(item).lower().strip()
        if k and k not in seen:
            seen.add(k)
            result.append(str(item).strip())
    return result


def analyze_title(project: dict):
    title = str(project.get("title", "")).strip()
    domain = infer_domain(project)
    text = " ".join([title, project.get("population", ""), project.get("intervention", ""), project.get("outcome", ""), project.get("comparator", "")]).lower()
    profile = DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["Peternakan"])

    has_review_label = bool(re.search(r"systematic review|meta-analysis|meta analysis|systematic map|scoping review", title, re.I))
    has_population = bool(project.get("population", "").strip()) or any(k in text for k in profile["objects"])
    has_intervention = bool(project.get("intervention", "").strip()) or any(k in text for k in profile["interventions"])
    has_comparator = bool(project.get("comparator", "").strip()) or bool(re.search(r"control|compared|versus|vs\.?|without|conventional|non", text, re.I))
    has_outcome = bool(project.get("outcome", "").strip()) or any(k in text for k in profile["outcomes"])
    has_study = bool(project.get("study_design", "").strip()) or has_review_label
    title_len = len(title.split())
    good_length = 8 <= title_len <= 28
    global_scope = project.get("geographical_scope", "Global") in ["Global", "International", "Internasional"] or "indonesia" not in text
    measurable = has_outcome and any(k in text for k in profile["outcomes"] + ["yield", "fcr", "mortality", "carbon", "growth", "quality"])

    sub = {
        "Kejelasan topik": 15 if has_population and has_intervention else 8 if has_population or has_intervention else 3,
        "Kelengkapan PICOS/PECO": 7 * sum([has_population, has_intervention, has_comparator, has_outcome, has_study]),
        "Outcome terukur": 15 if measurable else 9 if has_outcome else 3,
        "Kelayakan meta-analysis": 12 if has_comparator and measurable else 7 if has_outcome else 2,
        "Relevansi global": 10 if global_scope else 5,
        "Kerapian judul": 8 if has_review_label and good_length else 5 if good_length else 3,
        "Kesesuaian bidang": 5 if domain in DOMAIN_PROFILES else 2,
    }
    score = min(100, int(sum(sub.values())))

    weaknesses = []
    if not title:
        weaknesses.append("Judul belum diisi.")
    if not has_review_label:
        weaknesses.append("Judul belum menyebut jenis naskah seperti Systematic Review atau Systematic Review and Meta-Analysis.")
    if not has_population:
        weaknesses.append("Population/problem belum jelas. Tambahkan spesies, komoditas, tanah, crop, atau sistem produksi.")
    if not has_intervention:
        weaknesses.append("Intervention/exposure belum jelas. Tambahkan perlakuan, teknologi, pakan, pupuk, atau strategi manajemen.")
    if not has_comparator:
        weaknesses.append("Comparator belum eksplisit. Tambahkan control, conventional practice, no treatment, atau non-supplemented group.")
    if not has_outcome:
        weaknesses.append("Outcome belum kuat. Tambahkan variabel hasil seperti FCR, body weight gain, yield, soil organic carbon, survival, atau quality attributes.")
    if title_len < 8:
        weaknesses.append("Judul terlalu pendek untuk target jurnal bereputasi.")
    if title_len > 28:
        weaknesses.append("Judul terlalu panjang. Padatkan tanpa menghilangkan PICOS/PECO.")
    if not global_scope:
        weaknesses.append("Cakupan terlalu lokal; jelaskan kontribusi internasional atau perluas scope.")

    strengths = []
    if has_population:
        strengths.append("Objek/populasi sudah terbaca.")
    if has_intervention:
        strengths.append("Intervensi/eksposur sudah spesifik.")
    if has_outcome:
        strengths.append("Outcome sudah dapat dijadikan dasar sintesis bukti.")
    if has_review_label:
        strengths.append("Jenis naskah review sudah tercermin di judul.")
    if measurable and has_comparator:
        strengths.append("Ada peluang meta-analysis apabila data numerik studi cukup homogen.")

    readiness = "Belum siap"
    if score >= 80:
        readiness = "Siap dikembangkan untuk target Q-level, dengan catatan metode harus transparan."
    elif score >= 60:
        readiness = "Cukup siap, tetapi masih perlu penguatan PICOS, search strategy, dan quality assessment."
    elif score >= 40:
        readiness = "Perlu revisi besar sebelum layak menjadi systematic review."

    pop = project.get("population", "target population/commodity") or "target population/commodity"
    inter = project.get("intervention", "intervention/exposure") or "intervention/exposure"
    comp = project.get("comparator", "control or conventional practice") or "control or conventional practice"
    out = project.get("outcome", "main outcomes") or "main outcomes"

    suggested_titles = [
        f"Effects of {inter.title()} on {out.title()} in {pop.title()}: A Systematic Review",
        f"{inter.title()} Compared with {comp.title()} for Improving {out.title()} in {pop.title()}: A Systematic Review and Meta-Analysis",
        f"Evidence on {inter.title()} for {pop.title()}: A Systematic Review of {out.title()}",
    ]

    research_questions = [
        f"How does {inter} affect {out} in {pop} compared with {comp}?",
        f"What factors explain variation in the effects of {inter} on {out} across studies involving {pop}?",
        f"What is the quality and strength of evidence supporting {inter} for {pop}?",
    ]

    return {
        "score": score,
        "readiness": readiness,
        "domain": domain,
        "sub_scores": sub,
        "strengths": strengths or ["Belum ada kekuatan utama yang terdeteksi. Lengkapi judul dan PICOS/PECO."],
        "weaknesses": weaknesses or ["Tidak ada kelemahan besar yang terdeteksi secara otomatis."],
        "suggested_titles": suggested_titles,
        "research_questions": research_questions,
        "recommended_databases": profile["databases"],
        "quality_tool": profile["quality_tool"],
    }


def normalize_columns(df: pd.DataFrame):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    aliases = {
        "article_title": "title",
        "document_title": "title",
        "source_title": "journal",
        "publication_title": "journal",
        "publication_year": "year",
        "abstract_note": "abstract",
        "database": "source_database",
        "study_type": "study_design",
        "crop": "species_or_crop",
        "species": "species_or_crop",
        "commodity": "species_or_crop",
    }
    df = df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})
    for col in ARTICLE_COLUMNS:
        if col not in df.columns:
            if col == "duplicate":
                df[col] = False
            elif col in ["picos_relevance_score"]:
                df[col] = 0
            elif col in ["auto_screening_suggestion", "screening_decision", "full_text_decision"]:
                df[col] = "Belum dinilai"
            else:
                df[col] = ""
    if df["id"].astype(str).str.strip().eq("").all():
        df["id"] = [f"A{i+1:03d}" for i in range(len(df))]
    df["id"] = df["id"].astype(str)
    return df[ARTICLE_COLUMNS]


def parse_ris(text: str):
    records, current, authors = [], {}, []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("TY  -"):
            current, authors = {}, []
        elif line.startswith("ER  -"):
            current["authors"] = "; ".join(authors)
            records.append(current)
        elif len(line) >= 6 and line[2:6] == "  - ":
            tag, val = line[:2], line[6:].strip()
            if tag in ["TI", "T1"]:
                current["title"] = val
            elif tag == "AU":
                authors.append(val)
            elif tag == "PY":
                current["year"] = val[:4]
            elif tag in ["JO", "JF", "T2"]:
                current["journal"] = val
            elif tag == "DO":
                current["doi"] = val
            elif tag in ["AB", "N2"]:
                current["abstract"] = val
    return pd.DataFrame(records)


def read_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    if name.endswith(".ris"):
        return parse_ris(uploaded_file.getvalue().decode("utf-8", errors="ignore"))
    raise ValueError("Format belum didukung. Gunakan CSV, XLSX, atau RIS.")


def flag_duplicates(df: pd.DataFrame):
    if df.empty:
        return df
    df = df.copy()
    title_key = df["title"].astype(str).str.lower().str.replace(r"\W+", " ", regex=True).str.strip()
    doi_key = df["doi"].astype(str).str.lower().str.strip()
    df["duplicate"] = (title_key.duplicated(keep="first") & title_key.ne("")) | (doi_key.duplicated(keep="first") & doi_key.ne(""))
    return df


def score_article_relevance(row: pd.Series, terms: dict):
    text = " ".join([str(row.get("title", "")), str(row.get("abstract", "")), str(row.get("species_or_crop", "")), str(row.get("intervention", "")), str(row.get("outcome", ""))]).lower()
    score = 0
    weights = {
        "population_terms": 25,
        "intervention_terms": 30,
        "comparator_terms": 10,
        "outcome_terms": 25,
        "study_terms": 10,
    }
    for key, weight in weights.items():
        terms_list = split_terms(terms.get(key, ""))
        if not terms_list:
            continue
        hits = sum(1 for term in terms_list if term.lower().replace('"', '') in text)
        score += min(weight, int(weight * hits / max(1, min(3, len(terms_list)))))
    return min(100, score)


def apply_relevance_scoring(df: pd.DataFrame):
    if df.empty:
        return df
    df = df.copy()
    terms = st.session_state.terms
    df["picos_relevance_score"] = df.apply(lambda r: score_article_relevance(r, terms), axis=1)
    suggestions = []
    for _, row in df.iterrows():
        if bool(row.get("duplicate", False)):
            suggestions.append("Exclude - Duplikat")
        elif row.get("picos_relevance_score", 0) >= 70:
            suggestions.append("Include")
        elif row.get("picos_relevance_score", 0) >= 40:
            suggestions.append("Maybe")
        else:
            suggestions.append("Exclude - Relevansi rendah")
    df["auto_screening_suggestion"] = suggestions
    return df


def get_prisma_counts(auto=True):
    if not auto:
        return st.session_state.prisma_manual
    a = st.session_state.articles
    counts = {k: 0 for k in st.session_state.prisma_manual}
    if a.empty:
        return counts
    counts["records_database"] = len(a)
    counts["records_other"] = 0
    counts["duplicates_removed"] = int(a["duplicate"].fillna(False).astype(bool).sum())
    nondup = a[~a["duplicate"].fillna(False).astype(bool)]
    counts["records_screened"] = len(nondup)
    counts["records_excluded_title_abs"] = int((nondup["screening_decision"] == "Exclude").sum())
    full_pool = nondup[nondup["screening_decision"].isin(["Include", "Maybe"])]
    counts["full_text_assessed"] = len(full_pool)
    counts["full_text_excluded"] = int((full_pool["full_text_decision"] == "Exclude").sum())
    counts["studies_included"] = int((full_pool["full_text_decision"] == "Include").sum())
    return counts


def sync_quality_extraction():
    a = st.session_state.articles
    if a.empty:
        return
    include = a[(a["full_text_decision"].eq("Include")) | ((a["full_text_decision"].eq("Belum dinilai")) & a["screening_decision"].eq("Include"))]
    q = st.session_state.quality.copy()
    e = st.session_state.extraction.copy()

    for _, row in include.iterrows():
        aid = str(row.get("id", ""))
        if aid and (q.empty or aid not in q["id"].astype(str).values):
            newq = {c: "" for c in QUALITY_COLUMNS}
            for c in ["clear_objective", "appropriate_design", "adequate_sample", "clear_intervention", "valid_outcome", "adequate_statistics", "bias_control", "complete_reporting"]:
                newq[c] = False
            newq.update({"id": aid, "title": row.get("title", ""), "quality_score": 0, "quality_category": "Belum dinilai"})
            q = pd.concat([q, pd.DataFrame([newq])], ignore_index=True)
        if aid and (e.empty or aid not in e["id"].astype(str).values):
            newe = {c: "" for c in EXTRACTION_COLUMNS}
            newe.update({
                "id": aid, "title": row.get("title", ""), "species_or_crop": row.get("species_or_crop", ""),
                "intervention": row.get("intervention", ""), "comparator": row.get("comparator", ""),
                "main_outcome": row.get("outcome", ""),
            })
            e = pd.concat([e, pd.DataFrame([newe])], ignore_index=True)

    valid_ids = set(include["id"].astype(str))
    if not q.empty:
        q = q[q["id"].astype(str).isin(valid_ids)].reset_index(drop=True)
    if not e.empty:
        e = e[e["id"].astype(str).isin(valid_ids)].reset_index(drop=True)
    st.session_state.quality = calculate_quality(q[QUALITY_COLUMNS])
    st.session_state.extraction = e[EXTRACTION_COLUMNS]


def calculate_quality(df: pd.DataFrame):
    if df.empty:
        return df
    df = df.copy()
    bool_cols = ["clear_objective", "appropriate_design", "adequate_sample", "clear_intervention", "valid_outcome", "adequate_statistics", "bias_control", "complete_reporting"]
    for c in bool_cols:
        df[c] = df.get(c, False).fillna(False).astype(bool)
    df["quality_score"] = df[bool_cols].sum(axis=1)
    df["quality_category"] = pd.cut(df["quality_score"], bins=[-1, 3, 5, 8], labels=["Low", "Moderate", "High"]).astype(str)
    return df


def completion_status():
    p = st.session_state.project
    a, q, e = st.session_state.articles, st.session_state.quality, st.session_state.extraction
    checks = {
        "Judul & PICOS lengkap": all(str(p.get(k, "")).strip() for k in ["title", "population", "intervention", "outcome"]),
        "Search strategy tersedia": bool(build_search_string(st.session_state.terms).strip()),
        "Artikel sudah diimpor": not a.empty,
        "Screening judul/abstrak berjalan": not a.empty and (a["screening_decision"] != "Belum dinilai").any(),
        "Full-text decision diisi": not a.empty and (a["full_text_decision"] != "Belum dinilai").any(),
        "Quality assessment tersedia": not q.empty and (q["quality_category"] != "Belum dinilai").any(),
        "Data extraction tersedia": not e.empty and e["key_finding"].astype(str).str.strip().ne("").any(),
        "Insight & export siap": not a.empty,
    }
    pct = int(100 * sum(checks.values()) / len(checks))
    return checks, pct


def infer_evidence_strength():
    a, q, e = st.session_state.articles, st.session_state.quality, st.session_state.extraction
    counts = get_prisma_counts(True)
    included = counts["studies_included"]
    if q.empty:
        avg_q = 0
        high_share = 0
    else:
        avg_q = float(pd.to_numeric(q["quality_score"], errors="coerce").fillna(0).mean())
        high_share = float((q["quality_category"] == "High").mean()) if len(q) else 0
    if e.empty or "effect_direction" not in e:
        consistency = 0
        dominant = "Belum tersedia"
    else:
        effects = e["effect_direction"].replace("", np.nan).dropna()
        if effects.empty:
            consistency = 0
            dominant = "Belum tersedia"
        else:
            dominant = effects.value_counts().idxmax()
            consistency = float(effects.value_counts().max() / len(effects))
    numeric_effects = 0
    if not e.empty:
        numeric_effects = int(pd.to_numeric(e["effect_size"], errors="coerce").notna().sum())
    if included >= 10 and avg_q >= 6 and consistency >= 0.7:
        strength = "Kuat"
    elif included >= 5 and avg_q >= 4 and consistency >= 0.5:
        strength = "Sedang"
    elif included > 0:
        strength = "Terbatas"
    else:
        strength = "Belum dapat dinilai"
    meta_ready = included >= 5 and numeric_effects >= 3 and consistency >= 0.4
    return {
        "included": included,
        "avg_quality": avg_q,
        "high_quality_share": high_share,
        "dominant_effect": dominant,
        "effect_consistency": consistency,
        "numeric_effects": numeric_effects,
        "strength": strength,
        "meta_ready": meta_ready,
    }


def build_insight_report():
    p = st.session_state.project
    title_result = analyze_title(p)
    a, q, e = st.session_state.articles, st.session_state.quality, st.session_state.extraction
    counts = get_prisma_counts(True)
    evidence = infer_evidence_strength()

    lines = []
    lines.append("# Evidence Insight Report")
    lines.append(f"\n## 1. Ringkasan proyek\nJudul sementara: **{p.get('title', '')}**. Domain terdeteksi: **{title_result['domain']}**. Skor kesiapan judul dan protocol adalah **{title_result['score']}/100**, dengan status: **{title_result['readiness']}**")
    lines.append("\n## 2. Insight kelayakan judul")
    lines.append("Kekuatan utama: " + "; ".join(title_result["strengths"]))
    lines.append("Kelemahan/perbaikan: " + "; ".join(title_result["weaknesses"]))
    lines.append("\n## 3. Insight screening dan PRISMA")
    if a.empty:
        lines.append("Belum ada artikel yang diimpor, sehingga insight screening belum dapat dihitung.")
    else:
        dup = counts["duplicates_removed"]
        excluded = counts["records_excluded_title_abs"]
        included = counts["studies_included"]
        lines.append(f"Sistem mendeteksi **{len(a)}** record awal, **{dup}** duplikasi, **{excluded}** record tereksklusi pada screening judul/abstrak, dan **{included}** studi include final.")
        if dup / max(1, len(a)) > 0.2:
            lines.append("Proporsi duplikasi cukup tinggi. Pastikan ekspor dari database tidak saling tumpang tindih atau lakukan deduplikasi DOI/title secara lebih ketat.")
        if included < 5 and len(a) > 0:
            lines.append("Jumlah studi include final masih rendah. Pertimbangkan memperluas sinonim kata kunci, database, atau rentang tahun selama tetap sesuai PICOS/PECO.")
    lines.append("\n## 4. Insight kualitas bukti")
    lines.append(f"Kekuatan bukti sementara: **{evidence['strength']}**. Rata-rata skor kualitas: **{evidence['avg_quality']:.2f}/8**. Proporsi studi berkualitas tinggi: **{evidence['high_quality_share']*100:.1f}%**.")
    if evidence["strength"] in ["Terbatas", "Belum dapat dinilai"]:
        lines.append("Kualitas bukti masih perlu diperkuat dengan penilaian risiko bias yang lebih detail, pencatatan desain studi, ukuran sampel, validitas outcome, dan kecukupan statistik.")
    lines.append("\n## 5. Insight hasil dan arah efek")
    lines.append(f"Arah efek dominan: **{evidence['dominant_effect']}** dengan konsistensi **{evidence['effect_consistency']*100:.1f}%** dari data extraction yang telah diisi.")
    if not e.empty:
        dominant_intervention = e["intervention"].replace("", np.nan).dropna().value_counts()
        dominant_outcome = e["main_outcome"].replace("", np.nan).dropna().value_counts()
        if not dominant_intervention.empty:
            lines.append(f"Intervensi yang paling sering muncul adalah **{dominant_intervention.index[0]}**.")
        if not dominant_outcome.empty:
            lines.append(f"Outcome yang paling banyak dilaporkan adalah **{dominant_outcome.index[0]}**.")
    lines.append("\n## 6. Kesiapan meta-analysis")
    if evidence["meta_ready"]:
        lines.append("Data sementara menunjukkan **berpotensi untuk meta-analysis**, karena jumlah studi include dan effect size numerik mulai mencukupi. Pastikan satuan outcome, desain studi, dan model statistik homogen.")
    else:
        lines.append("Saat ini naskah lebih aman diarahkan ke **narrative synthesis/systematic review**. Meta-analysis belum disarankan sebelum effect size, satuan outcome, dan ukuran varians lebih lengkap.")
    lines.append("\n## 7. Gap riset otomatis")
    gaps = generate_gaps()
    for i, gap in enumerate(gaps, 1):
        lines.append(f"{i}. {gap}")
    lines.append("\n## 8. Rekomendasi tindak lanjut")
    recs = generate_recommendations()
    for i, rec in enumerate(recs, 1):
        lines.append(f"{i}. {rec}")
    return "\n".join(lines)


def generate_gaps():
    a, q, e = st.session_state.articles, st.session_state.quality, st.session_state.extraction
    gaps = []
    if a.empty:
        return ["Belum ada data artikel; gap riset belum dapat dibaca."]
    if "country" in a and a["country"].replace("", np.nan).dropna().nunique() <= 2:
        gaps.append("Sebaran negara/lokasi penelitian masih sempit, sehingga generalisasi global perlu dijelaskan dengan hati-hati.")
    years = pd.to_numeric(a.get("year", pd.Series(dtype=str)), errors="coerce").dropna()
    if not years.empty and years.max() < 2022:
        gaps.append("Artikel terbaru belum banyak tercakup. Perlu memperbarui pencarian agar bukti lebih mutakhir.")
    if not q.empty and (q["quality_category"] == "Low").mean() > 0.3:
        gaps.append("Sebagian studi memiliki kualitas rendah, sehingga gap metodologis perlu dibahas dalam diskusi.")
    if not e.empty:
        effects = e["effect_direction"].replace("", np.nan).dropna()
        if not effects.empty and effects.nunique() > 2:
            gaps.append("Arah efek bervariasi antarstudi; faktor dosis, durasi, spesies/komoditas, dan kondisi lingkungan perlu dianalisis sebagai sumber heterogenitas.")
        if pd.to_numeric(e["effect_size"], errors="coerce").notna().sum() < 3:
            gaps.append("Effect size numerik masih minim, sehingga meta-analysis belum kuat dan pelaporan kuantitatif perlu dilengkapi.")
    if not gaps:
        gaps.append("Gap utama kemungkinan berada pada heterogenitas desain studi, variasi outcome, dan kebutuhan standardisasi pelaporan data.")
    return gaps


def generate_recommendations():
    p = st.session_state.project
    a, q, e = st.session_state.articles, st.session_state.quality, st.session_state.extraction
    evidence = infer_evidence_strength()
    recs = []
    title_result = analyze_title(p)
    if title_result["score"] < 80:
        recs.append("Perbaiki judul dengan memasukkan population, intervention/exposure, comparator, outcome, dan jenis review secara eksplisit.")
    if a.empty:
        recs.append("Impor hasil pencarian dari minimal 2-3 database utama agar screening dan PRISMA dapat berjalan.")
    else:
        if a["source_database"].replace("", np.nan).dropna().nunique() < 2:
            recs.append("Tambahkan database pencarian lain agar cakupan bukti tidak terlalu sempit.")
        if get_prisma_counts(True)["studies_included"] < 5:
            recs.append("Review search string dan kriteria inklusi agar jumlah studi include final cukup untuk sintesis yang kuat.")
    if not q.empty and evidence["avg_quality"] < 5:
        recs.append("Perkuat quality assessment dengan alat yang sesuai desain studi dan gunakan hasilnya dalam pembahasan risiko bias.")
    if not e.empty and not evidence["meta_ready"]:
        recs.append("Lengkapi effect size, standard deviation/standard error, sample size, dan satuan outcome apabila ingin melanjutkan ke meta-analysis.")
    recs.append("Gunakan Insight Report sebagai dasar menulis bagian Results, Discussion, Limitations, dan Future Research.")
    return unique_keep_order(recs)


def make_protocol_markdown():
    p, c = st.session_state.project, st.session_state.criteria
    return f"""# Protocol Systematic Review

## Judul
{p.get('title','')}

## Bidang dan Target
- Domain: {p.get('domain','')}
- Framework: {p.get('framework','')}
- Target publikasi: {p.get('target_level','')}
- Jenis review: {p.get('review_type','')}
- Rentang tahun: {p.get('year_range','')}
- Bahasa: {p.get('language','')}
- Cakupan geografis: {p.get('geographical_scope','')}

## Pertanyaan Penelitian
{p.get('research_question','')}

## Kerangka {p.get('framework','PICOS')}
- Population/Problem: {p.get('population','')}
- Intervention/Exposure: {p.get('intervention','')}
- Comparator: {p.get('comparator','')}
- Outcome: {p.get('outcome','')}
- Study Design: {p.get('study_design','')}

## Kriteria Inklusi
{c.get('inclusion','')}

## Kriteria Eksklusi
{c.get('exclusion','')}

## Strategi Pencarian
```text
{build_search_string(st.session_state.terms)}
```

## Rencana Screening
Record dari database digabungkan, duplikasi dihapus berdasarkan DOI dan judul, kemudian dilakukan screening judul/abstrak dan full-text. Alasan eksklusi dicatat pada setiap tahap.

## Rencana Quality Assessment
Quality assessment menggunakan checklist yang sesuai desain studi. Komponen minimal meliputi tujuan, desain, sampel, intervensi, outcome, statistik, kontrol bias, dan kelengkapan pelaporan.

## Rencana Sintesis
Sintesis dilakukan secara naratif. Meta-analysis dipertimbangkan apabila outcome, satuan, desain studi, dan effect size cukup homogen.
"""


def make_methods_template():
    p = st.session_state.project
    counts = get_prisma_counts(True)
    return f"""# Draft Methods Section

This systematic review was designed to synthesize empirical evidence addressing the question: {p.get('research_question','')}. The review followed the {p.get('framework','PICOS')} framework. The population/problem was {p.get('population','')}, the intervention/exposure was {p.get('intervention','')}, the comparator was {p.get('comparator','')}, and the main outcomes were {p.get('outcome','')}.

The search strategy was developed using Boolean operators and synonyms for each review component. The final search string was:

```text
{build_search_string(st.session_state.terms)}
```

Records were imported into the screening system. Duplicate records were identified using DOI and normalized title matching. The current PRISMA count identified {counts['records_database']} database records, {counts['duplicates_removed']} duplicates removed, {counts['records_screened']} records screened, {counts['full_text_assessed']} full-text articles assessed, and {counts['studies_included']} studies included in the final synthesis.

Quality assessment was conducted using a structured checklist covering clarity of objective, study design, sample adequacy, intervention reporting, outcome validity, statistical adequacy, bias control, and completeness of reporting. Data extraction included population/commodity, intervention, comparator, sample size, duration, outcome, effect direction, effect size, p-value, key findings, limitations, and implications.
"""


def make_export_zip():
    mem = BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("protocol_systematic_review.md", make_protocol_markdown())
        z.writestr("methods_template.md", make_methods_template())
        z.writestr("evidence_insight_report.md", build_insight_report())
        z.writestr("screening_results.csv", st.session_state.articles.to_csv(index=False))
        z.writestr("quality_assessment.csv", st.session_state.quality.to_csv(index=False))
        z.writestr("data_extraction.csv", st.session_state.extraction.to_csv(index=False))
        z.writestr("project_state.json", json.dumps({
            "project": st.session_state.project,
            "criteria": st.session_state.criteria,
            "terms": st.session_state.terms,
            "notes": st.session_state.notes,
        }, ensure_ascii=False, indent=2))
    mem.seek(0)
    return mem.getvalue()


def download_df_button(label, df, filename):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), filename, "text/csv", use_container_width=True)


def render_sidebar():
    checks, pct = completion_status()
    st.sidebar.title("Workflow")
    st.sidebar.progress(pct / 100)
    st.sidebar.caption(f"Progress: {pct}%")
    for label, ok in checks.items():
        st.sidebar.write(("✅" if ok else "⬜") + " " + label)
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Sinkronkan semua modul", use_container_width=True):
        st.session_state.articles = flag_duplicates(st.session_state.articles)
        st.session_state.articles = apply_relevance_scoring(st.session_state.articles)
        sync_quality_extraction()
        st.sidebar.success("Data sudah disinkronkan.")
    st.sidebar.caption(APP_VERSION)


def page_workflow():
    st.title(f"🌾 {APP_TITLE}")
    st.caption(APP_VERSION)
    st.info("Gunakan halaman ini sebagai peta kerja. Setiap langkah menghasilkan output yang dipakai oleh langkah berikutnya.")

    steps = [
        ("1", "Judul & PICOS/PECO", "Masukkan judul, bidang, target jurnal, dan komponen PICOS/PECO.", "Output: skor kesiapan judul, kelemahan, rekomendasi judul, research question."),
        ("2", "Protocol & Search Strategy", "Rapikan protocol, kriteria inklusi-eksklusi, dan Boolean search.", "Output: protocol awal dan search string yang bisa dipakai di Scopus/WoS/database lain."),
        ("3", "Import Artikel", "Unggah hasil ekspor CSV/XLSX/RIS dari database.", "Output: data artikel yang sudah dinormalisasi dan dideduplikasi."),
        ("4", "Screening", "Gunakan skor relevansi PICOS sebagai bantuan, lalu tetapkan keputusan Include/Maybe/Exclude.", "Output: daftar artikel eligible untuk full-text."),
        ("5", "PRISMA", "Pantau jumlah record dari identifikasi sampai studi include final.", "Output: angka PRISMA untuk naskah."),
        ("6", "Quality Assessment", "Nilai kualitas studi berdasarkan checklist.", "Output: kategori Low/Moderate/High."),
        ("7", "Data Extraction", "Isi outcome, effect direction, effect size, temuan kunci, limitasi, dan implikasi.", "Output: matriks bukti untuk sintesis."),
        ("8", "Insight & Export", "Sistem membaca seluruh hasil dan menyusun insight otomatis.", "Output: Evidence Insight Report, protocol, methods template, dan export ZIP."),
    ]
    for no, title, desc, out in steps:
        with st.container(border=True):
            st.subheader(f"Langkah {no}. {title}")
            st.write(desc)
            st.caption(out)

    st.subheader("Ringkasan cepat proyek")
    p = st.session_state.project
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Skor judul", f"{analyze_title(p)['score']}/100")
    c2.metric("Artikel", len(st.session_state.articles))
    c3.metric("Include final", get_prisma_counts(True)["studies_included"])
    c4.metric("Kekuatan bukti", infer_evidence_strength()["strength"])


def page_title_protocol():
    st.header("1. Judul, PICOS/PECO, dan Kelayakan Naskah")
    p = st.session_state.project.copy()
    with st.form("project_form"):
        p["title"] = st.text_area("Judul sementara", value=p.get("title", ""), height=80)
        c1, c2, c3, c4 = st.columns(4)
        domains = ["Peternakan", "Agro/Agronomi", "Perikanan/Akuakultur", "Pangan", "Lingkungan", "Otomatis"]
        p["domain"] = c1.selectbox("Bidang", domains, index=domains.index(p.get("domain", "Peternakan")) if p.get("domain", "Peternakan") in domains else 0)
        p["framework"] = c2.selectbox("Kerangka", ["PICOS", "PECO", "PICO"], index=["PICOS", "PECO", "PICO"].index(p.get("framework", "PICOS")) if p.get("framework", "PICOS") in ["PICOS", "PECO", "PICO"] else 0)
        p["target_level"] = c3.selectbox("Target", ["Q1/Q2", "Q2/Q3", "Scopus awal", "Sinta/Kampus"], index=["Q1/Q2", "Q2/Q3", "Scopus awal", "Sinta/Kampus"].index(p.get("target_level", "Q1/Q2")) if p.get("target_level", "Q1/Q2") in ["Q1/Q2", "Q2/Q3", "Scopus awal", "Sinta/Kampus"] else 0)
        p["geographical_scope"] = c4.selectbox("Cakupan", ["Global", "Asia", "Indonesia", "Lokal/Daerah"], index=["Global", "Asia", "Indonesia", "Lokal/Daerah"].index(p.get("geographical_scope", "Global")) if p.get("geographical_scope", "Global") in ["Global", "Asia", "Indonesia", "Lokal/Daerah"] else 0)
        c5, c6 = st.columns(2)
        p["population"] = c5.text_input("Population / Problem", value=p.get("population", ""))
        p["intervention"] = c6.text_input("Intervention / Exposure", value=p.get("intervention", ""))
        p["comparator"] = c5.text_input("Comparator", value=p.get("comparator", ""))
        p["outcome"] = c6.text_input("Outcome", value=p.get("outcome", ""))
        p["study_design"] = c5.text_input("Study design", value=p.get("study_design", ""))
        p["year_range"] = c6.text_input("Rentang tahun", value=p.get("year_range", "2015-2026"))
        p["language"] = c5.text_input("Bahasa artikel", value=p.get("language", "English and Bahasa Indonesia"))
        p["review_type"] = c6.selectbox("Jenis review", ["Systematic Review", "Systematic Review and Meta-Analysis", "Systematic Map", "Scoping Review"], index=["Systematic Review", "Systematic Review and Meta-Analysis", "Systematic Map", "Scoping Review"].index(p.get("review_type", "Systematic Review and Meta-Analysis")) if p.get("review_type", "Systematic Review and Meta-Analysis") in ["Systematic Review", "Systematic Review and Meta-Analysis", "Systematic Map", "Scoping Review"] else 1)
        submitted = st.form_submit_button("Simpan dan analisis", use_container_width=True)
    if submitted:
        st.session_state.project = p
        st.session_state.terms = suggest_terms_from_project(p)
        st.success("Data proyek disimpan dan search terms otomatis diperbarui.")

    result = analyze_title(st.session_state.project)
    st.subheader("Hasil Analisis Kelayakan")
    c1, c2, c3 = st.columns([1, 2, 2])
    c1.metric("Skor", f"{result['score']}/100")
    c2.info(result["readiness"])
    c3.write(f"**Domain terdeteksi:** {result['domain']}")
    score_df = pd.DataFrame([{"Aspek": k, "Skor": v} for k, v in result["sub_scores"].items()])
    st.bar_chart(score_df.set_index("Aspek"))
    left, right = st.columns(2)
    with left:
        st.subheader("Kekuatan")
        for item in result["strengths"]:
            st.success(item)
    with right:
        st.subheader("Kelemahan")
        for item in result["weaknesses"]:
            st.warning(item)
    st.subheader("Rekomendasi judul dan pertanyaan penelitian")
    for i, t in enumerate(result["suggested_titles"], 1):
        st.markdown(f"**Judul {i}:** {t}")
    for i, rq in enumerate(result["research_questions"], 1):
        st.markdown(f"**RQ {i}:** {rq}")
    if st.button("Gunakan Research Question pertama", use_container_width=True):
        st.session_state.project["research_question"] = result["research_questions"][0]
        st.success("Research question diterapkan.")


def page_protocol_search():
    st.header("2. Protocol dan Search Strategy")
    p = st.session_state.project
    c = st.session_state.criteria
    with st.form("protocol_search"):
        p["research_question"] = st.text_area("Research question", value=p.get("research_question", ""), height=70)
        c["inclusion"] = st.text_area("Kriteria inklusi", value=c.get("inclusion", ""), height=90)
        c["exclusion"] = st.text_area("Kriteria eksklusi", value=c.get("exclusion", ""), height=90)
        st.subheader("Search terms")
        t = st.session_state.terms.copy()
        col1, col2 = st.columns(2)
        t["population_terms"] = col1.text_area("Population terms", value=t.get("population_terms", ""), height=120)
        t["intervention_terms"] = col2.text_area("Intervention/exposure terms", value=t.get("intervention_terms", ""), height=120)
        t["comparator_terms"] = col1.text_area("Comparator terms", value=t.get("comparator_terms", ""), height=100)
        t["outcome_terms"] = col2.text_area("Outcome terms", value=t.get("outcome_terms", ""), height=100)
        t["study_terms"] = st.text_area("Study design terms", value=t.get("study_terms", ""), height=80)
        submitted = st.form_submit_button("Simpan protocol dan search strategy", use_container_width=True)
    if submitted:
        st.session_state.project = p
        st.session_state.criteria = c
        st.session_state.terms = t
        st.session_state.articles = apply_relevance_scoring(st.session_state.articles)
        st.success("Protocol dan search strategy tersimpan. Relevance scoring artikel juga diperbarui.")

    result = analyze_title(st.session_state.project)
    profile = DOMAIN_PROFILES.get(result["domain"], DOMAIN_PROFILES["Peternakan"])
    c1, c2 = st.columns(2)
    c1.subheader("Database disarankan")
    c1.markdown("\n".join([f"- {db}" for db in profile["databases"]]))
    c2.subheader("Quality tool disarankan")
    c2.write(profile["quality_tool"])
    st.subheader("Boolean Search String")
    st.code(build_search_string(st.session_state.terms), language="text")
    st.download_button("Download protocol.md", make_protocol_markdown().encode("utf-8"), "protocol_systematic_review.md", "text/markdown", use_container_width=True)
    with st.expander("Preview protocol"):
        st.markdown(make_protocol_markdown())


def page_import_screening():
    st.header("3-4. Import Artikel dan Screening Terintegrasi")
    st.write("Unggah hasil ekspor dari database dalam format CSV, XLSX, atau RIS. Sistem akan menormalisasi kolom, mendeteksi duplikasi, dan memberi skor relevansi berdasarkan PICOS/PECO.")
    sample_path = "data/sample_articles.csv"
    with open(sample_path, "rb") as f:
        st.download_button("Download template/sample CSV", f.read(), "sample_articles.csv", "text/csv", use_container_width=True)
    upload = st.file_uploader("Upload file artikel", type=["csv", "xlsx", "xls", "ris"])
    col1, col2 = st.columns(2)
    if upload is not None:
        try:
            raw = read_uploaded_file(upload)
            df = normalize_columns(raw)
            df = flag_duplicates(df)
            df = apply_relevance_scoring(df)
            if col1.button("Gunakan file ini sebagai dataset screening", use_container_width=True):
                st.session_state.articles = df
                sync_quality_extraction()
                st.success("Artikel berhasil dimuat.")
            st.dataframe(df.head(20), use_container_width=True)
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
    if col2.button("Muat sample data", use_container_width=True):
        df = pd.read_csv(sample_path)
        df = normalize_columns(df)
        df = flag_duplicates(df)
        df = apply_relevance_scoring(df)
        st.session_state.articles = df
        sync_quality_extraction()
        st.success("Sample data dimuat.")

    if st.session_state.articles.empty:
        st.warning("Belum ada artikel yang dimuat.")
        return

    a = st.session_state.articles.copy()
    st.subheader("Insight awal dataset")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total artikel", len(a))
    c2.metric("Duplikasi", int(a["duplicate"].sum()))
    c3.metric("Rata-rata relevansi", f"{pd.to_numeric(a['picos_relevance_score'], errors='coerce').fillna(0).mean():.1f}")
    c4.metric("Saran Include", int((a["auto_screening_suggestion"] == "Include").sum()))

    st.subheader("Screening table")
    edited = st.data_editor(
        a,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "duplicate": st.column_config.CheckboxColumn("Duplicate"),
            "picos_relevance_score": st.column_config.ProgressColumn("PICOS relevance", min_value=0, max_value=100),
            "screening_decision": st.column_config.SelectboxColumn("Screening decision", options=["Belum dinilai", "Include", "Maybe", "Exclude"]),
            "full_text_decision": st.column_config.SelectboxColumn("Full-text decision", options=["Belum dinilai", "Include", "Exclude"]),
            "exclusion_reason": st.column_config.SelectboxColumn("Exclusion reason", options=["", "Tidak relevan", "Bukan studi empiris", "Populasi tidak sesuai", "Intervensi tidak sesuai", "Outcome tidak sesuai", "Duplikat", "Data tidak lengkap"]),
            "full_text_exclusion_reason": st.column_config.SelectboxColumn("Full-text exclusion reason", options=["", "Full text tidak tersedia", "Data outcome tidak lengkap", "Metode tidak sesuai", "Populasi/intervensi/outcome tidak sesuai", "Duplikat", "Artikel bukan peer-reviewed"]),
        },
        key="screening_editor"
    )
    if st.button("Simpan hasil screening dan sinkronkan", use_container_width=True):
        st.session_state.articles = flag_duplicates(edited)
        st.session_state.articles = apply_relevance_scoring(st.session_state.articles)
        sync_quality_extraction()
        st.success("Screening disimpan. PRISMA, Quality Assessment, dan Data Extraction sudah disinkronkan.")
    download_df_button("Download screening_results.csv", st.session_state.articles, "screening_results.csv")


def page_prisma_quality():
    st.header("5-6. PRISMA dan Quality Assessment")
    if st.session_state.articles.empty:
        st.warning("Import artikel terlebih dahulu.")
        return
    counts = get_prisma_counts(True)
    st.subheader("PRISMA Flow Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records identified", counts["records_database"] + counts["records_other"])
    c2.metric("Duplicates removed", counts["duplicates_removed"])
    c3.metric("Full-text assessed", counts["full_text_assessed"])
    c4.metric("Studies included", counts["studies_included"])
    st.code(f"""
Identification
Records from databases: {counts['records_database']}
Records from other sources: {counts['records_other']}
Duplicates removed: {counts['duplicates_removed']}

Screening
Records screened: {counts['records_screened']}
Records excluded at title/abstract: {counts['records_excluded_title_abs']}

Eligibility
Full-text articles assessed: {counts['full_text_assessed']}
Full-text articles excluded: {counts['full_text_excluded']}

Included
Studies included in final synthesis: {counts['studies_included']}
""", language="text")
    prisma_df = pd.DataFrame([counts])
    download_df_button("Download prisma_counts.csv", prisma_df, "prisma_counts.csv")

    st.subheader("Quality Assessment")
    sync_quality_extraction()
    q = calculate_quality(st.session_state.quality)
    if q.empty:
        st.info("Belum ada artikel include untuk dinilai kualitasnya.")
        return
    edited = st.data_editor(
        q,
        use_container_width=True,
        disabled=["quality_score", "quality_category"],
        column_config={
            "clear_objective": st.column_config.CheckboxColumn("Clear objective"),
            "appropriate_design": st.column_config.CheckboxColumn("Appropriate design"),
            "adequate_sample": st.column_config.CheckboxColumn("Adequate sample"),
            "clear_intervention": st.column_config.CheckboxColumn("Clear intervention"),
            "valid_outcome": st.column_config.CheckboxColumn("Valid outcome"),
            "adequate_statistics": st.column_config.CheckboxColumn("Adequate statistics"),
            "bias_control": st.column_config.CheckboxColumn("Bias control"),
            "complete_reporting": st.column_config.CheckboxColumn("Complete reporting"),
        },
        key="quality_editor"
    )
    if st.button("Simpan quality assessment", use_container_width=True):
        st.session_state.quality = calculate_quality(edited)
        st.success("Quality assessment disimpan.")
    if not st.session_state.quality.empty:
        st.bar_chart(st.session_state.quality["quality_category"].value_counts())
    download_df_button("Download quality_assessment.csv", st.session_state.quality, "quality_assessment.csv")


def page_extraction():
    st.header("7. Data Extraction")
    if st.session_state.articles.empty:
        st.warning("Import artikel terlebih dahulu.")
        return
    sync_quality_extraction()
    e = st.session_state.extraction.copy()
    if e.empty:
        st.info("Belum ada artikel include untuk diekstraksi.")
        return
    edited = st.data_editor(
        e,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "effect_direction": st.column_config.SelectboxColumn("Effect direction", options=["", "Positive", "Negative", "No effect", "Mixed"]),
            "key_finding": st.column_config.TextColumn("Key finding", width="large"),
            "limitations": st.column_config.TextColumn("Limitations", width="large"),
            "implication": st.column_config.TextColumn("Implication", width="large"),
        },
        key="extraction_editor"
    )
    if st.button("Simpan data extraction", use_container_width=True):
        st.session_state.extraction = edited
        st.success("Data extraction disimpan.")
    st.subheader("Insight extraction sementara")
    if "effect_direction" in edited:
        effects = edited["effect_direction"].replace("", np.nan).dropna().value_counts()
        if not effects.empty:
            st.bar_chart(effects)
    download_df_button("Download data_extraction.csv", st.session_state.extraction, "data_extraction.csv")


def page_insight_export():
    st.header("8. Evidence Insight Report dan Export")
    st.write("Halaman ini membaca semua bagian sistem dan menyusun informasi/insight otomatis untuk membantu penulisan Results, Discussion, Limitations, dan Future Research.")
    if st.session_state.articles.empty:
        st.warning("Belum ada data artikel. Anda tetap bisa mengekspor protocol, tetapi insight bukti belum lengkap.")

    title_result = analyze_title(st.session_state.project)
    evidence = infer_evidence_strength()
    counts = get_prisma_counts(True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Skor judul/protocol", f"{title_result['score']}/100")
    c2.metric("Include final", counts["studies_included"])
    c3.metric("Kualitas bukti", evidence["strength"])
    c4.metric("Meta-analysis", "Potensial" if evidence["meta_ready"] else "Belum siap")

    st.subheader("Insight utama")
    report = build_insight_report()
    st.markdown(report)

    st.subheader("Descriptive charts")
    a, q, e = st.session_state.articles, st.session_state.quality, st.session_state.extraction
    col1, col2 = st.columns(2)
    if not a.empty:
        years = pd.to_numeric(a["year"], errors="coerce").dropna().astype(int)
        if not years.empty:
            col1.write("Distribusi tahun publikasi")
            col1.bar_chart(years.value_counts().sort_index())
        countries = a["country"].replace("", np.nan).dropna().value_counts().head(15)
        if not countries.empty:
            col2.write("Distribusi negara")
            col2.bar_chart(countries)
    col3, col4 = st.columns(2)
    if not e.empty:
        effects = e["effect_direction"].replace("", np.nan).dropna().value_counts()
        if not effects.empty:
            col3.write("Arah efek")
            col3.bar_chart(effects)
    if not q.empty:
        qv = q["quality_category"].replace("", np.nan).dropna().value_counts()
        if not qv.empty:
            col4.write("Kategori kualitas")
            col4.bar_chart(qv)

    st.subheader("Export")
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download protocol.md", make_protocol_markdown().encode("utf-8"), "protocol_systematic_review.md", "text/markdown", use_container_width=True)
    c2.download_button("Download methods_template.md", make_methods_template().encode("utf-8"), "methods_template.md", "text/markdown", use_container_width=True)
    c3.download_button("Download insight_report.md", report.encode("utf-8"), "evidence_insight_report.md", "text/markdown", use_container_width=True)
    st.download_button("Download semua hasil sebagai ZIP", make_export_zip(), "systematic_review_export_package.zip", "application/zip", use_container_width=True)


def main():
    init_state()
    render_sidebar()
    page = st.sidebar.radio(
        "Menu utama",
        [
            "Panduan Workflow",
            "1. Judul & PICOS/PECO",
            "2. Protocol & Search",
            "3-4. Import & Screening",
            "5-6. PRISMA & Quality",
            "7. Data Extraction",
            "8. Insight & Export",
        ],
    )
    if page == "Panduan Workflow":
        page_workflow()
    elif page == "1. Judul & PICOS/PECO":
        page_title_protocol()
    elif page == "2. Protocol & Search":
        page_protocol_search()
    elif page == "3-4. Import & Screening":
        page_import_screening()
    elif page == "5-6. PRISMA & Quality":
        page_prisma_quality()
    elif page == "7. Data Extraction":
        page_extraction()
    elif page == "8. Insight & Export":
        page_insight_export()


if __name__ == "__main__":
    main()
