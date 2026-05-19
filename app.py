import json
import re
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Integrated Agro Systematic Review Builder",
    page_icon="🌾",
    layout="wide",
)

APP_TITLE = "Integrated Agro Systematic Review Builder"
APP_VERSION = "2.0-integrated"

ARTICLE_COLUMNS = [
    "id", "title", "authors", "year", "journal", "doi", "country", "study_design",
    "species_or_crop", "intervention", "comparator", "outcome", "abstract", "source_database",
    "picos_relevance_score", "duplicate", "screening_suggestion", "screening_decision",
    "exclusion_reason", "full_text_decision", "full_text_exclusion_reason"
]

QUALITY_COLUMNS = [
    "id", "title", "clear_objective", "appropriate_design", "adequate_sample",
    "clear_intervention", "valid_outcome", "adequate_statistics", "bias_control",
    "complete_reporting", "quality_score", "quality_category", "notes"
]

EXTRACTION_COLUMNS = [
    "id", "title", "species_or_crop", "intervention", "comparator", "sample_size",
    "duration", "main_outcome", "effect_direction", "effect_size", "p_value",
    "key_finding", "remarks"
]

BOOLEAN_FIELDS = [
    "population_terms", "intervention_terms", "comparator_terms", "outcome_terms", "study_terms"
]

QUALITY_BOOL_COLS = [
    "clear_objective", "appropriate_design", "adequate_sample", "clear_intervention",
    "valid_outcome", "adequate_statistics", "bias_control", "complete_reporting"
]

