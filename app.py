import json
import re
from io import StringIO
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Agro Systematic Review Builder",
    page_icon="🌾",
    layout="wide",
)

APP_TITLE = "Agro Systematic Review Builder"
DEFAULT_ARTICLE_COLUMNS = [
    "id", "title", "authors", "year", "journal", "doi", "country", "study_design",
    "species_or_crop", "intervention", "comparator", "outcome", "abstract", "source_database",
    "duplicate", "screening_decision", "exclusion_reason", "full_text_decision", "full_text_exclusion_reason"
]
QUALITY_COLUMNS = [
    "id", "title", "clear_objective", "appropriate_design", "adequate_sample", "clear_intervention",
    "valid_outcome", "adequate_statistics", "bias_control", "complete_reporting", "quality_score", "quality_category", "notes"
]
EXTRACTION_COLUMNS = [
    "id", "title", "species_or_crop", "intervention", "comparator", "sample_size", "duration",
    "main_outcome", "effect_direction", "effect_size", "p_value", "key_finding", "remarks"
]


def init_state():
    defaults = {
        "project": {
            "title": "Systematic Review bidang Agro/Peternakan",
            "domain": "Peternakan / Agro",
            "review_type": "Systematic Review",
            "research_question": "",
            "population": "",
            "intervention": "",
            "comparator": "",
            "outcome": "",
            "study_design": "",
            "date_started": str(date.today()),
        },
        "criteria": {
            "inclusion": "Artikel peer-reviewed, relevan dengan topik, memuat outcome utama, tersedia full text.",
            "exclusion": "Review non-sistematis, prosiding tanpa data lengkap, artikel tidak relevan, duplikasi, tanpa outcome yang dapat diekstraksi.",
        },
        "terms": {
            "population_terms": "broiler chicken\npoultry",
            "intervention_terms": "probiotic\nprebiotic\nsynbiotic",
            "comparator_terms": "control\nbasal diet",
            "outcome_terms": "growth performance\nfeed conversion ratio\nbody weight gain",
            "study_terms": "experimental study\ntrial",
        },
        "articles": pd.DataFrame(columns=DEFAULT_ARTICLE_COLUMNS),
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
        "title_analyzer": {
            "working_title": "Effects of Probiotic Supplementation on Growth Performance in Broiler Chickens: A Systematic Review and Meta-Analysis",
            "domain": "Peternakan",
            "framework": "PICOS",
            "population": "broiler chickens",
            "intervention": "probiotic supplementation",
            "comparator": "control diet or non-supplemented diet",
            "outcome": "growth performance, feed conversion ratio, body weight gain, mortality",
            "study_design": "experimental studies or feeding trials",
            "target_level": "Q1/Q2",
            "geographical_scope": "Global",
            "year_range": "2015-2026",
        },
        "analyzer_result": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    rename = {}
    for col in df.columns:
        clean = col.strip().lower().replace(" ", "_").replace("-", "_")
        rename[col] = clean
    df = df.rename(columns=rename)

    aliases = {
        "article_title": "title",
        "document_title": "title",
        "source_title": "journal",
        "publication_year": "year",
        "publication_title": "journal",
        "abstract_note": "abstract",
        "database": "source_database",
        "study_type": "study_design",
        "crop": "species_or_crop",
        "species": "species_or_crop",
    }
    df = df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})

    for col in DEFAULT_ARTICLE_COLUMNS:
        if col not in df.columns:
            if col in ["duplicate"]:
                df[col] = False
            elif col in ["screening_decision", "full_text_decision"]:
                df[col] = "Belum dinilai"
            else:
                df[col] = ""
    df = df[DEFAULT_ARTICLE_COLUMNS + [c for c in df.columns if c not in DEFAULT_ARTICLE_COLUMNS]]
    if df["id"].astype(str).str.strip().eq("").all():
        df["id"] = [f"A{i+1:03d}" for i in range(len(df))]
    else:
        df["id"] = df["id"].astype(str)
    return df


def read_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    if name.endswith(".ris"):
        return parse_ris(uploaded_file.getvalue().decode("utf-8", errors="ignore"))
    raise ValueError("Format belum didukung. Gunakan CSV, XLSX, atau RIS.")


def parse_ris(text: str) -> pd.DataFrame:
    records = []
    current = {}
    authors = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("TY  -"):
            current = {}
            authors = []
        elif line.startswith("ER  -"):
            current["authors"] = "; ".join(authors)
            records.append(current)
        elif len(line) >= 6 and line[2:6] == "  - ":
            tag = line[:2]
            value = line[6:].strip()
            if tag in ["TI", "T1"]:
                current["title"] = value
            elif tag == "AU":
                authors.append(value)
            elif tag == "PY":
                current["year"] = value[:4]
            elif tag in ["JO", "JF", "T2"]:
                current["journal"] = value
            elif tag == "DO":
                current["doi"] = value
            elif tag in ["AB", "N2"]:
                current["abstract"] = value
    return pd.DataFrame(records)


def flag_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    title_key = df["title"].astype(str).str.lower().str.replace(r"\W+", " ", regex=True).str.strip()
    doi_key = df["doi"].astype(str).str.lower().str.strip()
    dup_title = title_key.duplicated(keep="first") & title_key.ne("")
    dup_doi = doi_key.duplicated(keep="first") & doi_key.ne("")
    df["duplicate"] = dup_title | dup_doi
    return df


def boolean_group(text: str) -> str:
    terms = [t.strip() for t in text.splitlines() if t.strip()]
    quoted = []
    for term in terms:
        if " " in term and not (term.startswith('"') and term.endswith('"')):
            quoted.append(f'"{term}"')
        else:
            quoted.append(term)
    if not quoted:
        return ""
    return "(" + " OR ".join(quoted) + ")"


def build_search_string(terms: dict) -> str:
    groups = [
        boolean_group(terms.get("population_terms", "")),
        boolean_group(terms.get("intervention_terms", "")),
        boolean_group(terms.get("comparator_terms", "")),
        boolean_group(terms.get("outcome_terms", "")),
        boolean_group(terms.get("study_terms", "")),
    ]
    groups = [g for g in groups if g]
    return "\nAND\n".join(groups)