DOMAIN_PROFILES = {
    "Peternakan": {
        "objects": ["broiler", "chicken", "poultry", "ruminant", "cattle", "goat", "sheep", "dairy", "layer", "duck"],
        "interventions": ["probiotic", "prebiotic", "synbiotic", "feed additive", "black soldier fly", "herbal", "enzyme", "antibiotic alternative"],
        "outcomes": ["growth performance", "feed conversion ratio", "fcr", "body weight", "mortality", "egg production", "milk yield", "methane", "digestibility"],
        "databases": ["Scopus", "Web of Science", "CAB Abstracts", "ScienceDirect", "PubMed", "SpringerLink", "Wiley Online Library"],
        "quality_tool": "SYRCLE/ARRIVE-based checklist untuk studi hewan; JBI atau Newcastle-Ottawa untuk observasional.",
    },
    "Agro/Agronomi": {
        "objects": ["maize", "corn", "rice", "paddy", "wheat", "soybean", "soil", "crop", "plant", "zea mays", "oryza"],
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

DEFAULT_ANALYZER = {
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
}

DEFAULT_PROJECT = {
    "title": DEFAULT_ANALYZER["working_title"],
    "domain": "Peternakan",
    "review_type": "Systematic Review and Meta-Analysis",
    "framework": "PICOS",
    "target_level": "Q1/Q2",
    "geographical_scope": "Global",
    "year_range": "2015-2026",
    "research_question": "How does probiotic supplementation affect growth performance, feed conversion ratio, body weight gain, and mortality in broiler chickens compared with control diet or non-supplemented diet?",
    "population": "broiler chickens",
    "intervention": "probiotic supplementation",
    "comparator": "control diet or non-supplemented diet",
    "outcome": "growth performance, feed conversion ratio, body weight gain, mortality",
    "study_design": "experimental studies or feeding trials",
    "date_started": str(date.today()),
}

DEFAULT_CRITERIA = {
    "inclusion": "Artikel peer-reviewed; studi empiris; relevan dengan population/intervention/comparator/outcome; memuat outcome utama; tersedia full text; memiliki data metodologi yang dapat diekstraksi.",
    "exclusion": "Narrative review, editorial, opinion paper, duplikasi, prosiding tanpa data lengkap, artikel di luar ruang lingkup, tanpa outcome relevan, atau full text tidak tersedia.",
}

DEFAULT_TERMS = {
    "population_terms": "broiler chicken\npoultry\nGallus gallus",
    "intervention_terms": "probiotic\nprebiotic\nsynbiotic",
    "comparator_terms": "control\nbasal diet\nnon-supplemented diet",
    "outcome_terms": "growth performance\nfeed conversion ratio\nbody weight gain\nmortality",
    "study_terms": "experimental study\nfeeding trial\ncontrolled trial",
}


def empty_articles() -> pd.DataFrame:
    return pd.DataFrame(columns=ARTICLE_COLUMNS)


def empty_quality() -> pd.DataFrame:
    return pd.DataFrame(columns=QUALITY_COLUMNS)


def empty_extraction() -> pd.DataFrame:
    return pd.DataFrame(columns=EXTRACTION_COLUMNS)


def init_state() -> None:
    defaults = {
        "app_version": APP_VERSION,
        "analyzer": DEFAULT_ANALYZER.copy(),
        "analyzer_result": {},
        "project": DEFAULT_PROJECT.copy(),
        "criteria": DEFAULT_CRITERIA.copy(),
        "terms": DEFAULT_TERMS.copy(),
        "databases": DOMAIN_PROFILES["Peternakan"]["databases"].copy(),
        "quality_tool": DOMAIN_PROFILES["Peternakan"]["quality_tool"],
        "articles": empty_articles(),
        "quality": empty_quality(),
        "extraction": empty_extraction(),
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
        "use_manual_prisma": False,
        "workflow_log": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_log(message: str) -> None:
    logs = st.session_state.get("workflow_log", [])
    logs.append({"date": str(date.today()), "message": message})
    st.session_state.workflow_log = logs[-25:]


def split_terms(text: str) -> list[str]:
    if text is None:
        return []
    parts = re.split(r"[,;/\n]+", str(text))
    cleaned = []
    for part in parts:
        term = re.sub(r"\s+", " ", part.strip().lower())
        if term:
            cleaned.append(term)
    return list(dict.fromkeys(cleaned))


def boolean_group(text: str) -> str:
    terms = split_terms(text)
    quoted = []
    for term in terms:
        if " " in term and not (term.startswith('"') and term.endswith('"')):
            quoted.append(f'"{term}"')
        else:
            quoted.append(term)
    return "(" + " OR ".join(quoted) + ")" if quoted else ""


def build_search_string(terms: dict | None = None) -> str:
    terms = terms or st.session_state.terms
    groups = [boolean_group(terms.get(field, "")) for field in BOOLEAN_FIELDS]
    groups = [g for g in groups if g]
    return "\nAND\n".join(groups)


def infer_domain(title: str, selected_domain: str = "Otomatis") -> str:
    if selected_domain and selected_domain != "Otomatis":
        return selected_domain
    title_low = title.lower()
    scores = {}
    for domain, profile in DOMAIN_PROFILES.items():
        all_terms = profile["objects"] + profile["interventions"] + profile["outcomes"]
        scores[domain] = sum(1 for term in all_terms if term in title_low)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Peternakan"


def contains_any(text: str, terms: list[str]) -> bool:
    low = (text or "").lower()
    return any(term.lower() in low for term in terms if term)


def make_terms_from_picos(domain: str, population: str, intervention: str, comparator: str, outcome: str, study_design: str) -> dict:
    profile = DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["Peternakan"])
    pop_terms = split_terms(population) or profile["objects"][:4]
    int_terms = split_terms(intervention) or profile["interventions"][:4]
    comp_terms = split_terms(comparator) or ["control", "without treatment", "standard practice"]
    out_terms = split_terms(outcome) or profile["outcomes"][:4]
    study_terms = split_terms(study_design) or ["experimental study", "field trial", "controlled trial", "observational study"]
    return {
        "population_terms": "\n".join(list(dict.fromkeys(pop_terms + profile["objects"][:3]))),
        "intervention_terms": "\n".join(list(dict.fromkeys(int_terms + profile["interventions"][:3]))),
        "comparator_terms": "\n".join(list(dict.fromkeys(comp_terms))),
        "outcome_terms": "\n".join(list(dict.fromkeys(out_terms + profile["outcomes"][:3]))),
        "study_terms": "\n".join(list(dict.fromkeys(study_terms))),
    }


def analyze_title(data: dict) -> dict:
    title = (data.get("working_title") or "").strip()
    domain = infer_domain(title, data.get("domain", "Otomatis"))
    profile = DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["Peternakan"])

    population = (data.get("population") or "").strip()
    intervention = (data.get("intervention") or "").strip()
    comparator = (data.get("comparator") or "").strip()
    outcome = (data.get("outcome") or "").strip()
    study_design = (data.get("study_design") or "").strip()
    framework = data.get("framework", "PICOS")
    year_range = data.get("year_range", "")
    geo = data.get("geographical_scope", "Global")
    target = data.get("target_level", "Q1/Q2")

    title_len = len(title.split())
    has_review_label = bool(re.search(r"systematic review|meta-analysis|meta analysis|systematic map|scoping review", title, re.I))
    has_population = bool(population) or contains_any(title, profile["objects"])
    has_intervention = bool(intervention) or contains_any(title, profile["interventions"])
    has_comparator = bool(comparator) or bool(re.search(r"control|compared|versus|vs\.?|without|conventional|non[- ]", title, re.I))
    has_outcome = bool(outcome) or contains_any(title, profile["outcomes"])
    has_study_design = bool(study_design) or has_review_label
    global_scope = geo.lower() in ["global", "international", "internasional"] or not re.search(r"indonesia|local|lokal|kabupaten|kecamatan", title, re.I)
    too_short = title_len < 8
    too_long = title_len > 30

    sub_scores = {
        "Kejelasan topik": 15 if has_population and has_intervention else 8 if has_population or has_intervention else 3,
        "Kelengkapan PICOS/PECO": sum([has_population, has_intervention, has_comparator, has_outcome, has_study_design]) * 7,
        "Outcome terukur": 15 if has_outcome else 5,
        "Kelayakan meta-analysis": 12 if has_outcome and has_comparator else 6 if has_outcome else 2,
        "Relevansi global": 10 if global_scope else 5,
        "Kerapian judul": 8 if has_review_label and not too_short and not too_long else 4,
    }
    score = min(100, int(sum(sub_scores.values())))

    weaknesses = []
    if not title:
        weaknesses.append("Judul belum diisi.")
    if too_short:
        weaknesses.append("Judul masih terlalu pendek; tambahkan objek, intervensi, outcome, dan jenis review.")
    if too_long:
        weaknesses.append("Judul cukup panjang; padatkan agar lebih mudah dibaca reviewer.")
    if not has_review_label:
        weaknesses.append("Judul belum menyebut jenis naskah, misalnya Systematic Review atau Systematic Review and Meta-Analysis.")
    if not has_population:
        weaknesses.append("Population/problem belum jelas. Sebutkan spesies, komoditas, crop, tanah, atau sistem produksi.")
    if not has_intervention:
        weaknesses.append("Intervention/exposure belum jelas. Sebutkan perlakuan, teknologi, pakan, pupuk, atau pendekatan yang dikaji.")
    if not has_comparator:
        weaknesses.append("Comparator belum eksplisit. Tambahkan control diet, no treatment, conventional practice, atau pembanding lain.")
    if not has_outcome:
        weaknesses.append("Outcome belum terlihat. Tambahkan FCR, body weight gain, yield, soil organic carbon, mortality, nutrient uptake, dan sejenisnya.")
    if not global_scope:
        weaknesses.append("Ruang lingkup masih lokal. Untuk target Q-level, jelaskan kontribusi global atau konteks pembanding internasional.")

    strengths = []
    if has_population:
        strengths.append("Objek/populasi sudah terarah.")
    if has_intervention:
        strengths.append("Intervensi/eksposur sudah dapat dikenali.")
    if has_outcome:
        strengths.append("Outcome sudah mendukung sintesis bukti.")
    if has_review_label:
        strengths.append("Jenis naskah review sudah tercermin pada judul.")
    if has_outcome and has_comparator:
        strengths.append("Topik berpotensi dikembangkan menjadi meta-analysis jika data studi cukup homogen.")

    base_pop = population or "target population/commodity"
    base_int = intervention or "intervention/exposure"
    base_comp = comparator or "control or conventional practice"
    base_out = outcome or "main outcomes"
    base_design = study_design or "experimental/observational studies sesuai kriteria inklusi"
    rq = f"How does {base_int} affect {base_out} in {base_pop} compared with {base_comp}?"

    suggested_titles = [
        f"Effects of {base_int.title()} on {base_out.title()} in {base_pop.title()}: A Systematic Review",
        f"{base_int.title()} for Improving {base_out.title()} in {base_pop.title()}: A Systematic Review and Meta-Analysis",
        f"Evidence on {base_int.title()} Compared with {base_comp.title()} for {base_pop.title()}: A Systematic Review",
    ]

    terms = make_terms_from_picos(domain, base_pop, base_int, base_comp, base_out, base_design)
    search_string = build_search_string(terms)
    inclusion = f"Peer-reviewed empirical studies published within {year_range or 'the predefined year range'}; studies involving {base_pop}; studies evaluating {base_int}; studies reporting {base_out}; articles with sufficient methodological and outcome data for synthesis."
    exclusion = "Narrative reviews, scoping reviews yang tidak memuat data primer, opinion papers, editorials, duplicated records, studies without relevant outcome data, inaccessible full text, and studies outside the predefined scope/language criteria."

    readiness = "Belum siap"
    if score >= 80:
        readiness = "Siap dikembangkan untuk target Q-level"
    elif score >= 60:
        readiness = "Cukup siap, tetapi perlu penguatan metode dan cakupan"
    elif score >= 40:
        readiness = "Perlu revisi besar sebelum layak menjadi systematic review"

    protocol = make_protocol_markdown(
        project={
            "title": title,
            "domain": domain,
            "review_type": "Systematic Review and Meta-Analysis" if "meta" in title.lower() else "Systematic Review",
            "framework": framework,
            "target_level": target,
            "geographical_scope": geo,
            "year_range": year_range,
            "research_question": rq,
            "population": base_pop,
            "intervention": base_int,
            "comparator": base_comp,
            "outcome": base_out,
            "study_design": base_design,
        },
        criteria={"inclusion": inclusion, "exclusion": exclusion},
        terms=terms,
        databases=profile["databases"],
        quality_tool=profile["quality_tool"],
    )

    return {
        "score": score,
        "readiness": readiness,
        "domain": domain,
        "framework": framework,
        "sub_scores": sub_scores,
        "strengths": strengths or ["Belum ada kekuatan utama yang terdeteksi; lengkapi komponen judul dan PICOS/PECO."],
        "weaknesses": weaknesses or ["Tidak ada kelemahan besar yang terdeteksi oleh pemeriksaan otomatis."],
        "suggested_titles": suggested_titles,
        "research_questions": [rq, f"What factors explain variation in the effects of {base_int} on {base_out} across studies involving {base_pop}?", f"What is the quality and strength of evidence for the use of {base_int} in {base_pop}?"],
        "auto_terms": terms,
        "search_string": search_string,
        "recommended_databases": profile["databases"],
        "quality_tool": profile["quality_tool"],
        "inclusion": inclusion,
        "exclusion": exclusion,
        "protocol": protocol,
    }


def apply_analysis_to_workflow(result: dict, analyzer: dict) -> None:
    title = analyzer.get("working_title", "").strip()
    project = st.session_state.project.copy()
    project.update({
        "title": title,
        "domain": result.get("domain", analyzer.get("domain", project.get("domain", ""))),
        "review_type": "Systematic Review and Meta-Analysis" if "meta" in title.lower() else "Systematic Review",
        "framework": analyzer.get("framework", "PICOS"),
        "target_level": analyzer.get("target_level", "Q1/Q2"),
        "geographical_scope": analyzer.get("geographical_scope", "Global"),
        "year_range": analyzer.get("year_range", ""),
        "research_question": result.get("research_questions", [""])[0],
        "population": analyzer.get("population", ""),
        "intervention": analyzer.get("intervention", ""),
        "comparator": analyzer.get("comparator", ""),
        "outcome": analyzer.get("outcome", ""),
        "study_design": analyzer.get("study_design", ""),
    })
    st.session_state.project = project
    st.session_state.criteria = {
        "inclusion": result.get("inclusion", st.session_state.criteria.get("inclusion", "")),
        "exclusion": result.get("exclusion", st.session_state.criteria.get("exclusion", "")),
    }
    st.session_state.terms = result.get("auto_terms", st.session_state.terms)
    st.session_state.databases = result.get("recommended_databases", st.session_state.databases)
    st.session_state.quality_tool = result.get("quality_tool", st.session_state.quality_tool)
    # Re-score existing imported articles using updated PICOS terms.
    if not st.session_state.articles.empty:
        st.session_state.articles = enrich_articles(st.session_state.articles)
    add_log("Analisis judul diterapkan ke protocol, search strategy, database, quality tool, dan screening relevance.")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    rename = {col: col.strip().lower().replace(" ", "_").replace("-", "_") for col in df.columns}
    df = df.rename(columns=rename)
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
    }
    df = df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})
    for col in ARTICLE_COLUMNS:
        if col not in df.columns:
            if col == "duplicate":
                df[col] = False
            elif col == "picos_relevance_score":
                df[col] = 0
            elif col in ["screening_decision", "full_text_decision"]:
                df[col] = "Belum dinilai"
            else:
                df[col] = ""
    df = df[ARTICLE_COLUMNS + [c for c in df.columns if c not in ARTICLE_COLUMNS]]
    if df["id"].astype(str).str.strip().eq("").all():
        df["id"] = [f"A{i+1:03d}" for i in range(len(df))]
    else:
        df["id"] = df["id"].astype(str).replace("nan", "")
        missing = df["id"].astype(str).str.strip().eq("")
        df.loc[missing, "id"] = [f"A{i+1:03d}" for i in range(missing.sum())]
    return df