def make_protocol_markdown() -> str:
    p = st.session_state.project
    c = st.session_state.criteria
    search = build_search_string(st.session_state.terms)
    return f"""# Protocol Systematic Review

## Judul
{p.get('title','')}

## Bidang
{p.get('domain','')}

## Jenis Review
{p.get('review_type','')}

## Pertanyaan Penelitian
{p.get('research_question','')}

## Kerangka PICOS/PECO
- Population/Problem: {p.get('population','')}
- Intervention/Exposure: {p.get('intervention','')}
- Comparator: {p.get('comparator','')}
- Outcome: {p.get('outcome','')}
- Study Design: {p.get('study_design','')}

## Kriteria Inklusi
{c.get('inclusion','')}

## Kriteria Eksklusi
{c.get('exclusion','')}

## Search String
```text
{search}
```

## Rencana Screening
Screening dilakukan pada tahap judul/abstrak, dilanjutkan dengan penilaian full-text. Artikel duplikat dihapus sebelum screening. Alasan eksklusi dicatat secara eksplisit.

## Rencana Quality Assessment
Kualitas studi dinilai berdasarkan kejelasan tujuan, kesesuaian desain, kecukupan sampel, kejelasan intervensi, validitas outcome, kecukupan statistik, pengendalian bias, dan kelengkapan pelaporan.

## Rencana Sintesis
Data disintesis secara naratif dan, apabila data homogen serta ukuran efek tersedia, dapat dilanjutkan ke meta-analysis.
"""


def make_methods_template() -> str:
    p = st.session_state.project
    search = build_search_string(st.session_state.terms)
    articles = st.session_state.articles
    total = len(articles)
    dup = int(articles["duplicate"].sum()) if not articles.empty and "duplicate" in articles else 0
    included = 0
    if not articles.empty and "full_text_decision" in articles:
        included = int((articles["full_text_decision"] == "Include").sum())
    return f"""# Draft Methods Section

This systematic review was designed to synthesize empirical evidence related to {p.get('research_question','the review question')}. The review followed a transparent screening and data extraction procedure based on the PICOS framework. The population/problem was defined as {p.get('population','')}, the intervention/exposure as {p.get('intervention','')}, the comparator as {p.get('comparator','')}, and the main outcomes as {p.get('outcome','')}.

Literature searches were conducted using the following Boolean search strategy:

```text
{search}
```

Records retrieved from bibliographic databases were imported into the screening system. Duplicate records were identified based on DOI and normalized article title. A total of {total} records were imported, with {dup} duplicate records flagged by the system. Title and abstract screening was conducted according to predefined inclusion and exclusion criteria. Eligible studies were then assessed at the full-text stage. Studies that met all eligibility criteria were included in the final synthesis.

Data extraction covered bibliographic information, country, study design, species/crop, intervention, comparator, sample size, duration, outcomes, effect direction, and key findings. Study quality was assessed using a structured checklist covering objective clarity, design appropriateness, sample adequacy, intervention clarity, outcome validity, statistical adequacy, bias control, and reporting completeness. Quality scores were categorized as high, moderate, or low to support interpretation of the evidence.

Based on the current screening file, {included} studies were marked as included for final synthesis. The synthesis was conducted narratively by comparing intervention effects, outcome patterns, methodological quality, and research gaps across the included studies.
"""


DOMAIN_PROFILES = {
    "Peternakan": {
        "objects": ["broiler", "chicken", "poultry", "ruminant", "cattle", "goat", "sheep", "dairy", "layer", "duck"],
        "interventions": ["probiotic", "prebiotic", "synbiotic", "feed additive", "black soldier fly", "herbal", "enzyme", "antibiotic alternative"],
        "outcomes": ["growth performance", "feed conversion ratio", "body weight", "mortality", "egg production", "milk yield", "methane", "digestibility"],
        "databases": ["Scopus", "Web of Science", "CAB Abstracts", "ScienceDirect", "PubMed", "SpringerLink", "Wiley Online Library"],
        "quality_tool": "SYRCLE/ARRIVE-based checklist untuk studi hewan; JBI atau Newcastle-Ottawa untuk observasional.",
    },
    "Agro/Agronomi": {
        "objects": ["maize", "rice", "paddy", "wheat", "soybean", "soil", "crop", "plant", "zea mays", "oryza"],
        "interventions": ["biochar", "organic fertilizer", "compost", "irrigation", "drought", "nitrogen", "mulch", "climate-smart"],
        "outcomes": ["yield", "soil organic carbon", "nutrient availability", "nitrogen uptake", "water use efficiency", "productivity"],
        "databases": ["Scopus", "Web of Science", "CAB Abstracts", "AGRICOLA", "ScienceDirect", "SpringerLink", "Taylor & Francis"],
        "quality_tool": "CEE/ROSES critical appraisal, JBI checklist, atau checklist desain eksperimen lapangan.",
    },
    "Perikanan/Akuakultur": {
        "objects": ["fish", "tilapia", "shrimp", "catfish", "aquaculture", "carp", "salmon"],
        "interventions": ["feed additive", "probiotic", "prebiotic", "replacement", "biofloc", "water quality", "immunostimulant"],
        "outcomes": ["growth performance", "feed conversion ratio", "survival rate", "immune response", "water quality"],
        "databases": ["Scopus", "Web of Science", "Aquatic Sciences and Fisheries Abstracts", "ScienceDirect", "SpringerLink", "Wiley Online Library"],
        "quality_tool": "Checklist eksperimen akuakultur berbasis desain, outcome, statistik, dan bias reporting.",
    },
    "Pangan": {
        "objects": ["food", "functional food", "meat", "milk", "grain", "fruit", "vegetable", "processing"],
        "interventions": ["processing", "fermentation", "packaging", "fortification", "drying", "storage", "edible coating"],
        "outcomes": ["quality", "shelf life", "antioxidant", "microbial", "sensory", "nutritional", "safety"],
        "databases": ["Scopus", "Web of Science", "ScienceDirect", "PubMed", "Food Science and Technology Abstracts", "Wiley Online Library"],
        "quality_tool": "JBI checklist, desain eksperimen pangan, atau quality appraisal sesuai tipe studi.",
    },
    "Lingkungan": {
        "objects": ["soil", "water", "waste", "ecosystem", "land", "emission", "climate", "biodiversity"],
        "interventions": ["remediation", "biochar", "waste management", "mitigation", "conservation", "restoration"],
        "outcomes": ["carbon", "emission", "pollution", "biodiversity", "soil quality", "water quality", "sustainability"],
        "databases": ["Scopus", "Web of Science", "Environmental Evidence", "ScienceDirect", "SpringerLink", "Taylor & Francis"],
        "quality_tool": "ROSES/CEE critical appraisal untuk evidence synthesis lingkungan.",
    },
}

GENERIC_BAD_TERMS = ["review", "systematic review", "kajian", "studi", "analisis", "pengaruh", "effect", "effects", "impact", "artikel"]


def split_phrase_terms(text: str) -> list:
    parts = []
    for chunk in re.split(r"[,;/\n]+", text or ""):
        clean = chunk.strip().lower()
        clean = re.sub(r"\s+", " ", clean)
        if clean:
            parts.append(clean)
    return parts


def title_contains_any(title: str, terms: list) -> bool:
    low = title.lower()
    return any(t.lower() in low for t in terms if t)


def infer_domain_from_title(title: str, selected_domain: str) -> str:
    if selected_domain and selected_domain != "Otomatis":
        return selected_domain
    scores = {}
    low = title.lower()
    for domain, profile in DOMAIN_PROFILES.items():
        terms = profile["objects"] + profile["interventions"] + profile["outcomes"]
        scores[domain] = sum(1 for term in terms if term in low)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Peternakan"


def suggest_terms_from_profile(domain: str, population: str, intervention: str, outcome: str, comparator: str = "") -> dict:
    profile = DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["Peternakan"])
    pop_terms = split_phrase_terms(population) or profile["objects"][:4]
    int_terms = split_phrase_terms(intervention) or profile["interventions"][:4]
    comp_terms = split_phrase_terms(comparator) or ["control", "without treatment", "standard practice"]
    out_terms = split_phrase_terms(outcome) or profile["outcomes"][:4]
    return {
        "population_terms": "\n".join(dict.fromkeys(pop_terms + profile["objects"][:3])),
        "intervention_terms": "\n".join(dict.fromkeys(int_terms + profile["interventions"][:3])),
        "comparator_terms": "\n".join(dict.fromkeys(comp_terms)),
        "outcome_terms": "\n".join(dict.fromkeys(out_terms + profile["outcomes"][:3])),
        "study_terms": "experimental study\nfield trial\ncontrolled trial\nobservational study",
    }