def parse_ris(text: str) -> pd.DataFrame:
    records = []
    current = {}
    authors = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
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


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    if name.endswith(".ris"):
        return parse_ris(uploaded_file.getvalue().decode("utf-8", errors="ignore"))
    raise ValueError("Format belum didukung. Gunakan CSV, XLSX, atau RIS.")


def flag_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    title_key = df["title"].astype(str).str.lower().str.replace(r"\W+", " ", regex=True).str.strip()
    doi_key = df["doi"].astype(str).str.lower().str.strip()
    dup_title = title_key.duplicated(keep="first") & title_key.ne("")
    dup_doi = doi_key.duplicated(keep="first") & doi_key.ne("")
    df["duplicate"] = (dup_title | dup_doi).fillna(False)
    return df


def relevance_score(row: pd.Series) -> int:
    text = " ".join([str(row.get(c, "")) for c in ["title", "abstract", "species_or_crop", "intervention", "outcome", "study_design"]]).lower()
    terms = st.session_state.terms
    weights = {
        "population_terms": 25,
        "intervention_terms": 25,
        "outcome_terms": 25,
        "comparator_terms": 10,
        "study_terms": 15,
    }
    score = 0
    for field, weight in weights.items():
        field_terms = split_terms(terms.get(field, ""))
        if not field_terms:
            continue
        hits = sum(1 for term in field_terms if term in text)
        if hits:
            score += min(weight, 8 + hits * 6)
    return min(score, 100)


def screening_suggestion(score: int, duplicate: bool) -> str:
    if duplicate:
        return "Exclude - duplicate"
    if score >= 60:
        return "Prioritas Include"
    if score >= 35:
        return "Maybe - cek abstrak"
    return "Kemungkinan Exclude"


def enrich_articles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = flag_duplicates(normalize_columns(df))
    df["picos_relevance_score"] = df.apply(relevance_score, axis=1).astype(int)
    df["screening_suggestion"] = [screening_suggestion(int(s), bool(d)) for s, d in zip(df["picos_relevance_score"], df["duplicate"])]
    return df


def get_screening_pool() -> pd.DataFrame:
    articles = st.session_state.articles
    if articles.empty:
        return articles
    return articles[~articles["duplicate"].fillna(False).astype(bool)]


def get_included_articles() -> pd.DataFrame:
    articles = get_screening_pool()
    if articles.empty:
        return articles
    final = articles[articles["full_text_decision"].eq("Include")]
    if final.empty:
        final = articles[articles["screening_decision"].eq("Include")]
    return final


def sync_downstream() -> None:
    included = get_included_articles()
    if included.empty:
        st.session_state.quality = empty_quality()
        st.session_state.extraction = empty_extraction()
        return

    quality = st.session_state.quality.copy()
    extraction = st.session_state.extraction.copy()
    included_ids = included["id"].astype(str).tolist()

    quality = quality[quality["id"].astype(str).isin(included_ids)] if not quality.empty else empty_quality()
    extraction = extraction[extraction["id"].astype(str).isin(included_ids)] if not extraction.empty else empty_extraction()

    for _, row in included.iterrows():
        aid = str(row.get("id", ""))
        if aid and (quality.empty or aid not in quality["id"].astype(str).values):
            new_row = {col: "" for col in QUALITY_COLUMNS}
            new_row.update({
                "id": aid,
                "title": row.get("title", ""),
                **{col: False for col in QUALITY_BOOL_COLS},
                "quality_score": 0,
                "quality_category": "Belum dinilai",
            })
            quality = pd.concat([quality, pd.DataFrame([new_row])], ignore_index=True)
        if aid and (extraction.empty or aid not in extraction["id"].astype(str).values):
            new_ex = {col: "" for col in EXTRACTION_COLUMNS}
            new_ex.update({
                "id": aid,
                "title": row.get("title", ""),
                "species_or_crop": row.get("species_or_crop", ""),
                "intervention": row.get("intervention", ""),
                "comparator": row.get("comparator", ""),
                "main_outcome": row.get("outcome", ""),
            })
            extraction = pd.concat([extraction, pd.DataFrame([new_ex])], ignore_index=True)

    st.session_state.quality = calculate_quality(quality[QUALITY_COLUMNS])
    st.session_state.extraction = extraction[EXTRACTION_COLUMNS]


def calculate_quality(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    for col in QUALITY_BOOL_COLS:
        if col not in df.columns:
            df[col] = False
        df[col] = df[col].fillna(False).astype(bool)
    df["quality_score"] = df[QUALITY_BOOL_COLS].sum(axis=1)
    df["quality_category"] = pd.cut(df["quality_score"], bins=[-1, 3, 5, 8], labels=["Low", "Moderate", "High"]).astype(str)
    return df


def prisma_counts() -> dict:
    articles = st.session_state.articles
    if st.session_state.use_manual_prisma:
        return st.session_state.prisma_manual
    if articles.empty:
        return {
            "records_database": 0,
            "records_other": 0,
            "duplicates_removed": 0,
            "records_screened": 0,
            "records_excluded_title_abs": 0,
            "full_text_assessed": 0,
            "full_text_excluded": 0,
            "studies_included": 0,
        }
    duplicates = int(articles["duplicate"].sum())
    non_dup = get_screening_pool()
    screen_excluded = int(non_dup["screening_decision"].eq("Exclude").sum())
    full_pool = non_dup[non_dup["screening_decision"].isin(["Include", "Maybe"])]
    full_excluded = int(full_pool["full_text_decision"].eq("Exclude").sum())
    included = int(full_pool["full_text_decision"].eq("Include").sum())
    return {
        "records_database": len(articles),
        "records_other": 0,
        "duplicates_removed": duplicates,
        "records_screened": len(non_dup),
        "records_excluded_title_abs": screen_excluded,
        "full_text_assessed": len(full_pool),
        "full_text_excluded": full_excluded,
        "studies_included": included,
    }


def completion_status() -> dict:
    project = st.session_state.project
    articles = st.session_state.articles
    q = st.session_state.quality
    ex = st.session_state.extraction
    pc = prisma_counts()
    status = {
        "Analisis judul": bool(st.session_state.analyzer_result),
        "Protocol & PICOS": all(str(project.get(k, "")).strip() for k in ["title", "research_question", "population", "intervention", "outcome"]),
        "Search strategy": bool(build_search_string(st.session_state.terms).strip()),
        "Import artikel": not articles.empty,
        "Screening": not articles.empty and articles["screening_decision"].ne("Belum dinilai").any(),
        "PRISMA": pc.get("records_screened", 0) > 0,
        "Quality assessment": not q.empty and q["quality_category"].ne("Belum dinilai").any(),
        "Data extraction": not ex.empty and ex["key_finding"].astype(str).str.strip().ne("").any(),
        "Synthesis export": not articles.empty and pc.get("studies_included", 0) > 0,
    }
    return status


def make_protocol_markdown(project=None, criteria=None, terms=None, databases=None, quality_tool=None) -> str:
    project = project or st.session_state.project
    criteria = criteria or st.session_state.criteria
    terms = terms or st.session_state.terms
    databases = databases or st.session_state.databases
    quality_tool = quality_tool or st.session_state.quality_tool
    search = build_search_string(terms)
    return f"""# Protocol Systematic Review

## Judul
{project.get('title', '')}

## Bidang dan Target
- Bidang: {project.get('domain', '')}
- Jenis review: {project.get('review_type', '')}
- Kerangka: {project.get('framework', '')}
- Target publikasi: {project.get('target_level', '')}
- Cakupan geografis: {project.get('geographical_scope', '')}
- Rentang tahun artikel: {project.get('year_range', '')}

## Pertanyaan Penelitian
{project.get('research_question', '')}

## PICOS/PECO
- Population/Problem: {project.get('population', '')}
- Intervention/Exposure: {project.get('intervention', '')}
- Comparator: {project.get('comparator', '')}
- Outcome: {project.get('outcome', '')}
- Study Design: {project.get('study_design', '')}

## Database yang Digunakan/Disarankan
{', '.join(databases)}

## Kriteria Inklusi
{criteria.get('inclusion', '')}

## Kriteria Eksklusi
{criteria.get('exclusion', '')}

## Search String Utama
```text
{search}
```

## Rencana Screening
Seluruh artikel yang diimpor akan dinilai berdasarkan relevansi PICOS/PECO, status duplikasi, kesesuaian judul/abstrak, dan penilaian full text. Alasan eksklusi dicatat agar alur PRISMA dapat ditelusuri.

## Quality Assessment
{quality_tool}

## Rencana Data Extraction
Data yang diekstraksi meliputi identitas artikel, desain studi, komoditas/spesies, intervensi, pembanding, sampel, durasi, outcome utama, arah efek, ukuran efek, nilai signifikansi, temuan utama, dan catatan metodologis.

## Rencana Sintesis
Sintesis dilakukan secara naratif dengan membandingkan pola outcome, arah efek, kualitas studi, desain penelitian, dan gap riset. Meta-analysis dapat dipertimbangkan jika outcome, satuan data, dan desain studi cukup homogen.
"""


def make_methods_template() -> str:
    p = st.session_state.project
    counts = prisma_counts()
    search = build_search_string(st.session_state.terms)
    return f"""# Draft Methods Section

This systematic review was designed to answer the following question: {p.get('research_question', '')}. The review used the {p.get('framework', 'PICOS')} framework. The population/problem was {p.get('population', '')}, the intervention/exposure was {p.get('intervention', '')}, the comparator was {p.get('comparator', '')}, and the main outcomes were {p.get('outcome', '')}.

A structured search strategy was developed from the integrated protocol and applied to the selected bibliographic databases: {', '.join(st.session_state.databases)}. The main Boolean search string was:

```text
{search}
```

Records were imported into the screening system and duplicate records were identified using DOI and normalized article titles. The current review file contains {counts.get('records_database', 0)} database records, with {counts.get('duplicates_removed', 0)} duplicates removed. A total of {counts.get('records_screened', 0)} records proceeded to title and abstract screening, and {counts.get('full_text_assessed', 0)} records were assessed at full-text stage. The current final synthesis includes {counts.get('studies_included', 0)} studies.

Data extraction covered bibliographic information, country, study design, species/crop, intervention, comparator, sample size, duration, outcomes, effect direction, effect size, significance level, and key findings. Study quality was assessed using the selected appraisal approach: {st.session_state.quality_tool}. Evidence was synthesized narratively by comparing direction of effect, consistency across studies, methodological quality, and research gaps. Quantitative meta-analysis can be added when effect sizes and outcome units are sufficiently comparable.
"""


def make_synthesis_markdown() -> str:
    p = st.session_state.project
    articles = st.session_state.articles
    quality = st.session_state.quality
    extraction = st.session_state.extraction
    counts = prisma_counts()
    if extraction.empty:
        effect_text = "Arah efek belum dapat disimpulkan karena data extraction belum lengkap."
    else:
        effects = extraction["effect_direction"].replace("", np.nan).dropna().value_counts().to_dict()
        effect_text = "; ".join([f"{k}: {v}" for k, v in effects.items()]) if effects else "Arah efek belum diisi."
    if quality.empty:
        quality_text = "Quality assessment belum tersedia."
    else:
        q = quality["quality_category"].replace("", np.nan).dropna().value_counts().to_dict()
        quality_text = "; ".join([f"{k}: {v}" for k, v in q.items()]) if q else "Quality assessment belum lengkap."
    return f"""# Integrated Synthesis Summary

## Fokus Review
{p.get('title', '')}

Pertanyaan penelitian: {p.get('research_question', '')}

## Ringkasan PRISMA
- Records identified from databases: {counts.get('records_database', 0)}
- Duplicates removed: {counts.get('duplicates_removed', 0)}
- Records screened: {counts.get('records_screened', 0)}
- Records excluded at title/abstract: {counts.get('records_excluded_title_abs', 0)}
- Full-text assessed: {counts.get('full_text_assessed', 0)}
- Full-text excluded: {counts.get('full_text_excluded', 0)}
- Studies included: {counts.get('studies_included', 0)}

## Pola Arah Efek
{effect_text}

## Kualitas Studi
{quality_text}

## Narasi Sintesis Awal
Berdasarkan data yang telah diimpor, proses sintesis perlu difokuskan pada hubungan antara {p.get('intervention', '')} dan {p.get('outcome', '')} pada {p.get('population', '')}. Perbedaan desain studi, durasi perlakuan, karakteristik sampel, serta kualitas pelaporan perlu dibahas sebagai faktor yang dapat menjelaskan variasi hasil antarstudi.

## Gap Riset Awal
Gap riset dapat diidentifikasi dari outcome yang belum konsisten, keterbatasan desain studi, kualitas metodologi rendah/sedang, serta kurangnya pelaporan ukuran efek yang dapat digunakan untuk meta-analysis.
"""


def export_project_json() -> str:
    payload = {
        "app_version": APP_VERSION,
        "analyzer": st.session_state.analyzer,
        "analyzer_result": st.session_state.analyzer_result,
        "project": st.session_state.project,
        "criteria": st.session_state.criteria,
        "terms": st.session_state.terms,
        "databases": st.session_state.databases,
        "quality_tool": st.session_state.quality_tool,
        "prisma_manual": st.session_state.prisma_manual,
        "use_manual_prisma": st.session_state.use_manual_prisma,
        "articles": st.session_state.articles.to_dict(orient="records"),
        "quality": st.session_state.quality.to_dict(orient="records"),
        "extraction": st.session_state.extraction.to_dict(orient="records"),
        "workflow_log": st.session_state.workflow_log,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def import_project_json(uploaded_file) -> None:
    payload = json.loads(uploaded_file.getvalue().decode("utf-8"))
    for key in ["analyzer", "analyzer_result", "project", "criteria", "terms", "databases", "quality_tool", "prisma_manual", "use_manual_prisma", "workflow_log"]:
        if key in payload:
            st.session_state[key] = payload[key]
    st.session_state.articles = normalize_columns(pd.DataFrame(payload.get("articles", []))) if payload.get("articles") else empty_articles()
    st.session_state.quality = calculate_quality(pd.DataFrame(payload.get("quality", []))) if payload.get("quality") else empty_quality()
    st.session_state.extraction = pd.DataFrame(payload.get("extraction", [])) if payload.get("extraction") else empty_extraction()
    for col in QUALITY_COLUMNS:
        if col not in st.session_state.quality.columns:
            st.session_state.quality[col] = "" if col not in QUALITY_BOOL_COLS else False
    for col in EXTRACTION_COLUMNS:
        if col not in st.session_state.extraction.columns:
            st.session_state.extraction[col] = ""
    st.session_state.quality = st.session_state.quality[QUALITY_COLUMNS]
    st.session_state.extraction = st.session_state.extraction[EXTRACTION_COLUMNS]
    add_log("Project JSON dimuat kembali ke workflow.")


def download_df(label: str, df: pd.DataFrame, filename: str) -> None:
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), filename, "text/csv", use_container_width=True)