def analyze_review_title(data: dict) -> dict:
    title = (data.get("working_title") or "").strip()
    domain = infer_domain_from_title(title, data.get("domain", "Peternakan"))
    framework = data.get("framework", "PICOS")
    population = (data.get("population") or "").strip()
    intervention = (data.get("intervention") or "").strip()
    comparator = (data.get("comparator") or "").strip()
    outcome = (data.get("outcome") or "").strip()
    study_design = (data.get("study_design") or "").strip()
    target_level = data.get("target_level", "Q1/Q2")
    geo = data.get("geographical_scope", "Global")
    year_range = data.get("year_range", "")

    has_review_label = bool(re.search(r"systematic review|meta-analysis|meta analysis|systematic map|scoping review", title, re.I))
    has_population = bool(population) or title_contains_any(title, DOMAIN_PROFILES.get(domain, {}).get("objects", []))
    has_intervention = bool(intervention) or title_contains_any(title, DOMAIN_PROFILES.get(domain, {}).get("interventions", []))
    has_outcome = bool(outcome) or title_contains_any(title, DOMAIN_PROFILES.get(domain, {}).get("outcomes", []))
    has_comparator = bool(comparator) or bool(re.search(r"control|compared|versus|vs\.?|without|conventional", title, re.I))
    has_study_design = bool(study_design) or has_review_label
    global_scope = geo.lower() in ["global", "internasional", "international"] or not re.search(r"indonesia|local|lokal|kabupaten|kecamatan", title, re.I)
    title_len = len(title.split())
    too_short = title_len < 8
    too_long = title_len > 28
    too_generic = sum(1 for term in GENERIC_BAD_TERMS if term in title.lower()) >= 3 and not (has_population and has_intervention and has_outcome)

    sub_scores = {
        "Kejelasan topik": 15 if has_population and has_intervention else 8 if has_population or has_intervention else 3,
        "Kelengkapan PICOS/PECO": sum([has_population, has_intervention, has_comparator, has_outcome, has_study_design]) * 7,
        "Outcome terukur": 15 if has_outcome else 5,
        "Kelayakan meta-analysis": 12 if has_outcome and has_comparator else 6 if has_outcome else 2,
        "Relevansi global": 10 if global_scope else 5,
        "Kerapian judul": 8 if not too_short and not too_long and has_review_label else 4,
    }
    score = min(100, int(sum(sub_scores.values())))

    weaknesses = []
    if not title:
        weaknesses.append("Judul belum diisi.")
    if too_short:
        weaknesses.append("Judul terlalu pendek; tambahkan objek, intervensi, outcome, dan jenis review.")
    if too_long:
        weaknesses.append("Judul cukup panjang; pertimbangkan membuatnya lebih padat agar mudah dibaca reviewer.")
    if not has_review_label:
        weaknesses.append("Judul belum menyebut jenis naskah, misalnya Systematic Review atau Systematic Review and Meta-Analysis.")
    if not has_population:
        weaknesses.append("Population/problem belum jelas. Sebutkan spesies, komoditas, crop, tanah, atau sistem produksi yang dikaji.")
    if not has_intervention:
        weaknesses.append("Intervention/exposure belum jelas. Sebutkan perlakuan seperti probiotik, biochar, pupuk organik, BSF larvae meal, atau teknologi tertentu.")
    if not has_comparator:
        weaknesses.append("Comparator belum eksplisit. Tambahkan pembanding seperti control diet, no treatment, conventional practice, atau non-amended soil.")
    if not has_outcome:
        weaknesses.append("Outcome belum terlihat. Tambahkan variabel hasil seperti FCR, body weight gain, yield, soil organic carbon, mortality, atau nutrient uptake.")
    if too_generic:
        weaknesses.append("Judul masih terasa umum seperti narrative review. Perjelas agar cocok menjadi systematic review.")
    if not global_scope:
        weaknesses.append("Ruang lingkup masih lokal. Untuk target Q-level, jelaskan kontribusi global atau alasan konteks lokal penting secara internasional.")

    strengths = []
    if has_population:
        strengths.append("Objek/populasi sudah mulai terarah.")
    if has_intervention:
        strengths.append("Intervensi/eksposur sudah dapat dikenali.")
    if has_outcome:
        strengths.append("Outcome sudah mendukung sintesis bukti.")
    if has_review_label:
        strengths.append("Jenis naskah review sudah tercermin pada judul.")
    if has_outcome and has_comparator:
        strengths.append("Topik berpotensi dikembangkan menjadi meta-analysis apabila data studi homogen.")

    readiness = "Belum siap"
    if score >= 80:
        readiness = "Siap dikembangkan untuk target Q-level"
    elif score >= 60:
        readiness = "Cukup siap, tetapi perlu penguatan metode dan cakupan"
    elif score >= 40:
        readiness = "Perlu revisi besar sebelum layak menjadi systematic review"

    base_pop = population or "target population/commodity"
    base_int = intervention or "intervention/exposure"
    base_comp = comparator or "control or conventional practice"
    base_out = outcome or "main outcomes"
    suggested_titles = [
        f"Effects of {base_int.title()} on {base_out.title()} in {base_pop.title()}: A Systematic Review",
        f"{base_int.title()} for Improving {base_out.title()} in {base_pop.title()}: A Systematic Review and Meta-Analysis",
        f"Evidence on {base_int.title()} Compared with {base_comp.title()} for {base_pop.title()}: A Systematic Review",
    ]
    research_questions = [
        f"How does {base_int} affect {base_out} in {base_pop} compared with {base_comp}?",
        f"What factors explain variation in the effects of {base_int} on {base_out} across studies involving {base_pop}?",
        f"What is the quality and strength of evidence for the use of {base_int} in {base_pop}?",
    ]

    auto_terms = suggest_terms_from_profile(domain, base_pop, base_int, base_out, base_comp)
    search_string = build_search_string(auto_terms)
    inclusion = f"Peer-reviewed empirical studies published within {year_range or 'the predefined year range'}; studies involving {base_pop}; studies evaluating {base_int}; studies reporting {base_out}; articles with sufficient methodological and outcome data for synthesis."
    exclusion = "Narrative reviews, opinion papers, editorials, duplicated records, studies without relevant outcome data, articles without accessible full text, and studies outside the predefined scope or language criteria."

    protocol = f"""# Draft Protocol Awal Berbasis Analisis Judul\n\n## Judul Sementara\n{title}\n\n## Domain\n{domain}\n\n## Target Publikasi\n{target_level}\n\n## Kerangka {framework}\n- Population/Problem: {base_pop}\n- Intervention/Exposure: {base_int}\n- Comparator: {base_comp}\n- Outcome: {base_out}\n- Study Design: {study_design or 'Experimental/observational studies sesuai kriteria inklusi'}\n\n## Research Question\n{research_questions[0]}\n\n## Kriteria Inklusi Awal\n{inclusion}\n\n## Kriteria Eksklusi Awal\n{exclusion}\n\n## Database yang Disarankan\n{', '.join(DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES['Peternakan'])['databases'])}\n\n## Search String Awal\n```text\n{search_string}\n```\n\n## Quality Assessment yang Disarankan\n{DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES['Peternakan'])['quality_tool']}\n\n## Rencana Sintesis\nSintesis dilakukan secara naratif dengan membandingkan arah efek, variasi outcome, desain studi, kualitas metodologi, dan konteks agro/peternakan. Meta-analysis dapat dilakukan apabila satuan outcome, desain studi, dan ukuran efek cukup homogen.\n"""

    return {
        "score": score,
        "readiness": readiness,
        "domain": domain,
        "framework": framework,
        "sub_scores": sub_scores,
        "strengths": strengths or ["Belum ada kekuatan utama yang terdeteksi; lengkapi komponen judul dan PICOS/PECO."],
        "weaknesses": weaknesses or ["Tidak ada kelemahan besar yang terdeteksi oleh pemeriksaan otomatis."],
        "suggested_titles": suggested_titles,
        "research_questions": research_questions,
        "auto_terms": auto_terms,
        "search_string": search_string,
        "recommended_databases": DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["Peternakan"])["databases"],
        "quality_tool": DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["Peternakan"])["quality_tool"],
        "inclusion": inclusion,
        "exclusion": exclusion,
        "protocol": protocol,
    }


def apply_analyzer_to_project(result: dict, analyzer: dict):
    p = st.session_state.project.copy()
    p["title"] = analyzer.get("working_title", p.get("title", ""))
    p["domain"] = result.get("domain", analyzer.get("domain", p.get("domain", "")))
    p["review_type"] = "Systematic Review and Meta-Analysis" if "meta" in analyzer.get("working_title", "").lower() else "Systematic Review"
    p["research_question"] = result.get("research_questions", [p.get("research_question", "")])[0]
    p["population"] = analyzer.get("population", "")
    p["intervention"] = analyzer.get("intervention", "")
    p["comparator"] = analyzer.get("comparator", "")
    p["outcome"] = analyzer.get("outcome", "")
    p["study_design"] = analyzer.get("study_design", "")
    st.session_state.project = p
    st.session_state.criteria = {
        "inclusion": result.get("inclusion", st.session_state.criteria.get("inclusion", "")),
        "exclusion": result.get("exclusion", st.session_state.criteria.get("exclusion", "")),
    }
    st.session_state.terms = result.get("auto_terms", st.session_state.terms)


def sync_quality_and_extraction():
    articles = st.session_state.articles
    if articles.empty:
        return
    included = articles[articles["full_text_decision"].eq("Include") | articles["screening_decision"].eq("Include")]
    if included.empty:
        included = articles.head(0)

    quality = st.session_state.quality.copy()
    extraction = st.session_state.extraction.copy()

    for _, row in included.iterrows():
        aid = str(row.get("id", ""))
        title = row.get("title", "")
        if aid and (quality.empty or aid not in quality["id"].astype(str).values):
            new_row = {col: "" for col in QUALITY_COLUMNS}
            new_row.update({
                "id": aid,
                "title": title,
                "clear_objective": False,
                "appropriate_design": False,
                "adequate_sample": False,
                "clear_intervention": False,
                "valid_outcome": False,
                "adequate_statistics": False,
                "bias_control": False,
                "complete_reporting": False,
                "quality_score": 0,
                "quality_category": "Belum dinilai",
            })
            quality = pd.concat([quality, pd.DataFrame([new_row])], ignore_index=True)
        if aid and (extraction.empty or aid not in extraction["id"].astype(str).values):
            new_ex = {col: "" for col in EXTRACTION_COLUMNS}
            new_ex.update({
                "id": aid,
                "title": title,
                "species_or_crop": row.get("species_or_crop", ""),
                "intervention": row.get("intervention", ""),
                "comparator": row.get("comparator", ""),
                "main_outcome": row.get("outcome", ""),
            })
            extraction = pd.concat([extraction, pd.DataFrame([new_ex])], ignore_index=True)

    st.session_state.quality = quality[QUALITY_COLUMNS]
    st.session_state.extraction = extraction[EXTRACTION_COLUMNS]