def page_header(title: str, subtitle: str | None = None) -> None:
    st.header(title)
    if subtitle:
        st.caption(subtitle)


def sidebar_workflow() -> None:
    st.sidebar.title("Navigasi")
    status = completion_status()
    done = sum(status.values())
    total = len(status)
    st.sidebar.progress(done / total if total else 0)
    st.sidebar.caption(f"Integrasi workflow: {done}/{total} tahap aktif")
    for name, ok in status.items():
        st.sidebar.write(("✅ " if ok else "⬜ ") + name)
    st.sidebar.markdown("---")
    if st.sidebar.button("Sinkronkan semua modul", use_container_width=True):
        st.session_state.articles = enrich_articles(st.session_state.articles)
        sync_downstream()
        add_log("Semua modul disinkronkan manual.")
        st.rerun()


def page_dashboard() -> None:
    st.title(f"🌾 {APP_TITLE}")
    st.caption("Sistem systematic review yang terintegrasi dari judul → protocol → search → screening → PRISMA → quality → extraction → synthesis.")

    sync_downstream()
    counts = prisma_counts()
    articles = st.session_state.articles
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Artikel", len(articles))
    col2.metric("Duplikasi", counts.get("duplicates_removed", 0))
    col3.metric("Screened", counts.get("records_screened", 0))
    col4.metric("Full-text", counts.get("full_text_assessed", 0))
    col5.metric("Included", counts.get("studies_included", 0))

    st.subheader("Ringkasan Proyek Terpadu")
    p = st.session_state.project
    st.markdown(f"**Judul:** {p.get('title', '')}")
    st.markdown(f"**Research question:** {p.get('research_question', '')}")
    c1, c2, c3 = st.columns(3)
    c1.info(f"**P:** {p.get('population', '-')}")
    c2.info(f"**I/E:** {p.get('intervention', '-')}")
    c3.info(f"**O:** {p.get('outcome', '-')}")

    st.subheader("Alur Terintegrasi")
    st.markdown(
        """
        1. **Title Analyzer** menilai judul dan otomatis mengisi PICOS/PECO.  
        2. **Protocol & PICOS** menjadi pusat data penelitian. Setiap perubahan dapat memperbarui search terms.  
        3. **Search Strategy** memakai komponen protocol untuk membuat Boolean search dan rekomendasi database.  
        4. **Import & Screening** menghitung relevansi artikel berdasarkan terms dari protocol/search.  
        5. **PRISMA Flow** mengambil angka otomatis dari hasil screening.  
        6. **Quality Assessment** dan **Data Extraction** otomatis hanya mengambil artikel yang sudah included.  
        7. **Synthesis & Export** menarik semua data dari modul sebelumnya menjadi protocol, methods, synthesis, dan paket ZIP.
        """
    )

    if st.session_state.workflow_log:
        st.subheader("Log Integrasi")
        for item in reversed(st.session_state.workflow_log[-6:]):
            st.write(f"- {item['date']}: {item['message']}")

    st.subheader("Simpan / Muat Project")
    c1, c2 = st.columns(2)
    c1.download_button("Download project_state.json", export_project_json().encode("utf-8"), "project_state.json", "application/json", use_container_width=True)
    uploaded_state = c2.file_uploader("Muat project_state.json", type=["json"], key="load_project_json")
    if uploaded_state is not None and c2.button("Terapkan project JSON", use_container_width=True):
        import_project_json(uploaded_state)
        st.success("Project berhasil dimuat.")
        st.rerun()


def page_title_analyzer() -> None:
    page_header("0. Title & Protocol Analyzer", "Hasil dari halaman ini mengisi protocol, terms, database, quality tool, dan scoring artikel.")
    analyzer = st.session_state.analyzer.copy()
    with st.form("title_form"):
        analyzer["working_title"] = st.text_area("Judul sementara", value=analyzer.get("working_title", ""), height=90)
        cols = st.columns(4)
        domains = ["Otomatis"] + list(DOMAIN_PROFILES.keys())
        current_domain = analyzer.get("domain", "Peternakan")
        analyzer["domain"] = cols[0].selectbox("Bidang", domains, index=domains.index(current_domain) if current_domain in domains else 0)
        frameworks = ["PICOS", "PECO", "PICO"]
        analyzer["framework"] = cols[1].selectbox("Kerangka", frameworks, index=frameworks.index(analyzer.get("framework", "PICOS")) if analyzer.get("framework", "PICOS") in frameworks else 0)
        targets = ["Q1/Q2", "Q2/Q3", "Sinta/Scopus awal", "Internal/Kampus"]
        analyzer["target_level"] = cols[2].selectbox("Target", targets, index=targets.index(analyzer.get("target_level", "Q1/Q2")) if analyzer.get("target_level", "Q1/Q2") in targets else 0)
        scopes = ["Global", "Asia", "Indonesia", "Lokal/Daerah"]
        analyzer["geographical_scope"] = cols[3].selectbox("Cakupan", scopes, index=scopes.index(analyzer.get("geographical_scope", "Global")) if analyzer.get("geographical_scope", "Global") in scopes else 0)

        st.subheader("Komponen inti")
        c1, c2 = st.columns(2)
        analyzer["population"] = c1.text_input("Population / Problem", value=analyzer.get("population", ""))
        analyzer["intervention"] = c2.text_input("Intervention / Exposure", value=analyzer.get("intervention", ""))
        analyzer["comparator"] = c1.text_input("Comparator", value=analyzer.get("comparator", ""))
        analyzer["outcome"] = c2.text_input("Outcome", value=analyzer.get("outcome", ""))
        analyzer["study_design"] = c1.text_input("Study design", value=analyzer.get("study_design", ""))
        analyzer["year_range"] = c2.text_input("Rentang tahun artikel", value=analyzer.get("year_range", "2015-2026"))
        submitted = st.form_submit_button("Analisis dan sinkronkan ke seluruh workflow", use_container_width=True)

    if submitted:
        result = analyze_title(analyzer)
        st.session_state.analyzer = analyzer
        st.session_state.analyzer_result = result
        apply_analysis_to_workflow(result, analyzer)
        st.success("Analisis selesai dan sudah disinkronkan ke protocol, search strategy, database, quality assessment, serta relevansi screening.")

    if not st.session_state.analyzer_result:
        st.session_state.analyzer_result = analyze_title(st.session_state.analyzer)
    result = st.session_state.analyzer_result

    st.subheader("Skor dan Diagnosis")
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
        st.subheader("Kelemahan")
        for item in result.get("weaknesses", []):
            st.warning(item)

    st.subheader("Rekomendasi Judul")
    selected_title = st.radio("Pilih judul untuk diterapkan ke protocol", result.get("suggested_titles", []), index=0 if result.get("suggested_titles") else None)
    if st.button("Terapkan judul rekomendasi terpilih", use_container_width=True):
        st.session_state.analyzer["working_title"] = selected_title
        st.session_state.project["title"] = selected_title
        add_log("Judul rekomendasi diterapkan ke protocol.")
        st.success("Judul rekomendasi sudah diterapkan.")
        st.rerun()

    st.subheader("Research Question & Boolean Search")
    st.write(result.get("research_questions", [""])[0])
    st.code(result.get("search_string", ""), language="text")

    with st.expander("Lihat draft protocol otomatis"):
        st.markdown(result.get("protocol", ""))
    st.download_button("Download hasil_analisis_judul.json", json.dumps(result, indent=2, ensure_ascii=False).encode("utf-8"), "hasil_analisis_judul.json", "application/json", use_container_width=True)


def page_protocol() -> None:
    page_header("1. Protocol & PICOS", "Pusat data review. Perubahan di sini dapat memperbarui search terms dan scoring artikel.")
    p = st.session_state.project.copy()
    c = st.session_state.criteria.copy()
    with st.form("protocol_form"):
        p["title"] = st.text_input("Judul review", value=p.get("title", ""))
        cols = st.columns(4)
        p["domain"] = cols[0].selectbox("Domain", list(DOMAIN_PROFILES.keys()), index=list(DOMAIN_PROFILES.keys()).index(p.get("domain", "Peternakan")) if p.get("domain") in DOMAIN_PROFILES else 0)
        p["review_type"] = cols[1].selectbox("Jenis review", ["Systematic Review", "Systematic Review and Meta-Analysis", "Systematic Map", "Scoping Review"], index=["Systematic Review", "Systematic Review and Meta-Analysis", "Systematic Map", "Scoping Review"].index(p.get("review_type", "Systematic Review")) if p.get("review_type") in ["Systematic Review", "Systematic Review and Meta-Analysis", "Systematic Map", "Scoping Review"] else 0)
        p["framework"] = cols[2].selectbox("Kerangka", ["PICOS", "PECO", "PICO"], index=["PICOS", "PECO", "PICO"].index(p.get("framework", "PICOS")) if p.get("framework") in ["PICOS", "PECO", "PICO"] else 0)
        p["target_level"] = cols[3].selectbox("Target", ["Q1/Q2", "Q2/Q3", "Sinta/Scopus awal", "Internal/Kampus"], index=["Q1/Q2", "Q2/Q3", "Sinta/Scopus awal", "Internal/Kampus"].index(p.get("target_level", "Q1/Q2")) if p.get("target_level") in ["Q1/Q2", "Q2/Q3", "Sinta/Scopus awal", "Internal/Kampus"] else 0)
        p["research_question"] = st.text_area("Research question", value=p.get("research_question", ""), height=75)
        c1, c2 = st.columns(2)
        p["population"] = c1.text_input("Population / Problem", value=p.get("population", ""))
        p["intervention"] = c2.text_input("Intervention / Exposure", value=p.get("intervention", ""))
        p["comparator"] = c1.text_input("Comparator", value=p.get("comparator", ""))
        p["outcome"] = c2.text_input("Outcome", value=p.get("outcome", ""))
        p["study_design"] = c1.text_input("Study design", value=p.get("study_design", ""))
        p["year_range"] = c2.text_input("Rentang tahun", value=p.get("year_range", ""))
        c["inclusion"] = st.text_area("Kriteria inklusi", value=c.get("inclusion", ""), height=100)
        c["exclusion"] = st.text_area("Kriteria eksklusi", value=c.get("exclusion", ""), height=100)
        sync_terms = st.checkbox("Perbarui search terms otomatis dari PICOS/PECO", value=True)
        submitted = st.form_submit_button("Simpan protocol dan sinkronkan", use_container_width=True)

    if submitted:
        st.session_state.project = p
        st.session_state.criteria = c
        profile = DOMAIN_PROFILES.get(p["domain"], DOMAIN_PROFILES["Peternakan"])
        st.session_state.databases = profile["databases"]
        st.session_state.quality_tool = profile["quality_tool"]
        if sync_terms:
            st.session_state.terms = make_terms_from_picos(p["domain"], p["population"], p["intervention"], p["comparator"], p["outcome"], p["study_design"])
            st.session_state.articles = enrich_articles(st.session_state.articles)
        sync_downstream()
        add_log("Protocol disimpan dan disinkronkan dengan search, database, quality tool, dan artikel.")
        st.success("Protocol tersimpan dan modul terkait sudah diperbarui.")

    st.subheader("Preview Protocol Terintegrasi")
    protocol = make_protocol_markdown()
    st.download_button("Download protocol_systematic_review.md", protocol.encode("utf-8"), "protocol_systematic_review.md", "text/markdown", use_container_width=True)
    st.markdown(protocol)