def calculate_quality(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    bool_cols = [
        "clear_objective", "appropriate_design", "adequate_sample", "clear_intervention",
        "valid_outcome", "adequate_statistics", "bias_control", "complete_reporting"
    ]
    for col in bool_cols:
        if col not in df.columns:
            df[col] = False
        df[col] = df[col].fillna(False).astype(bool)
    df["quality_score"] = df[bool_cols].sum(axis=1)
    df["quality_category"] = pd.cut(
        df["quality_score"],
        bins=[-1, 3, 5, 8],
        labels=["Low", "Moderate", "High"]
    ).astype(str)
    return df


def download_df_button(label: str, df: pd.DataFrame, filename: str):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, csv, filename, "text/csv", use_container_width=True)


def page_title_analyzer():
    st.header("0. Title & Protocol Analyzer")
    st.write("Modul ini membantu peneliti menilai kelayakan judul, menyusun PICOS/PECO, membuat research question, Boolean search, rekomendasi database, dan draft protocol awal.")

    analyzer = st.session_state.title_analyzer.copy()

    with st.form("title_analyzer_form"):
        analyzer["working_title"] = st.text_area("Judul sementara", value=analyzer.get("working_title", ""), height=85)
        cols = st.columns(4)
        domain_options = ["Otomatis", "Peternakan", "Agro/Agronomi", "Perikanan/Akuakultur", "Pangan", "Lingkungan"]
        current_domain = analyzer.get("domain", "Peternakan")
        if current_domain not in domain_options:
            current_domain = "Peternakan"
        analyzer["domain"] = cols[0].selectbox("Bidang", domain_options, index=domain_options.index(current_domain))
        analyzer["framework"] = cols[1].selectbox("Kerangka", ["PICOS", "PECO", "PICO"], index=["PICOS", "PECO", "PICO"].index(analyzer.get("framework", "PICOS")) if analyzer.get("framework", "PICOS") in ["PICOS", "PECO", "PICO"] else 0)
        analyzer["target_level"] = cols[2].selectbox("Target", ["Q1/Q2", "Q2/Q3", "Sinta/Scopus awal", "Internal/Kampus"], index=["Q1/Q2", "Q2/Q3", "Sinta/Scopus awal", "Internal/Kampus"].index(analyzer.get("target_level", "Q1/Q2")) if analyzer.get("target_level", "Q1/Q2") in ["Q1/Q2", "Q2/Q3", "Sinta/Scopus awal", "Internal/Kampus"] else 0)
        analyzer["geographical_scope"] = cols[3].selectbox("Cakupan", ["Global", "Asia", "Indonesia", "Lokal/Daerah"], index=["Global", "Asia", "Indonesia", "Lokal/Daerah"].index(analyzer.get("geographical_scope", "Global")) if analyzer.get("geographical_scope", "Global") in ["Global", "Asia", "Indonesia", "Lokal/Daerah"] else 0)

        st.subheader("Input komponen PICOS/PECO")
        c1, c2 = st.columns(2)
        analyzer["population"] = c1.text_input("Population / Problem", value=analyzer.get("population", ""), placeholder="contoh: broiler chickens, maize, paddy soil")
        analyzer["intervention"] = c2.text_input("Intervention / Exposure", value=analyzer.get("intervention", ""), placeholder="contoh: probiotic supplementation, biochar application")
        analyzer["comparator"] = c1.text_input("Comparator", value=analyzer.get("comparator", ""), placeholder="contoh: control diet, non-biochar soil")
        analyzer["outcome"] = c2.text_input("Outcome", value=analyzer.get("outcome", ""), placeholder="contoh: FCR, body weight gain, yield, soil organic carbon")
        analyzer["study_design"] = c1.text_input("Study design", value=analyzer.get("study_design", ""), placeholder="contoh: experimental studies, field trials")
        analyzer["year_range"] = c2.text_input("Rentang tahun artikel", value=analyzer.get("year_range", "2015-2026"))

        submitted = st.form_submit_button("Analisis judul dan buat protocol otomatis", use_container_width=True)

    if submitted:
        st.session_state.title_analyzer = analyzer
        st.session_state.analyzer_result = analyze_review_title(analyzer)
        st.success("Analisis selesai. Hasil otomatis ditampilkan di bawah.")

    result = st.session_state.get("analyzer_result", {})
    if not result:
        result = analyze_review_title(analyzer)
        st.session_state.analyzer_result = result

    st.subheader("Skor Kesiapan Judul")
    c1, c2, c3 = st.columns([1, 2, 2])
    c1.metric("Skor", f"{result.get('score', 0)}/100")
    c2.info(result.get("readiness", "Belum dianalisis"))
    c3.write(f"**Domain terdeteksi:** {result.get('domain', '-')}")

    score_df = pd.DataFrame([{"Aspek": k, "Skor": v} for k, v in result.get("sub_scores", {}).items()])
    if not score_df.empty:
        st.bar_chart(score_df.set_index("Aspek"))

    left, right = st.columns(2)
    with left:
        st.subheader("Kekuatan")
        for item in result.get("strengths", []):
            st.success(item)
    with right:
        st.subheader("Kelemahan yang perlu diperbaiki")
        for item in result.get("weaknesses", []):
            st.warning(item)

    st.subheader("Rekomendasi Judul yang Lebih Kuat")
    for i, title in enumerate(result.get("suggested_titles", []), start=1):
        st.markdown(f"**Opsi {i}:** {title}")

    st.subheader("Research Question Otomatis")
    for i, rq in enumerate(result.get("research_questions", []), start=1):
        st.markdown(f"{i}. {rq}")

    st.subheader("Database dan Quality Assessment yang Disarankan")
    d1, d2 = st.columns(2)
    d1.markdown("**Database:**\n" + "\n".join([f"- {db}" for db in result.get("recommended_databases", [])]))
    d2.markdown(f"**Quality assessment:**\n\n{result.get('quality_tool', '-')}")

    st.subheader("Boolean Search Otomatis")
    st.code(result.get("search_string", ""), language="text")

    st.subheader("Draft Protocol Awal")
    st.download_button("Download draft_protocol_otomatis.md", result.get("protocol", "").encode("utf-8"), "draft_protocol_otomatis.md", "text/markdown", use_container_width=True)
    st.markdown(result.get("protocol", ""))

    st.subheader("Terapkan ke modul sistem")
    st.write("Tombol ini akan mengisi otomatis menu Protocol & PICOS serta Search Strategy berdasarkan hasil analisis judul.")
    if st.button("Gunakan hasil analisis untuk mengisi Protocol & Search Strategy", use_container_width=True):
        apply_analyzer_to_project(result, analyzer)
        st.success("Hasil analisis sudah diterapkan ke Protocol & PICOS serta Search Strategy.")

    export_payload = json.dumps({"input": analyzer, "analysis": result}, indent=2, ensure_ascii=False)
    st.download_button("Download hasil_analisis_judul.json", export_payload.encode("utf-8"), "hasil_analisis_judul.json", "application/json", use_container_width=True)