def page_search_strategy() -> None:
    page_header("2. Search Strategy", "Boolean search berasal dari PICOS/PECO dan dipakai untuk scoring relevansi artikel pada tahap screening.")
    p = st.session_state.project
    st.info(f"Saat ini search strategy terhubung dengan topik: **{p.get('title', '')}**")

    c1, c2 = st.columns(2)
    terms = st.session_state.terms.copy()
    with st.form("search_form"):
        terms["population_terms"] = c1.text_area("Population terms", value=terms.get("population_terms", ""), height=130)
        terms["intervention_terms"] = c2.text_area("Intervention/Exposure terms", value=terms.get("intervention_terms", ""), height=130)
        terms["comparator_terms"] = c1.text_area("Comparator terms", value=terms.get("comparator_terms", ""), height=110)
        terms["outcome_terms"] = c2.text_area("Outcome terms", value=terms.get("outcome_terms", ""), height=110)
        terms["study_terms"] = st.text_area("Study design terms", value=terms.get("study_terms", ""), height=90)
        submitted = st.form_submit_button("Simpan search terms dan update scoring artikel", use_container_width=True)
    if submitted:
        st.session_state.terms = terms
        st.session_state.articles = enrich_articles(st.session_state.articles)
        add_log("Search terms diperbarui dan skor relevansi artikel dihitung ulang.")
        st.success("Search terms tersimpan. Artikel yang sudah diimpor ikut dihitung ulang relevansinya.")

    st.subheader("Boolean Search Utama")
    search = build_search_string(st.session_state.terms)
    st.code(search, language="text")
    st.download_button("Download boolean_search.txt", search.encode("utf-8"), "boolean_search.txt", "text/plain", use_container_width=True)

    st.subheader("Database yang Disarankan")
    selected = st.multiselect("Pilih database final", options=sorted(set(sum([v["databases"] for v in DOMAIN_PROFILES.values()], []))), default=st.session_state.databases)
    if st.button("Simpan database final", use_container_width=True):
        st.session_state.databases = selected
        add_log("Database final diperbarui.")
        st.success("Database final tersimpan dan akan masuk ke protocol/methods.")

    st.subheader("Search Log Template")
    search_log = pd.DataFrame({
        "database": st.session_state.databases,
        "search_string": [search] * len(st.session_state.databases),
        "date_searched": [str(date.today())] * len(st.session_state.databases),
        "filters": [f"Year: {p.get('year_range', '')}; Document type: article; Language: English/Indonesian"] * len(st.session_state.databases),
        "records_found": [""] * len(st.session_state.databases),
    })
    st.dataframe(search_log, use_container_width=True)
    download_df("Download search_log_template.csv", search_log, "search_log_template.csv")


def page_import_screening() -> None:
    page_header("3. Import & Screening", "Artikel yang diimpor otomatis diberi skor relevansi berdasarkan search terms dari protocol.")
    uploaded = st.file_uploader("Upload file bibliografi", type=["csv", "xlsx", "xls", "ris"])
    c1, c2, c3 = st.columns(3)
    if uploaded is not None:
        try:
            raw = read_uploaded_file(uploaded)
            df = enrich_articles(raw)
            st.write("Preview data yang akan ditambahkan:")
            st.dataframe(df.head(10), use_container_width=True)
            if c1.button("Tambahkan ke screening", use_container_width=True):
                combined = df if st.session_state.articles.empty else pd.concat([st.session_state.articles, df], ignore_index=True)
                combined["id"] = [f"A{i+1:03d}" for i in range(len(combined))]
                st.session_state.articles = enrich_articles(combined)
                sync_downstream()
                add_log(f"{len(df)} artikel ditambahkan ke screening.")
                st.success(f"Berhasil menambahkan {len(df)} artikel.")
                st.rerun()
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

    if c2.button("Gunakan data contoh", use_container_width=True):
        paths = [Path("data/sample_articles.csv"), Path(__file__).parent / "data" / "sample_articles.csv"]
        sample = None
        for path in paths:
            if path.exists():
                sample = pd.read_csv(path)
                break
        if sample is None:
            st.error("File data contoh tidak ditemukan.")
        else:
            st.session_state.articles = enrich_articles(sample)
            sync_downstream()
            add_log("Data contoh dimuat dan dihitung relevansinya.")
            st.success("Data contoh dimuat.")
            st.rerun()

    if c3.button("Hapus semua data artikel", use_container_width=True):
        st.session_state.articles = empty_articles()
        st.session_state.quality = empty_quality()
        st.session_state.extraction = empty_extraction()
        add_log("Semua data artikel, quality, dan extraction dihapus.")
        st.rerun()

    articles = st.session_state.articles
    if articles.empty:
        st.warning("Belum ada artikel. Import file bibliografi terlebih dahulu.")
        return

    st.subheader("Ringkasan Relevansi Otomatis")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", len(articles))
    m2.metric("Duplikasi", int(articles["duplicate"].sum()))
    m3.metric("Skor ≥ 60", int((articles["picos_relevance_score"] >= 60).sum()))
    m4.metric("Belum dinilai", int(articles["screening_decision"].eq("Belum dinilai").sum()))

    st.subheader("Screening Table Terintegrasi")
    edited = st.data_editor(
        articles,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "duplicate": st.column_config.CheckboxColumn("Duplicate"),
            "picos_relevance_score": st.column_config.ProgressColumn("PICOS relevance", min_value=0, max_value=100),
            "screening_decision": st.column_config.SelectboxColumn("Title/abstract decision", options=["Belum dinilai", "Include", "Exclude", "Maybe"]),
            "full_text_decision": st.column_config.SelectboxColumn("Full-text decision", options=["Belum dinilai", "Include", "Exclude", "Maybe"]),
            "abstract": st.column_config.TextColumn("Abstract", width="large"),
            "exclusion_reason": st.column_config.TextColumn("Exclusion reason", width="medium"),
            "full_text_exclusion_reason": st.column_config.TextColumn("Full-text exclusion reason", width="medium"),
        },
        key="articles_editor",
    )
    st.session_state.articles = normalize_columns(edited)

    c4, c5, c6 = st.columns(3)
    if c4.button("Terapkan saran otomatis ke keputusan awal", use_container_width=True):
        df = st.session_state.articles.copy()
        mask = df["screening_decision"].eq("Belum dinilai")
        df.loc[mask & df["duplicate"].astype(bool), "screening_decision"] = "Exclude"
        df.loc[mask & ~df["duplicate"].astype(bool) & (df["picos_relevance_score"] >= 60), "screening_decision"] = "Include"
        df.loc[mask & ~df["duplicate"].astype(bool) & df["picos_relevance_score"].between(35, 59), "screening_decision"] = "Maybe"
        df.loc[mask & ~df["duplicate"].astype(bool) & (df["picos_relevance_score"] < 35), "screening_decision"] = "Exclude"
        st.session_state.articles = df
        sync_downstream()
        add_log("Saran otomatis diterapkan pada keputusan screening awal.")
        st.rerun()
    if c5.button("Hitung ulang duplikasi & relevansi", use_container_width=True):
        st.session_state.articles = enrich_articles(st.session_state.articles)
        sync_downstream()
        add_log("Duplikasi dan relevance scoring dihitung ulang.")
        st.rerun()
    if c6.button("Sinkronkan included ke quality/extraction", use_container_width=True):
        sync_downstream()
        add_log("Artikel included disinkronkan ke quality assessment dan extraction.")
        st.success("Data downstream sudah disinkronkan.")

    download_df("Download screening_results.csv", st.session_state.articles, "screening_results.csv")