def page_dashboard():
    st.title(f"🌾 {APP_TITLE}")
    st.caption("Aplikasi pendamping untuk menyusun systematic review bidang agro, peternakan, pangan, agronomi, perikanan, dan lingkungan.")

    p = st.session_state.project
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Artikel diimpor", len(st.session_state.articles))
    dup = int(st.session_state.articles["duplicate"].sum()) if not st.session_state.articles.empty and "duplicate" in st.session_state.articles else 0
    col2.metric("Duplikasi", dup)
    inc_screen = int((st.session_state.articles["screening_decision"] == "Include").sum()) if not st.session_state.articles.empty else 0
    col3.metric("Include screening", inc_screen)
    inc_full = int((st.session_state.articles["full_text_decision"] == "Include").sum()) if not st.session_state.articles.empty else 0
    col4.metric("Include final", inc_full)

    st.subheader("Ringkasan Proyek")
    st.write(f"**Judul:** {p.get('title','')}")
    st.write(f"**Pertanyaan penelitian:** {p.get('research_question','Belum diisi')}")

    st.subheader("Alur kerja yang disarankan")
    st.markdown(
        """
        1. Mulai dari **Title & Protocol Analyzer** untuk menilai kelayakan judul, membuat PICOS/PECO, dan menyusun protocol awal.  
        2. Cek serta rapikan **Protocol & PICOS** agar pertanyaan review jelas.  
        3. Susun atau revisi **Search Strategy** dengan Boolean string.  
        4. Impor artikel dari CSV/XLSX/RIS pada menu **Import & Screening**.  
        5. Lakukan screening dan catat alasan eksklusi.  
        6. Pantau jumlah artikel di **PRISMA Flow**.  
        7. Nilai kualitas studi, isi data extraction, lalu export paket naskah.
        """
    )


def page_protocol():
    st.header("1. Protocol & PICOS")
    p = st.session_state.project
    c = st.session_state.criteria

    with st.form("protocol_form"):
        p["title"] = st.text_input("Judul review", value=p.get("title", ""))
        cols = st.columns(3)
        p["domain"] = cols[0].text_input("Bidang", value=p.get("domain", ""))
        p["review_type"] = cols[1].selectbox(
            "Jenis naskah",
            ["Systematic Review", "Systematic Review and Meta-Analysis", "Systematic Map", "Scoping Review"],
            index=["Systematic Review", "Systematic Review and Meta-Analysis", "Systematic Map", "Scoping Review"].index(p.get("review_type", "Systematic Review"))
            if p.get("review_type", "Systematic Review") in ["Systematic Review", "Systematic Review and Meta-Analysis", "Systematic Map", "Scoping Review"] else 0
        )
        p["date_started"] = cols[2].text_input("Tanggal mulai", value=p.get("date_started", str(date.today())))
        p["research_question"] = st.text_area("Research question", value=p.get("research_question", ""), height=90)

        st.subheader("PICOS/PECO")
        p["population"] = st.text_input("Population / Problem", value=p.get("population", ""))
        p["intervention"] = st.text_input("Intervention / Exposure", value=p.get("intervention", ""))
        p["comparator"] = st.text_input("Comparator", value=p.get("comparator", ""))
        p["outcome"] = st.text_input("Outcome", value=p.get("outcome", ""))
        p["study_design"] = st.text_input("Study design", value=p.get("study_design", ""))

        st.subheader("Eligibility Criteria")
        c["inclusion"] = st.text_area("Kriteria inklusi", value=c.get("inclusion", ""), height=110)
        c["exclusion"] = st.text_area("Kriteria eksklusi", value=c.get("exclusion", ""), height=110)

        submitted = st.form_submit_button("Simpan protocol", use_container_width=True)
        if submitted:
            st.session_state.project = p
            st.session_state.criteria = c
            st.success("Protocol tersimpan.")

    st.subheader("Preview Protocol")
    protocol = make_protocol_markdown()
    st.download_button("Download protocol.md", protocol.encode("utf-8"), "protocol_systematic_review.md", "text/markdown")
    st.markdown(protocol)


def page_search_strategy():
    st.header("2. Search Strategy Builder")
    st.write("Masukkan sinonim tiap komponen. Satu istilah per baris. Aplikasi akan membuat Boolean search string.")

    terms = st.session_state.terms
    col1, col2 = st.columns(2)
    terms["population_terms"] = col1.text_area("Population terms", value=terms.get("population_terms", ""), height=160)
    terms["intervention_terms"] = col2.text_area("Intervention / exposure terms", value=terms.get("intervention_terms", ""), height=160)
    terms["comparator_terms"] = col1.text_area("Comparator terms", value=terms.get("comparator_terms", ""), height=120)
    terms["outcome_terms"] = col2.text_area("Outcome terms", value=terms.get("outcome_terms", ""), height=120)
    terms["study_terms"] = st.text_area("Study design terms", value=terms.get("study_terms", ""), height=100)
    st.session_state.terms = terms

    search = build_search_string(terms)
    st.subheader("Boolean Search String")
    st.code(search, language="text")
    st.download_button("Download search_string.txt", search.encode("utf-8"), "search_string.txt", "text/plain")

    st.info("Catatan: untuk jurnal bereputasi, tuliskan database, tanggal pencarian, search string per database, dan filter yang digunakan.")