def page_prisma() -> None:
    page_header("4. PRISMA Flow", "Jumlah PRISMA otomatis ditarik dari screening. Manual hanya dipakai bila data berasal dari sumber lain.")
    st.session_state.use_manual_prisma = st.toggle("Gunakan jumlah manual", value=st.session_state.use_manual_prisma)
    if st.session_state.use_manual_prisma:
        counts = st.session_state.prisma_manual.copy()
        cols = st.columns(4)
        for i, key in enumerate(counts.keys()):
            counts[key] = cols[i % 4].number_input(key.replace("_", " ").title(), min_value=0, value=int(counts.get(key, 0)))
        st.session_state.prisma_manual = counts
    else:
        counts = prisma_counts()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records identified", counts.get("records_database", 0) + counts.get("records_other", 0))
    c2.metric("Duplicates removed", counts.get("duplicates_removed", 0))
    c3.metric("Full-text assessed", counts.get("full_text_assessed", 0))
    c4.metric("Studies included", counts.get("studies_included", 0))

    st.subheader("PRISMA Text Flow")
    flow = f"""
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
"""
    st.code(flow, language="text")
    st.download_button("Download prisma_flow.txt", flow.encode("utf-8"), "prisma_flow.txt", "text/plain", use_container_width=True)
    download_df("Download prisma_counts.csv", pd.DataFrame([counts]), "prisma_counts.csv")

    articles = st.session_state.articles
    if not articles.empty:
        st.subheader("Alasan Eksklusi")
        reasons = []
        for col in ["exclusion_reason", "full_text_exclusion_reason"]:
            reasons.extend(articles[col].replace("", np.nan).dropna().tolist())
        if reasons:
            st.bar_chart(pd.Series(reasons).value_counts())
        else:
            st.caption("Belum ada alasan eksklusi yang diisi.")


def page_quality() -> None:
    page_header("5. Quality Assessment", "Tabel otomatis hanya berisi artikel yang sudah included dari screening/full-text.")
    sync_downstream()
    included = get_included_articles()
    if included.empty:
        st.warning("Belum ada artikel included. Tandai artikel sebagai Include pada screening/full-text terlebih dahulu.")
        return
    st.info(f"Quality assessment terhubung dengan {len(included)} artikel included. Tool disarankan: {st.session_state.quality_tool}")
    quality = calculate_quality(st.session_state.quality)
    edited = st.data_editor(
        quality,
        use_container_width=True,
        num_rows="dynamic",
        disabled=["quality_score", "quality_category"],
        column_config={col: st.column_config.CheckboxColumn(col.replace("_", " ").title()) for col in QUALITY_BOOL_COLS},
        key="quality_editor",
    )
    st.session_state.quality = calculate_quality(edited)
    st.subheader("Ringkasan Kualitas")
    if not st.session_state.quality.empty:
        st.bar_chart(st.session_state.quality["quality_category"].value_counts())
    download_df("Download quality_assessment.csv", st.session_state.quality, "quality_assessment.csv")


def page_extraction() -> None:
    page_header("6. Data Extraction", "Tabel otomatis mengikuti artikel included dan menarik data awal dari screening.")
    sync_downstream()
    if st.session_state.extraction.empty:
        st.warning("Belum ada artikel included untuk diekstraksi.")
        return
    edited = st.data_editor(
        st.session_state.extraction,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "effect_direction": st.column_config.SelectboxColumn("Effect direction", options=["", "Positive", "Negative", "No effect", "Mixed"]),
            "key_finding": st.column_config.TextColumn("Key finding", width="large"),
            "remarks": st.column_config.TextColumn("Remarks", width="large"),
        },
        key="extraction_editor",
    )
    st.session_state.extraction = edited

    st.subheader("Ringkasan Data Extraction")
    effects = edited["effect_direction"].replace("", np.nan).dropna().value_counts()
    if not effects.empty:
        st.bar_chart(effects)
    download_df("Download data_extraction.csv", st.session_state.extraction, "data_extraction.csv")


def make_export_zip() -> bytes:
    files = {
        "protocol_systematic_review.md": make_protocol_markdown(),
        "methods_template.md": make_methods_template(),
        "synthesis_summary.md": make_synthesis_markdown(),
        "project_state.json": export_project_json(),
        "boolean_search.txt": build_search_string(st.session_state.terms),
        "prisma_counts.csv": pd.DataFrame([prisma_counts()]).to_csv(index=False),
        "screening_results.csv": st.session_state.articles.to_csv(index=False),
        "quality_assessment.csv": st.session_state.quality.to_csv(index=False),
        "data_extraction.csv": st.session_state.extraction.to_csv(index=False),
    }
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    buffer.seek(0)
    return buffer.getvalue()


def page_synthesis() -> None:
    page_header("7. Synthesis & Export", "Semua output diambil dari modul sebelumnya sehingga tidak berdiri sendiri.")
    sync_downstream()
    counts = prisma_counts()
    articles = st.session_state.articles
    quality = st.session_state.quality
    extraction = st.session_state.extraction

    if articles.empty:
        st.warning("Belum ada data untuk disintesis.")
        return

    st.subheader("Visual Ringkas")
    c1, c2 = st.columns(2)
    years = pd.to_numeric(articles["year"], errors="coerce").dropna().astype(int) if "year" in articles else pd.Series(dtype=int)
    if not years.empty:
        c1.write("Distribusi tahun publikasi")
        c1.bar_chart(years.value_counts().sort_index())
    countries = articles["country"].replace("", np.nan).dropna().value_counts().head(15) if "country" in articles else pd.Series(dtype=int)
    if not countries.empty:
        c2.write("Distribusi negara")
        c2.bar_chart(countries)

    c3, c4 = st.columns(2)
    if not extraction.empty:
        effects = extraction["effect_direction"].replace("", np.nan).dropna().value_counts()
        if not effects.empty:
            c3.write("Arah efek intervensi")
            c3.bar_chart(effects)
    if not quality.empty:
        q = quality["quality_category"].replace("", np.nan).dropna().value_counts()
        if not q.empty:
            c4.write("Kategori kualitas studi")
            c4.bar_chart(q)

    st.subheader("Integrated Auto Summary")
    summary = make_synthesis_markdown()
    st.markdown(summary)

    st.subheader("Export Paket Naskah")
    c5, c6, c7 = st.columns(3)
    c5.download_button("Download protocol.md", make_protocol_markdown().encode("utf-8"), "protocol_systematic_review.md", "text/markdown", use_container_width=True)
    c6.download_button("Download methods.md", make_methods_template().encode("utf-8"), "methods_template.md", "text/markdown", use_container_width=True)
    c7.download_button("Download synthesis.md", summary.encode("utf-8"), "synthesis_summary.md", "text/markdown", use_container_width=True)

    st.download_button("Download semua output sebagai ZIP", make_export_zip(), "systematic_review_outputs.zip", "application/zip", use_container_width=True)


def main() -> None:
    init_state()
    sidebar_workflow()
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
    st.sidebar.caption("Versi 2.0: setiap modul saling terhubung melalui state project terpadu.")

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