def page_import_screening():
    st.header("3. Import & Screening")
    st.write("Upload artikel dari CSV, Excel, atau RIS. Kolom ideal: title, authors, year, journal, doi, abstract, country, study_design, species_or_crop, intervention, comparator, outcome.")

    uploaded = st.file_uploader("Upload file bibliografi", type=["csv", "xlsx", "xls", "ris"])
    col_a, col_b = st.columns([1, 1])
    if uploaded is not None:
        try:
            raw = read_uploaded_file(uploaded)
            df = normalize_columns(raw)
            df = flag_duplicates(df)
            if col_a.button("Tambahkan ke data screening", use_container_width=True):
                if st.session_state.articles.empty:
                    combined = df
                else:
                    combined = pd.concat([st.session_state.articles, df], ignore_index=True)
                    combined["id"] = [f"A{i+1:03d}" for i in range(len(combined))]
                    combined = flag_duplicates(combined)
                st.session_state.articles = combined
                st.success(f"Berhasil menambahkan {len(df)} artikel.")
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

    if col_b.button("Gunakan data contoh", use_container_width=True):
        sample_path = "data/sample_articles.csv"
        try:
            sample = pd.read_csv(sample_path)
        except FileNotFoundError:
            sample = pd.read_csv("/mnt/data/agro_sysreview_streamlit/data/sample_articles.csv")
        st.session_state.articles = flag_duplicates(normalize_columns(sample))
        st.success("Data contoh dimuat.")

    if st.session_state.articles.empty:
        st.warning("Belum ada data artikel.")
        return

    st.subheader("Screening Table")
    st.caption("Edit keputusan screening langsung di tabel. Gunakan pilihan Include, Exclude, Maybe, atau Belum dinilai.")
    articles = st.session_state.articles.copy()

    edited = st.data_editor(
        articles,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "duplicate": st.column_config.CheckboxColumn("Duplicate"),
            "screening_decision": st.column_config.SelectboxColumn(
                "Screening decision", options=["Belum dinilai", "Include", "Exclude", "Maybe"]
            ),
            "full_text_decision": st.column_config.SelectboxColumn(
                "Full-text decision", options=["Belum dinilai", "Include", "Exclude", "Maybe"]
            ),
            "abstract": st.column_config.TextColumn("Abstract", width="large"),
        },
        key="articles_editor"
    )
    st.session_state.articles = edited

    c1, c2, c3 = st.columns(3)
    if c1.button("Deteksi ulang duplikasi", use_container_width=True):
        st.session_state.articles = flag_duplicates(st.session_state.articles)
        st.rerun()
    if c2.button("Sinkronkan ke quality & extraction", use_container_width=True):
        sync_quality_and_extraction()
        st.success("Data include disinkronkan.")
    if c3.button("Hapus semua artikel", use_container_width=True):
        st.session_state.articles = pd.DataFrame(columns=DEFAULT_ARTICLE_COLUMNS)
        st.session_state.quality = pd.DataFrame(columns=QUALITY_COLUMNS)
        st.session_state.extraction = pd.DataFrame(columns=EXTRACTION_COLUMNS)
        st.rerun()

    download_df_button("Download screening_results.csv", st.session_state.articles, "screening_results.csv")


def page_prisma():
    st.header("4. PRISMA Flow")
    st.write("Gunakan jumlah otomatis dari data screening atau isi manual bila data berasal dari beberapa sumber.")

    articles = st.session_state.articles
    auto = {}
    if articles.empty:
        auto = {
            "records_database": 0,
            "duplicates_removed": 0,
            "records_screened": 0,
            "records_excluded_title_abs": 0,
            "full_text_assessed": 0,
            "full_text_excluded": 0,
            "studies_included": 0,
        }
    else:
        auto["records_database"] = len(articles)
        auto["duplicates_removed"] = int(articles["duplicate"].sum()) if "duplicate" in articles else 0
        non_dup = articles[~articles["duplicate"].fillna(False).astype(bool)] if "duplicate" in articles else articles
        auto["records_screened"] = len(non_dup)
        auto["records_excluded_title_abs"] = int((non_dup["screening_decision"] == "Exclude").sum()) if "screening_decision" in non_dup else 0
        full_pool = non_dup[non_dup["screening_decision"].isin(["Include", "Maybe"])] if "screening_decision" in non_dup else non_dup
        auto["full_text_assessed"] = len(full_pool)
        auto["full_text_excluded"] = int((full_pool["full_text_decision"] == "Exclude").sum()) if "full_text_decision" in full_pool else 0
        auto["studies_included"] = int((full_pool["full_text_decision"] == "Include").sum()) if "full_text_decision" in full_pool else 0

    mode = st.radio("Mode jumlah PRISMA", ["Otomatis dari screening", "Manual"], horizontal=True)
    counts = auto if mode == "Otomatis dari screening" else st.session_state.prisma_manual.copy()

    if mode == "Manual":
        cols = st.columns(4)
        keys = list(st.session_state.prisma_manual.keys())
        for i, k in enumerate(keys):
            counts[k] = cols[i % 4].number_input(k.replace("_", " ").title(), min_value=0, value=int(counts.get(k, 0)))
        st.session_state.prisma_manual = counts

    st.subheader("PRISMA Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records identified", counts.get("records_database", 0) + counts.get("records_other", 0))
    c2.metric("Duplicates removed", counts.get("duplicates_removed", 0))
    c3.metric("Full-text assessed", counts.get("full_text_assessed", 0))
    c4.metric("Studies included", counts.get("studies_included", 0))

    st.markdown(
        f"""
        ```text
        Identification
        Records from databases: {counts.get('records_database', 0)}
        Records from other sources: {counts.get('records_other', 0)}
        Duplicates removed: {counts.get('duplicates_removed', 0)}

        Screening
        Records screened: {counts.get('records_screened', 0)}
        Records excluded at title/abstract: {counts.get('records_excluded_title_abs', 0)}

        Eligibility
        Full-text articles assessed: {counts.get('full_text_assessed', 0)}
        Full-text articles excluded: {counts.get('full_text_excluded', 0)}

        Included
        Studies included in final synthesis: {counts.get('studies_included', 0)}
        ```
        """
    )

    prisma_df = pd.DataFrame([counts])
    download_df_button("Download prisma_counts.csv", prisma_df, "prisma_counts.csv")

    if not articles.empty:
        st.subheader("Alasan Eksklusi Full-text")
        if "full_text_exclusion_reason" in articles:
            reasons = articles.loc[articles["full_text_decision"].eq("Exclude"), "full_text_exclusion_reason"].replace("", np.nan).dropna()
            if not reasons.empty:
                st.bar_chart(reasons.value_counts())
            else:
                st.caption("Belum ada alasan eksklusi full-text yang diisi.")


def page_quality():
    st.header("5. Quality Assessment")
    st.write("Checklist ini bersifat umum dan bisa disesuaikan dengan desain studi agro/peternakan yang dipakai.")

    if st.session_state.articles.empty:
        st.warning("Import dan pilih artikel include terlebih dahulu.")
        return

    sync_quality_and_extraction()
    quality = calculate_quality(st.session_state.quality)

    edited = st.data_editor(
        quality,
        use_container_width=True,
        num_rows="dynamic",
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
    st.session_state.quality = calculate_quality(edited)

    st.subheader("Ringkasan Kualitas")
    if not st.session_state.quality.empty:
        st.bar_chart(st.session_state.quality["quality_category"].value_counts())
    download_df_button("Download quality_assessment.csv", st.session_state.quality, "quality_assessment.csv")


def page_extraction():
    st.header("6. Data Extraction")
    if st.session_state.articles.empty:
        st.warning("Import artikel terlebih dahulu.")
        return

    sync_quality_and_extraction()
    extraction = st.session_state.extraction.copy()
    edited = st.data_editor(
        extraction,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "effect_direction": st.column_config.SelectboxColumn(
                "Effect direction", options=["", "Positive", "Negative", "No effect", "Mixed"]
            ),
            "key_finding": st.column_config.TextColumn("Key finding", width="large"),
        },
        key="extraction_editor"
    )
    st.session_state.extraction = edited
    download_df_button("Download data_extraction.csv", st.session_state.extraction, "data_extraction.csv")


def page_synthesis():
    st.header("7. Synthesis & Export")
    articles = st.session_state.articles
    quality = st.session_state.quality
    extraction = st.session_state.extraction

    if articles.empty:
        st.warning("Belum ada data untuk disintesis.")
        return

    st.subheader("Descriptive Synthesis")
    col1, col2 = st.columns(2)
    if "year" in articles and articles["year"].astype(str).str.strip().ne("").any():
        years = pd.to_numeric(articles["year"], errors="coerce").dropna().astype(int)
        if not years.empty:
            col1.write("Distribusi tahun publikasi")
            col1.bar_chart(years.value_counts().sort_index())

    if "country" in articles and articles["country"].astype(str).str.strip().ne("").any():
        countries = articles["country"].replace("", np.nan).dropna().value_counts().head(15)
        if not countries.empty:
            col2.write("Distribusi negara")
            col2.bar_chart(countries)

    col3, col4 = st.columns(2)
    if not extraction.empty and "effect_direction" in extraction:
        effects = extraction["effect_direction"].replace("", np.nan).dropna().value_counts()
        if not effects.empty:
            col3.write("Arah efek intervensi")
            col3.bar_chart(effects)
    if not quality.empty and "quality_category" in quality:
        q = quality["quality_category"].replace("", np.nan).dropna().value_counts()
        if not q.empty:
            col4.write("Kategori kualitas studi")
            col4.bar_chart(q)

    st.subheader("Auto Summary")
    included_final = articles[articles["full_text_decision"].eq("Include")] if "full_text_decision" in articles else articles
    summary = f"""
    Berdasarkan data yang dimasukkan, terdapat {len(articles)} artikel pada basis screening. Setelah proses full-text, {len(included_final)} artikel ditandai sebagai include untuk sintesis akhir. Sintesis dapat difokuskan pada pola arah efek, jenis intervensi, variasi outcome, kualitas metodologi, serta kesenjangan penelitian yang muncul dari studi-studi yang dianalisis.
    """
    st.write(summary)

    st.subheader("Export Paket Naskah")
    protocol = make_protocol_markdown()
    methods = make_methods_template()
    project_json = json.dumps({
        "project": st.session_state.project,
        "criteria": st.session_state.criteria,
        "terms": st.session_state.terms,
        "prisma_manual": st.session_state.prisma_manual,
    }, indent=2, ensure_ascii=False)

    c1, c2, c3 = st.columns(3)
    c1.download_button("Download protocol.md", protocol.encode("utf-8"), "protocol_systematic_review.md", "text/markdown", use_container_width=True)
    c2.download_button("Download methods_template.md", methods.encode("utf-8"), "methods_template.md", "text/markdown", use_container_width=True)
    c3.download_button("Download project_config.json", project_json.encode("utf-8"), "project_config.json", "application/json", use_container_width=True)

    c4, c5, c6 = st.columns(3)
    with c4:
        download_df_button("Download screening.csv", articles, "screening_results.csv")
    with c5:
        download_df_button("Download quality.csv", quality, "quality_assessment.csv")
    with c6:
        download_df_button("Download extraction.csv", extraction, "data_extraction.csv")


def main():
    init_state()
    st.sidebar.title("Navigasi")
    page = st.sidebar.radio(
        "Menu",
        [
            "Dashboard",
            "Title & Protocol Analyzer",
            "Protocol & PICOS",
            "Search Strategy",
            "Import & Screening",
            "PRISMA Flow",
            "Quality Assessment",
            "Data Extraction",
            "Synthesis & Export",
        ],
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("Dibuat untuk systematic review agro, peternakan, agronomi, pangan, perikanan, dan lingkungan.")

    if page == "Dashboard":
        page_dashboard()
    elif page == "Title & Protocol Analyzer":
        page_title_analyzer()
    elif page == "Protocol & PICOS":
        page_protocol()
    elif page == "Search Strategy":
        page_search_strategy()
    elif page == "Import & Screening":
        page_import_screening()
    elif page == "PRISMA Flow":
        page_prisma()
    elif page == "Quality Assessment":
        page_quality()
    elif page == "Data Extraction":
        page_extraction()
    elif page == "Synthesis & Export":
        page_synthesis()


if __name__ == "__main__":
    main()
