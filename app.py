import json
import re
import zipfile
from datetime import date, datetime

import requests
from io import BytesIO

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Agro & Biosystems Systematic Review Builder",
    page_icon="🌾",
    layout="wide",
)

APP_TITLE = "Agro & Biosystems Systematic Review Builder"
APP_VERSION = "Q-Level Manuscript Builder + Save & Resume + SlashAI Chat Completions + AI Usage Guidance"
SLASHAI_DEFAULT_API_BASE = "https://api.slashai.my.id"
SLASHAI_DEFAULT_CHAT_COMPLETIONS_ENDPOINT = "https://api.slashai.my.id/v1/chat/completions"

ARTICLE_COLUMNS = [
    "id", "title", "authors", "year", "journal", "doi", "country", "study_design",
    "species_or_crop", "intervention", "comparator", "outcome", "abstract", "source_database",
    "duplicate", "picos_relevance_score", "auto_screening_suggestion",
    "reviewer1_decision", "reviewer2_decision", "screening_conflict", "consensus_decision",
    "screening_decision", "exclusion_reason", "full_text_decision", "full_text_exclusion_reason", "notes"
]

QUALITY_COLUMNS = [
    "id", "title", "clear_objective", "appropriate_design", "adequate_sample",
    "clear_intervention", "valid_outcome", "adequate_statistics", "bias_control",
    "complete_reporting", "selection_bias", "performance_bias", "detection_bias",
    "attrition_bias", "reporting_bias", "other_bias", "quality_score", "quality_category",
    "overall_risk_of_bias", "grade_downgrade_reason", "certainty_of_evidence", "risk_of_bias_note"
]

EXTRACTION_COLUMNS = [
    "id", "title", "species_or_crop", "intervention", "comparator", "sample_size",
    "duration", "main_outcome", "outcome_unit", "mean_intervention", "sd_intervention",
    "n_intervention", "mean_control", "sd_control", "n_control", "effect_direction",
    "effect_size", "p_value", "key_finding", "limitations", "implication", "novelty_note"
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
    "Teknik Pertanian dan Biosistem": {
        "objects": ["agricultural machinery", "farm machinery", "irrigation", "greenhouse", "postharvest", "drying", "sensor", "iot", "remote sensing", "precision agriculture", "biosystem", "agricultural system", "smallholder farm", "soil", "crop"],
        "interventions": ["smart irrigation", "automated irrigation", "precision agriculture", "mechanization", "controlled traffic", "dryer", "solar dryer", "greenhouse technology", "sensor", "iot", "drone", "remote sensing", "decision support", "renewable energy"],
        "outcomes": ["water use efficiency", "crop yield", "energy efficiency", "labor productivity", "drying rate", "product quality", "soil compaction", "irrigation efficiency", "system performance", "cost", "adoption", "emission"],
        "databases": ["Scopus", "Web of Science", "CAB Abstracts", "AGRICOLA", "ASABE Technical Library", "ScienceDirect", "IEEE Xplore", "SpringerLink", "Taylor & Francis"],
        "quality_tool": "ROSES/CEE critical appraisal untuk evidence synthesis teknik-lingkungan, JBI adapted checklist untuk studi observasional, serta checklist rekayasa untuk validasi alat, uji performa, eksperimen lapang, simulasi-model, dan sensor/IoT."
    },
}

GENERIC_TERMS = ["review", "study", "analysis", "effect", "impact", "influence", "pengaruh", "analisis", "kajian", "systematic"]


FRAMEWORK_GUIDES = {
    "PICO": {
        "name": "PICO",
        "focus": "Intervensi/perlakuan tanpa penekanan eksplisit pada desain studi.",
        "best_for": "Cocok untuk pertanyaan efektivitas: pakan, probiotik, pupuk, biochar, vaksin, teknologi budidaya, atau metode pengolahan.",
        "components": {
            "P": "Population/Problem: objek, komoditas, spesies, sistem produksi, atau masalah utama.",
            "I": "Intervention: perlakuan, teknologi, produk, strategi, atau tindakan yang diuji.",
            "C": "Comparator: kontrol, praktik konvensional, tanpa perlakuan, atau perlakuan pembanding.",
            "O": "Outcome: hasil terukur seperti FCR, bobot badan, yield, kualitas, survival, emisi, atau soil carbon.",
        },
        "warning": "Gunakan PICO jika desain studi belum ingin dibatasi terlalu ketat. Untuk target Q1/Q2, biasanya PICOS lebih kuat karena desain studi dijelaskan sejak awal.",
    },
    "PICOS": {
        "name": "PICOS",
        "focus": "Intervensi/perlakuan dengan batasan jenis studi yang akan dimasukkan.",
        "best_for": "Paling cocok untuk systematic review yang ingin kuat secara metodologi dan berpotensi meta-analysis.",
        "components": {
            "P": "Population/Problem: objek, komoditas, spesies, sistem produksi, atau masalah utama.",
            "I": "Intervention: perlakuan, teknologi, produk, strategi, atau tindakan yang diuji.",
            "C": "Comparator: kontrol, praktik konvensional, tanpa perlakuan, atau perlakuan pembanding.",
            "O": "Outcome: hasil terukur seperti FCR, bobot badan, yield, kualitas, survival, emisi, atau soil carbon.",
            "S": "Study design: feeding trial, field trial, greenhouse experiment, randomized trial, observational study, atau laboratory experiment.",
        },
        "warning": "PICOS adalah pilihan paling aman untuk naskah systematic review yang ditargetkan ke jurnal bereputasi karena screening dan sintesis menjadi lebih terarah.",
    },
    "PECO": {
        "name": "PECO",
        "focus": "Paparan/exposure, faktor risiko, tekanan lingkungan, kondisi alami, atau faktor yang tidak selalu diberikan sebagai perlakuan langsung.",
        "best_for": "Cocok untuk topik kekeringan, heat stress, salinitas, pencemaran, iklim, penyakit, land-use change, atau paparan lingkungan lain.",
        "components": {
            "P": "Population/Problem: objek, komoditas, spesies, ekosistem, atau sistem produksi.",
            "E": "Exposure: paparan/faktor risiko/kondisi seperti drought, heat stress, salinity, pollutant, disease pressure, atau climate variability.",
            "C": "Comparator: kondisi normal, tidak terpapar, tingkat paparan rendah, atau lokasi/kondisi kontrol.",
            "O": "Outcome: dampak terukur seperti produksi, yield, survival, milk yield, soil health, kualitas air, atau biodiversitas.",
        },
        "warning": "PECO lebih tepat daripada PICO apabila variabel utama adalah paparan atau kondisi, bukan intervensi yang sengaja diberikan peneliti.",
    },
}

DOMAIN_FRAMEWORK_EXAMPLES = {
    ("Peternakan", "PICOS"): {
        "title": "Effects of Probiotic Supplementation on Growth Performance and Feed Conversion Ratio in Broiler Chickens: A Systematic Review and Meta-Analysis",
        "population": "broiler chickens",
        "intervention": "probiotic supplementation",
        "comparator": "control diet or non-supplemented diet",
        "outcome": "growth performance; feed conversion ratio; body weight gain; mortality",
        "study_design": "experimental studies or feeding trials",
        "research_question": "How does probiotic supplementation affect growth performance, feed conversion ratio, and mortality in broiler chickens compared with non-supplemented diets?",
        "keywords": {
            "population_terms": "broiler chicken\npoultry\nGallus gallus",
            "intervention_terms": "probiotic\nprebiotic\nsynbiotic\nfeed additive",
            "comparator_terms": "control diet\nbasal diet\nnon-supplemented diet",
            "outcome_terms": "growth performance\nfeed conversion ratio\nFCR\nbody weight gain\nmortality",
            "study_terms": "feeding trial\nexperimental study\ncontrolled trial",
        },
        "insight": "Topik ini kuat untuk meta-analysis karena outcome seperti FCR dan body weight gain biasanya kuantitatif. Tantangannya adalah heterogenitas strain probiotik, dosis, durasi pemberian, umur broiler, dan kondisi pemeliharaan.",
    },
    ("Peternakan", "PICO"): {
        "title": "Herbal Feed Additives for Improving Growth Performance in Poultry: A Systematic Review",
        "population": "poultry or broiler chickens",
        "intervention": "herbal feed additives",
        "comparator": "basal diet or commercial feed without herbal additives",
        "outcome": "growth performance; feed efficiency; immune response",
        "study_design": "experimental studies",
        "research_question": "Do herbal feed additives improve growth performance and feed efficiency in poultry compared with basal diets?",
        "keywords": {
            "population_terms": "poultry\nbroiler chicken\nlayer chicken",
            "intervention_terms": "herbal feed additive\nphytogenic additive\nplant extract\nessential oil",
            "comparator_terms": "basal diet\ncontrol diet\nwithout additive",
            "outcome_terms": "growth performance\nfeed efficiency\nbody weight gain\nimmune response",
            "study_terms": "experimental study\nfeeding trial",
        },
        "insight": "PICO cukup untuk mengeksplorasi efektivitas umum, tetapi untuk naskah jurnal Q sebaiknya study design tetap dijelaskan pada kriteria inklusi agar kualitas bukti lebih terkontrol.",
    },
    ("Peternakan", "PECO"): {
        "title": "Effects of Heat Stress Exposure on Milk Yield and Physiological Responses in Dairy Cattle: A Systematic Review",
        "population": "dairy cattle",
        "intervention": "heat stress exposure",
        "comparator": "thermoneutral or non-heat stress conditions",
        "outcome": "milk yield; physiological response; feed intake; reproductive performance",
        "study_design": "observational studies and experimental exposure studies",
        "research_question": "How does heat stress exposure affect milk yield and physiological responses in dairy cattle compared with thermoneutral conditions?",
        "keywords": {
            "population_terms": "dairy cattle\ndairy cow\nlactating cow",
            "intervention_terms": "heat stress\nthermal stress\nhigh temperature\ntemperature humidity index",
            "comparator_terms": "thermoneutral\nnormal temperature\nnon-heat stress",
            "outcome_terms": "milk yield\nfeed intake\nphysiological response\nreproductive performance",
            "study_terms": "observational study\nexperimental study\nfield study",
        },
        "insight": "Gunakan PECO karena heat stress adalah paparan. Fokus analisis sebaiknya mencatat indeks THI, durasi paparan, fase laktasi, dan sistem pemeliharaan.",
    },
    ("Agro/Agronomi", "PICOS"): {
        "title": "Effects of Biochar Application on Maize Yield and Soil Organic Carbon in Tropical Agriculture: A Systematic Review and Meta-Analysis",
        "population": "maize crops or tropical agricultural soils",
        "intervention": "biochar application",
        "comparator": "no biochar or conventional fertilization",
        "outcome": "maize yield; soil organic carbon; nutrient availability; water use efficiency",
        "study_design": "field trials and greenhouse experiments",
        "research_question": "How does biochar application affect maize yield and soil organic carbon in tropical agricultural systems compared with no biochar or conventional fertilization?",
        "keywords": {
            "population_terms": "maize\ncorn\nZea mays\ntropical soil",
            "intervention_terms": "biochar\nsoil amendment\ncharcoal amendment",
            "comparator_terms": "no biochar\ncontrol\nconventional fertilization",
            "outcome_terms": "maize yield\nsoil organic carbon\nnutrient availability\nwater use efficiency",
            "study_terms": "field trial\ngreenhouse experiment\ncontrolled experiment",
        },
        "insight": "Topik biochar kuat untuk systematic review karena relevan dengan soil health dan climate-smart agriculture. Untuk meta-analysis, pastikan satuan yield, dosis biochar, jenis bahan baku biochar, dan kondisi tanah dicatat lengkap.",
    },
    ("Agro/Agronomi", "PICO"): {
        "title": "Organic Fertilizer Application for Improving Rice Productivity: A Systematic Review",
        "population": "rice crops or paddy fields",
        "intervention": "organic fertilizer application",
        "comparator": "inorganic fertilizer or no fertilizer control",
        "outcome": "rice yield; soil fertility; nutrient uptake",
        "study_design": "field trials and greenhouse experiments",
        "research_question": "Does organic fertilizer application improve rice yield and soil fertility compared with inorganic fertilizer or no fertilizer control?",
        "keywords": {
            "population_terms": "rice\npaddy\nOryza sativa",
            "intervention_terms": "organic fertilizer\ncompost\nmanure\norganic amendment",
            "comparator_terms": "inorganic fertilizer\nchemical fertilizer\ncontrol\nno fertilizer",
            "outcome_terms": "rice yield\nsoil fertility\nnutrient uptake\nproductivity",
            "study_terms": "field trial\ngreenhouse experiment",
        },
        "insight": "Topik ini cocok untuk PICO karena ada intervensi pemupukan. Namun untuk jurnal Q, pisahkan kompos, manure, dan biofertilizer karena mekanisme dan efeknya bisa berbeda.",
    },
    ("Agro/Agronomi", "PECO"): {
        "title": "Effects of Drought Stress on Rice Growth and Yield: A Systematic Review",
        "population": "rice crops",
        "intervention": "drought stress exposure",
        "comparator": "normal irrigation or non-drought conditions",
        "outcome": "rice yield; growth; physiological response; water use efficiency",
        "study_design": "field trials, greenhouse experiments, and observational studies",
        "research_question": "How does drought stress exposure affect rice growth and yield compared with normal irrigation conditions?",
        "keywords": {
            "population_terms": "rice\nOryza sativa\npaddy",
            "intervention_terms": "drought stress\nwater deficit\nlimited irrigation",
            "comparator_terms": "normal irrigation\nwell-watered\nnon-drought",
            "outcome_terms": "rice yield\ngrowth\nphysiological response\nwater use efficiency",
            "study_terms": "field trial\ngreenhouse experiment\nobservational study",
        },
        "insight": "PECO tepat karena drought adalah paparan. Catat fase pertumbuhan tanaman, intensitas kekeringan, durasi paparan, dan varietas karena faktor tersebut sangat memengaruhi heterogenitas.",
    },
    ("Perikanan/Akuakultur", "PICOS"): {
        "title": "Effects of Probiotic Supplementation on Growth Performance and Survival of Nile Tilapia: A Systematic Review and Meta-Analysis",
        "population": "Nile tilapia or cultured fish",
        "intervention": "probiotic supplementation",
        "comparator": "control feed or non-supplemented diet",
        "outcome": "growth performance; survival rate; feed conversion ratio; immune response",
        "study_design": "aquaculture feeding trials and controlled experiments",
        "research_question": "How does probiotic supplementation affect growth performance, survival, and feed conversion ratio in Nile tilapia compared with non-supplemented diets?",
        "keywords": {
            "population_terms": "Nile tilapia\nOreochromis niloticus\nfarmed fish\naquaculture",
            "intervention_terms": "probiotic\nprebiotic\nsynbiotic\nfeed additive",
            "comparator_terms": "control feed\nbasal diet\nnon-supplemented diet",
            "outcome_terms": "growth performance\nsurvival rate\nfeed conversion ratio\nimmune response",
            "study_terms": "feeding trial\ncontrolled experiment\naquaculture trial",
        },
        "insight": "Outcome akuakultur sering kuantitatif, tetapi kualitas air, padat tebar, ukuran awal ikan, dan lama pemeliharaan harus dicatat sebagai sumber heterogenitas.",
    },
    ("Perikanan/Akuakultur", "PICO"): {
        "title": "Biofloc Technology for Improving Water Quality and Growth in Aquaculture: A Systematic Review",
        "population": "cultured fish or shrimp",
        "intervention": "biofloc technology",
        "comparator": "conventional aquaculture system",
        "outcome": "water quality; growth performance; survival rate; feed efficiency",
        "study_design": "controlled aquaculture experiments",
        "research_question": "Does biofloc technology improve water quality, growth performance, and survival in aquaculture compared with conventional systems?",
        "keywords": {
            "population_terms": "aquaculture\nfish\nshrimp\ntilapia\ncatfish",
            "intervention_terms": "biofloc\nbiofloc technology\nBFT",
            "comparator_terms": "conventional aquaculture\nclear water system\ncontrol system",
            "outcome_terms": "water quality\ngrowth performance\nsurvival rate\nfeed efficiency",
            "study_terms": "controlled experiment\naquaculture trial",
        },
        "insight": "PICO dapat digunakan karena biofloc adalah intervensi teknologi. Perhatikan variasi C/N ratio, sumber karbon, padat tebar, dan parameter kualitas air.",
    },
    ("Perikanan/Akuakultur", "PECO"): {
        "title": "Effects of Ammonia Exposure on Growth, Survival, and Physiological Stress in Farmed Fish: A Systematic Review",
        "population": "farmed fish",
        "intervention": "ammonia exposure",
        "comparator": "low ammonia or normal water quality conditions",
        "outcome": "growth; survival; physiological stress; immune response",
        "study_design": "exposure studies and aquaculture experiments",
        "research_question": "How does ammonia exposure affect growth, survival, and physiological stress in farmed fish compared with normal water quality conditions?",
        "keywords": {
            "population_terms": "farmed fish\naquaculture fish\ntilapia\ncatfish",
            "intervention_terms": "ammonia exposure\nammonia toxicity\ntotal ammonia nitrogen\nTAN",
            "comparator_terms": "normal water quality\nlow ammonia\ncontrol",
            "outcome_terms": "growth\nsurvival\nphysiological stress\nimmune response",
            "study_terms": "exposure study\ncontrolled experiment\naquaculture trial",
        },
        "insight": "PECO tepat karena ammonia adalah paparan lingkungan. Ekstraksi data perlu mencatat konsentrasi ammonia, pH, suhu, spesies, dan durasi paparan.",
    },
    ("Pangan", "PICOS"): {
        "title": "Effects of Fermentation on Nutritional Quality and Antioxidant Activity of Plant-Based Foods: A Systematic Review",
        "population": "plant-based foods",
        "intervention": "fermentation process",
        "comparator": "unfermented foods or conventional processing",
        "outcome": "nutritional quality; antioxidant activity; sensory quality; microbial safety",
        "study_design": "laboratory experiments and controlled food processing studies",
        "research_question": "How does fermentation affect nutritional quality, antioxidant activity, and sensory quality of plant-based foods compared with unfermented or conventionally processed foods?",
        "keywords": {
            "population_terms": "plant-based food\nfermented food\nvegetable\ngrain\nlegume",
            "intervention_terms": "fermentation\nlactic acid fermentation\nmicrobial fermentation",
            "comparator_terms": "unfermented\nconventional processing\ncontrol",
            "outcome_terms": "nutritional quality\nantioxidant activity\nsensory quality\nmicrobial safety",
            "study_terms": "laboratory experiment\ncontrolled study\nfood processing study",
        },
        "insight": "Topik pangan sering memiliki outcome beragam. Untuk sintesis kuat, kelompokkan outcome menjadi gizi, keamanan mikrobiologi, sensoris, dan aktivitas bioaktif.",
    },
    ("Pangan", "PICO"): {
        "title": "Edible Coating for Extending Shelf Life of Fresh Fruits: A Systematic Review",
        "population": "fresh fruits",
        "intervention": "edible coating",
        "comparator": "uncoated control or conventional packaging",
        "outcome": "shelf life; weight loss; firmness; microbial quality",
        "study_design": "controlled postharvest experiments",
        "research_question": "Does edible coating extend shelf life and maintain quality of fresh fruits compared with uncoated or conventionally packaged controls?",
        "keywords": {
            "population_terms": "fresh fruit\npostharvest fruit\nfruit quality",
            "intervention_terms": "edible coating\nbiopolymer coating\nchitosan coating\nalginate coating",
            "comparator_terms": "uncoated control\nconventional packaging\ncontrol",
            "outcome_terms": "shelf life\nweight loss\nfirmness\nmicrobial quality",
            "study_terms": "postharvest experiment\ncontrolled experiment",
        },
        "insight": "PICO tepat karena edible coating adalah intervensi. Variabel penting: jenis coating, konsentrasi, suhu penyimpanan, jenis buah, dan lama penyimpanan.",
    },
    ("Pangan", "PECO"): {
        "title": "Effects of Storage Temperature Exposure on Microbial Safety and Quality of Fresh Meat: A Systematic Review",
        "population": "fresh meat products",
        "intervention": "storage temperature exposure",
        "comparator": "recommended cold storage temperature",
        "outcome": "microbial safety; shelf life; physicochemical quality; sensory quality",
        "study_design": "storage experiments and observational studies",
        "research_question": "How does storage temperature exposure affect microbial safety and quality of fresh meat products compared with recommended cold storage conditions?",
        "keywords": {
            "population_terms": "fresh meat\nmeat product\nbeef\nchicken meat",
            "intervention_terms": "storage temperature\ntemperature abuse\ncold storage\nrefrigeration",
            "comparator_terms": "recommended temperature\noptimal storage\ncontrol temperature",
            "outcome_terms": "microbial safety\nshelf life\nphysicochemical quality\nsensory quality",
            "study_terms": "storage experiment\nobservational study\ncontrolled study",
        },
        "insight": "PECO tepat jika suhu dianggap paparan. Catat suhu aktual, durasi, jenis kemasan, jenis daging, dan metode uji mikrobiologi.",
    },
    ("Lingkungan", "PICOS"): {
        "title": "Agroforestry Interventions for Improving Soil Health and Biodiversity in Agricultural Landscapes: A Systematic Review",
        "population": "agricultural landscapes or agroecosystems",
        "intervention": "agroforestry intervention",
        "comparator": "monoculture or conventional agricultural systems",
        "outcome": "soil health; biodiversity; carbon storage; ecosystem services",
        "study_design": "field studies and comparative ecological studies",
        "research_question": "How do agroforestry interventions affect soil health, biodiversity, and carbon storage compared with monoculture or conventional agricultural systems?",
        "keywords": {
            "population_terms": "agricultural landscape\nagroecosystem\nfarmland",
            "intervention_terms": "agroforestry\ntree-based farming\nsilvopasture\nalley cropping",
            "comparator_terms": "monoculture\nconventional agriculture\nnon-agroforestry",
            "outcome_terms": "soil health\nbiodiversity\ncarbon storage\necosystem services",
            "study_terms": "field study\ncomparative study\necological study",
        },
        "insight": "Topik ini cocok dengan ROSES/CEE karena berhubungan dengan environmental evidence. Heterogenitas lokasi dan indikator ekologis harus dijelaskan dengan hati-hati.",
    },
    ("Lingkungan", "PICO"): {
        "title": "Restoration Practices for Improving Soil Health in Degraded Agricultural Land: A Systematic Review",
        "population": "degraded agricultural land",
        "intervention": "restoration practices",
        "comparator": "unrestored or conventional land management",
        "outcome": "soil health; soil organic carbon; vegetation recovery; erosion reduction",
        "study_design": "field studies and restoration experiments",
        "research_question": "Do restoration practices improve soil health and vegetation recovery in degraded agricultural land compared with unrestored or conventional land management?",
        "keywords": {
            "population_terms": "degraded agricultural land\ndegraded soil\nfarmland",
            "intervention_terms": "restoration\nrehabilitation\nsoil conservation\nrevegetation",
            "comparator_terms": "unrestored land\nconventional management\ncontrol site",
            "outcome_terms": "soil health\nsoil organic carbon\nvegetation recovery\nerosion reduction",
            "study_terms": "field study\nrestoration experiment\ncomparative study",
        },
        "insight": "PICO masih bisa digunakan bila restoration dianggap intervensi. Untuk environmental evidence, gunakan ROSES dan jelaskan konteks ekosistem secara rinci.",
    },
    ("Lingkungan", "PECO"): {
        "title": "Effects of Land-Use Change Exposure on Soil Carbon and Biodiversity in Agroecosystems: A Systematic Review",
        "population": "agroecosystems or agricultural landscapes",
        "intervention": "land-use change exposure",
        "comparator": "unchanged land use or reference ecosystem",
        "outcome": "soil carbon; biodiversity; ecosystem services; soil quality",
        "study_design": "observational studies and comparative ecological studies",
        "research_question": "How does land-use change exposure affect soil carbon and biodiversity in agroecosystems compared with unchanged land use or reference ecosystems?",
        "keywords": {
            "population_terms": "agroecosystem\nagricultural landscape\nfarmland",
            "intervention_terms": "land-use change\nland conversion\nagricultural expansion",
            "comparator_terms": "reference ecosystem\nunchanged land use\ncontrol site",
            "outcome_terms": "soil carbon\nbiodiversity\necosystem services\nsoil quality",
            "study_terms": "observational study\ncomparative study\necological study",
        },
        "insight": "PECO tepat karena land-use change adalah paparan/kondisi. Catat tipe perubahan lahan, waktu sejak perubahan, zona iklim, dan indikator biodiversitas.",
    },
    ("Teknik Pertanian dan Biosistem", "PICOS"): {
        "title": "Smart Irrigation Technologies for Improving Water Use Efficiency and Crop Yield in Agricultural Systems: A Systematic Review",
        "population": "agricultural cropping systems or irrigated farms",
        "intervention": "smart irrigation technologies or automated irrigation systems",
        "comparator": "conventional irrigation or farmer-managed irrigation",
        "outcome": "water use efficiency; crop yield; irrigation water productivity; energy use; system performance",
        "study_design": "field trials, controlled experiments, and simulation-validation studies",
        "research_question": "How do smart irrigation technologies affect water use efficiency, crop yield, irrigation water productivity, and system performance compared with conventional irrigation in agricultural systems?",
        "keywords": {
            "population_terms": "agricultural system\nirrigated farm\ncropping system\nfield crop",
            "intervention_terms": "smart irrigation\nautomated irrigation\nprecision irrigation\nsensor-based irrigation\nIoT irrigation",
            "comparator_terms": "conventional irrigation\nfarmer-managed irrigation\nmanual irrigation\ncontrol irrigation",
            "outcome_terms": "water use efficiency\nirrigation water productivity\ncrop yield\nenergy use\nsystem performance",
            "study_terms": "field trial\ncontrolled experiment\nsimulation validation\nperformance evaluation",
        },
        "insight": "Topik ini kuat untuk Teknik Pertanian dan Biosistem karena menghubungkan rekayasa irigasi, sensor/IoT, efisiensi air, dan produktivitas tanaman. Untuk naskah Q-level, bedakan studi uji lapang, simulasi-model, dan prototipe laboratorium agar sintesis tidak terlalu heterogen.",
    },
    ("Teknik Pertanian dan Biosistem", "PICO"): {
        "title": "Solar Drying Technologies for Improving Drying Performance and Quality of Agricultural Products: A Systematic Review",
        "population": "agricultural products or postharvest commodities",
        "intervention": "solar drying technologies or hybrid dryers",
        "comparator": "open sun drying or conventional drying methods",
        "outcome": "drying rate; energy efficiency; product quality; moisture reduction; microbial safety",
        "study_design": "laboratory experiments, prototype performance tests, and postharvest trials",
        "research_question": "Do solar drying technologies improve drying performance, energy efficiency, and product quality of agricultural products compared with open sun drying or conventional drying methods?",
        "keywords": {
            "population_terms": "agricultural product\npostharvest commodity\nfood crop\nhorticultural product",
            "intervention_terms": "solar dryer\nhybrid solar dryer\nindirect solar drying\ngreenhouse dryer",
            "comparator_terms": "open sun drying\nconventional drying\nhot air drying\ncontrol drying",
            "outcome_terms": "drying rate\nenergy efficiency\nmoisture content\nproduct quality\nmicrobial safety",
            "study_terms": "laboratory experiment\nprototype test\nperformance evaluation\npostharvest trial",
        },
        "insight": "PICO sesuai bila teknologi pengering dianggap sebagai intervensi rekayasa. Ekstraksi data perlu mencatat tipe dryer, sumber energi tambahan, kapasitas alat, suhu, kelembapan, laju aliran udara, komoditas, serta parameter mutu produk.",
    },
    ("Teknik Pertanian dan Biosistem", "PECO"): {
        "title": "Effects of Agricultural Machinery Traffic Exposure on Soil Compaction and Crop Performance: A Systematic Review",
        "population": "agricultural soils or cropping systems",
        "intervention": "agricultural machinery traffic exposure",
        "comparator": "no traffic, controlled traffic, or low-intensity machinery traffic",
        "outcome": "soil compaction; bulk density; penetration resistance; crop yield; soil physical quality",
        "study_design": "field studies, controlled traffic experiments, and observational studies",
        "research_question": "How does agricultural machinery traffic exposure affect soil compaction, soil physical quality, and crop performance compared with no traffic, controlled traffic, or lower traffic intensity?",
        "keywords": {
            "population_terms": "agricultural soil\ncropping system\nfield soil\nfarmland",
            "intervention_terms": "machinery traffic\ntractor traffic\nwheel traffic\nsoil compaction\ntraffic intensity",
            "comparator_terms": "no traffic\ncontrolled traffic\nlow traffic intensity\nreference plot",
            "outcome_terms": "bulk density\npenetration resistance\nsoil compaction\nsoil physical quality\ncrop yield",
            "study_terms": "field study\ncontrolled traffic experiment\nobservational study\ncomparative study",
        },
        "insight": "PECO tepat karena lalu lintas mesin diperlakukan sebagai paparan. Catat jenis mesin, beban gandar, tekanan ban, jumlah lintasan, kadar air tanah, tekstur tanah, kedalaman pengukuran, dan fase pertumbuhan tanaman untuk menjelaskan heterogenitas.",
    },

}

TARGET_GUIDES = {
    "Q1/Q2": {
        "focus": "Topik harus spesifik, global, metodologi transparan, quality assessment kuat, dan sintesis tidak sekadar rangkuman artikel.",
        "minimum": "Gunakan minimal database besar seperti Scopus/Web of Science ditambah database bidang; tampilkan search string lengkap; gunakan PRISMA/ROSES; siapkan justification untuk heterogenitas.",
    },
    "Q2/Q3": {
        "focus": "Topik tetap harus punya novelty, tetapi scope dapat lebih terbatas selama metode systematic review jelas.",
        "minimum": "Pastikan screening, PRISMA, inclusion-exclusion, dan quality assessment terdokumentasi baik.",
    },
    "Scopus awal": {
        "focus": "Utamakan keterbacaan metode, kejelasan research question, dan konsistensi data extraction.",
        "minimum": "Gunakan database internasional dan hindari hanya memakai Google Scholar tanpa strategi pencarian yang dapat diulang.",
    },
    "Sinta/Kampus": {
        "focus": "Boleh lebih kontekstual/lokal, tetapi tetap harus sistematis dan tidak berubah menjadi narrative review biasa.",
        "minimum": "Minimal ada kerangka PICO/PICOS/PECO, flow seleksi artikel, dan alasan inklusi-eksklusi yang jelas.",
    },
}


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
        "sync_config": {
            "auto_sync": True,
            "overwrite_generated": True,
            "auto_apply_domain_example": True,
            "last_sync": "Belum pernah sinkron",
        },
        "ai_config": {
            "mode": "Offline Mode",
            "model_selection": "Auto pilih model hemat biaya",
            "model": "slashai/gemini-3-flash",
            "manual_model": "slashai/gemini-3-flash",
            "selected_model_source": "fallback",
        },
        "ai_outputs": {},
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




def make_auto_research_question(project: dict):
    """Generate a concise research question from the current framework fields."""
    framework = project.get("framework", "PICOS")
    population = project.get("population", "target population").strip() or "target population"
    intervention = project.get("intervention", "intervention/exposure").strip() or "intervention/exposure"
    comparator = project.get("comparator", "comparator/control").strip() or "comparator/control"
    outcome = project.get("outcome", "main outcomes").strip() or "main outcomes"
    study_design = project.get("study_design", "eligible studies").strip() or "eligible studies"

    if framework == "PECO":
        return f"How does exposure to {intervention} affect {outcome} in {population} compared with {comparator}?"
    if framework == "PICOS":
        return f"In {study_design}, how does {intervention} affect {outcome} in {population} compared with {comparator}?"
    return f"How does {intervention} affect {outcome} in {population} compared with {comparator}?"


def make_auto_criteria(project: dict):
    """Create inclusion-exclusion criteria that follow the previous menu choices."""
    framework = project.get("framework", "PICOS")
    population = project.get("population", "the defined population/problem").strip() or "the defined population/problem"
    intervention = project.get("intervention", "the defined intervention/exposure").strip() or "the defined intervention/exposure"
    comparator = project.get("comparator", "the defined comparator").strip() or "the defined comparator"
    outcome = project.get("outcome", "the defined outcome").strip() or "the defined outcome"
    study_design = project.get("study_design", "eligible empirical study designs").strip() or "eligible empirical study designs"
    year_range = project.get("year_range", "selected year range")
    language = project.get("language", "selected languages")
    scope = project.get("geographical_scope", "Global")

    exposure_or_intervention = "exposure" if framework == "PECO" else "intervention"
    inclusion = (
        f"Peer-reviewed empirical studies published within {year_range}; articles written in {language}; "
        f"studies involving {population}; studies evaluating the {exposure_or_intervention} of {intervention}; "
        f"studies using {comparator} as comparator/control where applicable; studies reporting at least one outcome related to {outcome}; "
        f"eligible study designs: {study_design}; geographical scope: {scope}."
    )
    exclusion = (
        "Duplicated records; narrative reviews, editorials, opinion papers, conference abstracts without full data, and non-peer-reviewed sources; "
        f"studies outside the population/problem ({population}); studies not evaluating {intervention}; studies without relevant comparator/control where required; "
        f"studies not reporting {outcome}; studies with inaccessible full text or insufficient data for extraction; studies outside {year_range}."
    )
    return {"inclusion": inclusion, "exclusion": exclusion}


def sync_downstream_from_project(reason="manual"):
    """Synchronize all downstream modules from the current project fields.

    Langkah 1 menjadi sumber utama. Fungsi ini membuat Protocol, Search Strategy,
    Screening Score, PRISMA, Quality Assessment, Data Extraction, Insight, dan Export
    membaca dasar yang sama.
    """
    p = st.session_state.project
    config = st.session_state.get("sync_config", {"auto_sync": True, "overwrite_generated": True})
    overwrite = bool(config.get("overwrite_generated", True))

    if overwrite or not str(p.get("research_question", "")).strip():
        p["research_question"] = make_auto_research_question(p)
    if overwrite or not st.session_state.get("criteria"):
        st.session_state.criteria = make_auto_criteria(p)
    elif not st.session_state.criteria.get("inclusion") or not st.session_state.criteria.get("exclusion"):
        st.session_state.criteria.update(make_auto_criteria(p))
    if overwrite or not st.session_state.get("terms"):
        st.session_state.terms = suggest_terms_from_project(p)
    else:
        # Tambahkan istilah inti dari menu sebelumnya tanpa menghapus istilah manual.
        suggested = suggest_terms_from_project(p)
        merged = {}
        for key in ["population_terms", "intervention_terms", "comparator_terms", "outcome_terms", "study_terms"]:
            merged[key] = "\n".join(unique_keep_order(split_terms(st.session_state.terms.get(key, "")) + split_terms(suggested.get(key, ""))))
        st.session_state.terms = merged

    if "articles" in st.session_state and not st.session_state.articles.empty:
        st.session_state.articles = flag_duplicates(st.session_state.articles)
        st.session_state.articles = apply_relevance_scoring(st.session_state.articles)
        sync_quality_extraction()
    st.session_state.sync_config["last_sync"] = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ({reason})"


def sync_if_auto(reason="auto"):
    config = st.session_state.get("sync_config", {})
    if config.get("auto_sync", True):
        sync_downstream_from_project(reason=reason)


def render_sync_status():
    config = st.session_state.get("sync_config", {})
    last_sync = config.get("last_sync", "Belum pernah sinkron")
    st.caption(f"Status sinkronisasi: {last_sync}. Protocol, search, screening score, PRISMA, quality, extraction, insight, dan export mengikuti data dari langkah sebelumnya.")



def get_selected_example(project: dict):
    domain = infer_domain(project)
    framework = project.get("framework", "PICOS")
    if domain == "Otomatis":
        domain = "Peternakan"
    return DOMAIN_FRAMEWORK_EXAMPLES.get((domain, framework)) or DOMAIN_FRAMEWORK_EXAMPLES.get((domain, "PICOS")) or DOMAIN_FRAMEWORK_EXAMPLES[("Peternakan", "PICOS")]


def apply_example_to_project(example: dict, domain: str, framework: str):
    st.session_state.project.update({
        "title": example.get("title", ""),
        "domain": domain,
        "framework": framework,
        "research_question": example.get("research_question", ""),
        "population": example.get("population", ""),
        "intervention": example.get("intervention", ""),
        "comparator": example.get("comparator", ""),
        "outcome": example.get("outcome", ""),
        "study_design": example.get("study_design", ""),
    })
    st.session_state.terms = example.get("keywords", suggest_terms_from_project(st.session_state.project))
    st.session_state.project["research_question"] = example.get("research_question", make_auto_research_question(st.session_state.project))
    st.session_state.criteria = make_auto_criteria(st.session_state.project)
    sync_downstream_from_project(reason="contoh diterapkan")




def apply_domain_framework_autofill(domain: str, framework: str, source: str = "perubahan bidang/kerangka"):
    """Apply the default example for a selected domain and framework.

    This keeps general project settings, but refreshes the review core fields so
    downstream menus can immediately follow the selected research field.
    """
    if domain == "Otomatis":
        inferred = infer_domain(st.session_state.project)
        domain_to_use = inferred if inferred != "Otomatis" else "Peternakan"
    else:
        domain_to_use = domain

    framework_to_use = framework if framework in FRAMEWORK_GUIDES else "PICOS"
    example = get_selected_example({"domain": domain_to_use, "framework": framework_to_use})
    keep = {
        "target_level": st.session_state.project.get("target_level", "Q1/Q2"),
        "review_type": st.session_state.project.get("review_type", "Systematic Review and Meta-Analysis"),
        "year_range": st.session_state.project.get("year_range", "2015-2026"),
        "language": st.session_state.project.get("language", "English and Bahasa Indonesia"),
        "geographical_scope": st.session_state.project.get("geographical_scope", "Global"),
        "date_started": st.session_state.project.get("date_started", str(date.today())),
    }
    apply_example_to_project(example, domain_to_use, framework_to_use)
    st.session_state.project.update(keep)
    sync_downstream_from_project(reason=source)
    return example


def render_current_domain_example_preview(domain: str, framework: str):
    """Show the example that will be used when the field/framework is selected."""
    domain_to_use = domain if domain != "Otomatis" else infer_domain(st.session_state.project)
    if domain_to_use == "Otomatis":
        domain_to_use = "Peternakan"
    example = get_selected_example({"domain": domain_to_use, "framework": framework})
    with st.expander("Lihat contoh yang akan diterapkan untuk pilihan ini", expanded=False):
        st.markdown(f"**Bidang:** {domain_to_use}  ")
        st.markdown(f"**Kerangka:** {framework}")
        st.success(example.get("title", ""))
        st.dataframe(pd.DataFrame([
            {"Komponen": "Population/Problem", "Contoh": example.get("population", "")},
            {"Komponen": "Intervention/Exposure", "Contoh": example.get("intervention", "")},
            {"Komponen": "Comparator", "Contoh": example.get("comparator", "")},
            {"Komponen": "Outcome", "Contoh": example.get("outcome", "")},
            {"Komponen": "Study Design", "Contoh": example.get("study_design", "")},
            {"Komponen": "Research Question", "Contoh": example.get("research_question", "")},
        ]), use_container_width=True, hide_index=True)
        st.code(build_search_string(example.get("keywords", {})), language="text")

def render_framework_domain_guidance(project: dict):
    domain = infer_domain(project)
    framework = project.get("framework", "PICOS")
    if domain == "Otomatis":
        domain = "Peternakan"
    guide = FRAMEWORK_GUIDES.get(framework, FRAMEWORK_GUIDES["PICOS"])
    example = get_selected_example({**project, "domain": domain, "framework": framework})
    target = TARGET_GUIDES.get(project.get("target_level", "Q1/Q2"), TARGET_GUIDES["Q1/Q2"])
    profile = DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["Peternakan"])

    st.subheader("Contoh dan Informasi Sesuai Pilihan")
    st.caption("Bagian ini berubah otomatis mengikuti pilihan bidang, kerangka, dan target publikasi yang dipilih peneliti.")

    t1, t2, t3, t4 = st.tabs(["Kerangka", "Contoh Topik", "Search & Database", "Insight Naskah"])
    with t1:
        st.markdown(f"**Kerangka terpilih:** {guide['name']}")
        st.write(guide["focus"])
        st.info(guide["best_for"])
        comp_df = pd.DataFrame([{"Kode": k, "Penjelasan": v} for k, v in guide["components"].items()])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)
        st.warning(guide["warning"])
    with t2:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**Contoh judul untuk {domain} - {framework}:**")
            st.success(example["title"])
            st.markdown("**Contoh research question:**")
            st.write(example["research_question"])
        with c2:
            if st.button("Gunakan contoh ini", use_container_width=True):
                apply_example_to_project(example, domain, framework)
                st.success("Contoh diterapkan ke judul, komponen review, dan search terms.")
                st.rerun()
        example_df = pd.DataFrame([
            {"Komponen": "Population/Problem", "Isi": example.get("population", "")},
            {"Komponen": "Intervention/Exposure", "Isi": example.get("intervention", "")},
            {"Komponen": "Comparator", "Isi": example.get("comparator", "")},
            {"Komponen": "Outcome", "Isi": example.get("outcome", "")},
            {"Komponen": "Study Design", "Isi": example.get("study_design", "")},
        ])
        st.dataframe(example_df, use_container_width=True, hide_index=True)
    with t3:
        st.markdown("**Contoh search terms:**")
        kw = example.get("keywords", {})
        for label, key in [
            ("Population terms", "population_terms"),
            ("Intervention/Exposure terms", "intervention_terms"),
            ("Comparator terms", "comparator_terms"),
            ("Outcome terms", "outcome_terms"),
            ("Study design terms", "study_terms"),
        ]:
            with st.expander(label, expanded=False):
                st.code(kw.get(key, ""), language="text")
        st.markdown("**Boolean search contoh:**")
        st.code(build_search_string(kw), language="text")
        c1, c2 = st.columns(2)
        c1.markdown("**Database disarankan:**\n" + "\n".join([f"- {x}" for x in profile["databases"]]))
        c2.markdown("**Quality assessment:**")
        c2.write(profile["quality_tool"])
    with t4:
        st.markdown("**Insight berdasarkan contoh terpilih:**")
        st.write(example["insight"])
        st.markdown("**Arahan untuk target publikasi:**")
        st.info(target["focus"])
        st.write(target["minimum"])
        st.markdown("**Catatan penulisan:**")
        if framework == "PECO":
            st.write("Gunakan istilah *exposure* secara konsisten pada judul, research question, eligibility criteria, dan tabel ekstraksi data. Jangan memaksa paparan menjadi intervensi.")
        elif framework == "PICOS":
            st.write("Tuliskan desain studi yang diterima sejak awal agar proses screening lebih objektif dan lebih siap untuk meta-analysis.")
        else:
            st.write("PICO boleh digunakan untuk tahap awal, tetapi tetap jelaskan study design pada eligibility criteria agar metode tidak terlalu longgar.")


def make_guidance_markdown():
    p = st.session_state.project
    domain = infer_domain(p)
    framework = p.get("framework", "PICOS")
    guide = FRAMEWORK_GUIDES.get(framework, FRAMEWORK_GUIDES["PICOS"])
    example = get_selected_example(p)
    target = TARGET_GUIDES.get(p.get("target_level", "Q1/Q2"), TARGET_GUIDES["Q1/Q2"])
    profile = DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["Peternakan"])
    components = "\n".join([f"- **{k}**: {v}" for k, v in guide["components"].items()])
    databases = "\n".join([f"- {db}" for db in profile["databases"]])
    return f"""# Examples and Guidance

## Pilihan Saat Ini
- Domain: {domain}
- Framework: {framework}
- Target: {p.get('target_level', '')}
- Review type: {p.get('review_type', '')}

## Penjelasan Framework
{guide['focus']}

{guide['best_for']}

### Komponen
{components}

Catatan: {guide['warning']}

## Contoh Sesuai Pilihan
**Judul contoh:** {example.get('title', '')}

**Research question:** {example.get('research_question', '')}

- Population/Problem: {example.get('population', '')}
- Intervention/Exposure: {example.get('intervention', '')}
- Comparator: {example.get('comparator', '')}
- Outcome: {example.get('outcome', '')}
- Study Design: {example.get('study_design', '')}

## Contoh Boolean Search
```text
{build_search_string(example.get('keywords', {}))}
```

## Database Disarankan
{databases}

## Quality Assessment Disarankan
{profile.get('quality_tool', '')}

## Insight Topik
{example.get('insight', '')}

## Arahan Target Publikasi
{target['focus']}

{target['minimum']}
"""


def df_to_xlsx_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    mem = BytesIO()
    with pd.ExcelWriter(mem, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    mem.seek(0)
    return mem.getvalue()

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
            elif col in ["auto_screening_suggestion", "screening_decision", "full_text_decision", "reviewer1_decision", "reviewer2_decision", "consensus_decision"]:
                df[col] = "Belum dinilai"
            elif col == "screening_conflict":
                df[col] = False
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
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    if name.endswith(".ris"):
        return parse_ris(uploaded_file.getvalue().decode("utf-8", errors="ignore"))
    raise ValueError("Format belum didukung. Gunakan XLSX, XLS, atau RIS.")


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
    for col in ["reviewer1_decision", "reviewer2_decision", "consensus_decision"]:
        if col not in df.columns:
            df[col] = "Belum dinilai"
        df[col] = df[col].fillna("Belum dinilai").replace("", "Belum dinilai")
    df = update_dual_reviewer_consensus(df)
    return df


def update_dual_reviewer_consensus(df: pd.DataFrame):
    """Calculate screening conflict and consensus without overwriting completed manual decisions."""
    if df.empty:
        return df
    df = df.copy()
    for col in ["reviewer1_decision", "reviewer2_decision", "consensus_decision", "screening_decision"]:
        if col not in df.columns:
            df[col] = "Belum dinilai"
        df[col] = df[col].fillna("Belum dinilai").replace("", "Belum dinilai")
    conflicts, consensus = [], []
    for _, row in df.iterrows():
        r1 = str(row.get("reviewer1_decision", "Belum dinilai"))
        r2 = str(row.get("reviewer2_decision", "Belum dinilai"))
        if r1 != "Belum dinilai" and r2 != "Belum dinilai" and r1 != r2:
            conflicts.append(True)
            consensus.append("Perlu diskusi")
        elif r1 != "Belum dinilai" and r2 != "Belum dinilai" and r1 == r2:
            conflicts.append(False)
            consensus.append(r1)
        elif r1 != "Belum dinilai":
            conflicts.append(False)
            consensus.append(r1)
        elif r2 != "Belum dinilai":
            conflicts.append(False)
            consensus.append(r2)
        else:
            conflicts.append(False)
            consensus.append(row.get("screening_decision", "Belum dinilai"))
    df["screening_conflict"] = conflicts
    df["consensus_decision"] = consensus
    # Bila belum ada keputusan utama, gunakan konsensus reviewer sebagai keputusan screening.
    mask = df["screening_decision"].isin(["", "Belum dinilai"]) & ~df["consensus_decision"].isin(["", "Belum dinilai", "Perlu diskusi"])
    df.loc[mask, "screening_decision"] = df.loc[mask, "consensus_decision"]
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
            for c in ["selection_bias", "performance_bias", "detection_bias", "attrition_bias", "reporting_bias", "other_bias"]:
                newq[c] = "Unclear"
            newq.update({"id": aid, "title": row.get("title", ""), "quality_score": 0, "quality_category": "Belum dinilai", "overall_risk_of_bias": "Unclear", "certainty_of_evidence": "Not assessed"})
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
    for c in ["selection_bias", "performance_bias", "detection_bias", "attrition_bias", "reporting_bias", "other_bias"]:
        if c not in df.columns:
            df[c] = "Unclear"
        df[c] = df[c].fillna("Unclear").replace("", "Unclear")
    df["quality_score"] = df[bool_cols].sum(axis=1)
    df["quality_category"] = pd.cut(df["quality_score"], bins=[-1, 3, 5, 8], labels=["Low", "Moderate", "High"]).astype(str)
    rob_cols = ["selection_bias", "performance_bias", "detection_bias", "attrition_bias", "reporting_bias", "other_bias"]
    overall = []
    for _, row in df.iterrows():
        vals = [str(row.get(c, "Unclear")) for c in rob_cols]
        if any(v == "High" for v in vals):
            overall.append("High")
        elif vals.count("Unclear") >= 3:
            overall.append("Unclear")
        else:
            overall.append("Low")
    df["overall_risk_of_bias"] = overall
    certainty = []
    reasons = []
    for _, row in df.iterrows():
        score = int(row.get("quality_score", 0))
        rob = row.get("overall_risk_of_bias", "Unclear")
        if score >= 7 and rob == "Low":
            certainty.append("High")
            reasons.append("Kualitas metodologi tinggi dan risiko bias rendah.")
        elif score >= 5 and rob in ["Low", "Unclear"]:
            certainty.append("Moderate")
            reasons.append("Ada keterbatasan kecil pada metode atau risiko bias belum sepenuhnya jelas.")
        elif score >= 3:
            certainty.append("Low")
            reasons.append("Beberapa domain quality/risk of bias perlu diperbaiki atau dilaporkan lebih jelas.")
        else:
            certainty.append("Very Low")
            reasons.append("Kualitas pelaporan rendah atau risiko bias tinggi/tidak jelas.")
    df["certainty_of_evidence"] = certainty
    if "grade_downgrade_reason" not in df.columns:
        df["grade_downgrade_reason"] = reasons
    else:
        blank = df["grade_downgrade_reason"].astype(str).str.strip().eq("")
        df.loc[blank, "grade_downgrade_reason"] = pd.Series(reasons, index=df.index)[blank]
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
Search strategy dihasilkan dari komponen {p.get('framework','PICOS')} dan otomatis mengikuti perubahan pada judul, bidang, population/problem, intervention/exposure, comparator, outcome, dan study design.

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




def prisma_compliance_df():
    """Simplified PRISMA 2020 readiness checklist for pre-submission checking."""
    p, c, terms = st.session_state.project, st.session_state.criteria, st.session_state.terms
    a, q, e = st.session_state.articles, st.session_state.quality, st.session_state.extraction
    counts = get_prisma_counts(True)
    title_result = analyze_title(p)
    checks = [
        ("Title", "Judul menyebut systematic review/meta-analysis", "Lengkap" if re.search(r"systematic review|meta-analysis|meta analysis|systematic map|scoping review", p.get("title", ""), re.I) else "Perlu revisi", "Tambahkan jenis review pada judul."),
        ("Abstract", "Abstract memuat tujuan, database, jumlah studi, hasil utama", "Perlu disusun", "Gunakan Manuscript Builder untuk draft awal."),
        ("Rationale", "Latar belakang menjelaskan alasan review dibutuhkan", "Perlu disusun", "Hubungkan gap bukti dengan kebutuhan review."),
        ("Objectives", "Pertanyaan penelitian eksplisit", "Lengkap" if p.get("research_question") else "Belum lengkap", "Buat research question dari PICOS/PECO."),
        ("Eligibility", "Kriteria inklusi dan eksklusi jelas", "Lengkap" if c.get("inclusion") and c.get("exclusion") else "Belum lengkap", "Lengkapi populasi, intervensi/eksposur, outcome, desain studi, tahun, bahasa."),
        ("Information sources", "Database/sumber informasi disebutkan", "Lengkap" if title_result.get("recommended_databases") else "Perlu revisi", "Sebutkan database yang digunakan dan tanggal pencarian."),
        ("Search strategy", "Search string bisa direplikasi", "Lengkap" if build_search_string(terms).strip() else "Belum lengkap", "Tampilkan Boolean string per database."),
        ("Selection process", "Proses screening title/abstract dan full-text dijelaskan", "Lengkap" if not a.empty and (a["screening_decision"] != "Belum dinilai").any() else "Belum lengkap", "Gunakan dual reviewer dan catat alasan eksklusi."),
        ("Data collection", "Form data extraction disiapkan", "Lengkap" if not e.empty else "Belum lengkap", "Ekstrak desain, sampel, outcome, effect direction, effect size."),
        ("Data items", "Outcome utama dan variabel penting ditentukan", "Lengkap" if p.get("outcome") else "Belum lengkap", "Outcome harus terukur dan konsisten."),
        ("Risk of bias", "Risk of bias/quality assessment dilakukan", "Lengkap" if not q.empty and q.get("overall_risk_of_bias", pd.Series(dtype=str)).replace("", np.nan).notna().any() else "Belum lengkap", "Gunakan SYRCLE/JBI/ROSES/ROBINS-I sesuai desain."),
        ("Effect measures", "Effect size/ukuran efek dicatat", "Lengkap" if not e.empty and pd.to_numeric(e.get("effect_size", pd.Series(dtype=str)), errors="coerce").notna().sum() >= 3 else "Perlu revisi", "Isi mean, SD, n, p-value, atau effect size."),
        ("Synthesis methods", "Metode sintesis dijelaskan", "Perlu disusun", "Jelaskan narrative synthesis atau meta-analysis bila data siap."),
        ("Reporting bias", "Potensi publication/reporting bias dipertimbangkan", "Perlu revisi", "Tambahkan rencana funnel plot/sensitivity atau pembahasan keterbatasan."),
        ("Certainty", "Certainty of evidence dinilai", "Lengkap" if not q.empty and q.get("certainty_of_evidence", pd.Series(dtype=str)).replace("Not assessed", np.nan).notna().any() else "Belum lengkap", "Gunakan GRADE sederhana/teradaptasi."),
        ("Study selection", "PRISMA flow memiliki angka lengkap", "Lengkap" if counts["records_screened"] > 0 else "Belum lengkap", "Import artikel dan isi keputusan screening."),
        ("Study characteristics", "Karakteristik studi disajikan", "Lengkap" if not e.empty else "Belum lengkap", "Gunakan tabel extraction."),
        ("Risk of bias results", "Hasil risk of bias dilaporkan", "Lengkap" if not q.empty else "Belum lengkap", "Sajikan tabel risk of bias."),
        ("Individual results", "Hasil per studi tersedia", "Lengkap" if not e.empty and e.get("key_finding", pd.Series(dtype=str)).astype(str).str.strip().ne("").any() else "Belum lengkap", "Isi key finding per studi."),
        ("Synthesis results", "Sintesis lintas studi tersedia", "Lengkap" if not e.empty and e.get("effect_direction", pd.Series(dtype=str)).replace("", np.nan).notna().any() else "Belum lengkap", "Ringkas arah efek dan heterogenitas."),
        ("Discussion", "Diskusi mengaitkan temuan, bias, dan gap", "Perlu disusun", "Gunakan Insight Report dan Novelty-Gap Analyzer."),
        ("Limitations", "Keterbatasan review ditulis", "Lengkap" if not e.empty and e.get("limitations", pd.Series(dtype=str)).astype(str).str.strip().ne("").any() else "Perlu revisi", "Tambahkan batasan database, bahasa, desain, data outcome."),
        ("Conclusion", "Kesimpulan tidak berlebihan", "Perlu disusun", "Sesuaikan klaim dengan kekuatan bukti."),
        ("Registration", "Protocol/registration disebutkan", "Perlu revisi", "Sebutkan OSF/PROSPERO/ROSES/CEE bila digunakan, atau jelaskan tidak diregistrasi."),
        ("Support", "Pendanaan/konflik kepentingan disiapkan", "Perlu disusun", "Tambahkan funding dan conflict of interest."),
        ("Data availability", "Data screening/extraction tersedia", "Lengkap" if not a.empty else "Belum lengkap", "Lampirkan XLSX/OSF/GitHub sesuai kebijakan jurnal."),
        ("Protocol deviations", "Perubahan dari protocol dicatat", "Perlu disusun", "Catat perubahan kriteria/search setelah screening."),
    ]
    return pd.DataFrame(checks, columns=["prisma_item", "requirement", "status", "recommendation"])


def prisma_s_audit_df():
    p, terms = st.session_state.project, st.session_state.terms
    search = build_search_string(terms)
    dbs = analyze_title(p).get("recommended_databases", [])
    checks = [
        ("Database selected", bool(dbs), "; ".join(dbs[:6]), "Pilih database aktual yang digunakan dan catat tanggal pencarian."),
        ("Full search string", bool(search.strip()), search[:250] + ("..." if len(search) > 250 else ""), "Tampilkan search string lengkap per database."),
        ("Population terms", bool(terms.get("population_terms", "").strip()), terms.get("population_terms", ""), "Tambahkan sinonim spesies/komoditas."),
        ("Intervention/exposure terms", bool(terms.get("intervention_terms", "").strip()), terms.get("intervention_terms", ""), "Tambahkan sinonim perlakuan/paparan."),
        ("Comparator terms", bool(terms.get("comparator_terms", "").strip()), terms.get("comparator_terms", ""), "Comparator dapat dipakai sebagai pencarian atau kriteria screening."),
        ("Outcome terms", bool(terms.get("outcome_terms", "").strip()), terms.get("outcome_terms", ""), "Outcome harus terukur."),
        ("Study design terms", bool(terms.get("study_terms", "").strip()), terms.get("study_terms", ""), "Tambahkan field trial, feeding trial, randomized, observational, dll."),
        ("Boolean operators", "AND" in search and "OR" in search, "AND/OR detected" if "AND" in search or "OR" in search else "Missing", "Gunakan OR untuk sinonim dan AND antar konsep."),
        ("Date range", bool(p.get("year_range", "").strip()), p.get("year_range", ""), "Sebutkan alasan rentang tahun."),
        ("Language", bool(p.get("language", "").strip()), p.get("language", ""), "Jelaskan filter bahasa jika digunakan."),
        ("Grey literature decision", False, "Belum diatur", "Putuskan apakah grey literature dimasukkan atau dikecualikan."),
        ("Deduplication method", True, "DOI + normalized title", "Jelaskan metode deduplikasi."),
        ("Search date", bool(p.get("search_date", "").strip()), p.get("search_date", "Belum diisi"), "Isi tanggal pencarian terakhir."),
        ("Limits/filters", bool(p.get("year_range") or p.get("language")), f"Year: {p.get('year_range','')}; Language: {p.get('language','')}", "Dokumentasikan semua filter database."),
        ("Supplementary search", False, "Belum diatur", "Tambahkan backward/forward citation tracking bila perlu."),
        ("Export documentation", not st.session_state.articles.empty, f"{len(st.session_state.articles)} records imported", "Simpan file ekspor database sebagai lampiran/OSF."),
    ]
    rows = []
    for item, ok, evidence, rec in checks:
        rows.append({"audit_item": item, "status": "Lengkap" if ok else "Perlu revisi", "evidence": evidence, "recommendation": rec})
    return pd.DataFrame(rows)


def meta_analysis_readiness():
    e = st.session_state.extraction
    counts = get_prisma_counts(True)
    total = counts["studies_included"]
    if e.empty:
        return {"score": 0, "status": "Belum siap", "reasons": ["Belum ada data extraction."], "table": pd.DataFrame()}
    num_cols = ["mean_intervention", "sd_intervention", "n_intervention", "mean_control", "sd_control", "n_control"]
    for c in num_cols:
        if c not in e.columns:
            e[c] = ""
    complete_numeric = e[num_cols].apply(lambda col: pd.to_numeric(col, errors="coerce").notna()).all(axis=1).sum()
    effect_numeric = pd.to_numeric(e.get("effect_size", pd.Series(dtype=str)), errors="coerce").notna().sum()
    outcome_filled = e.get("main_outcome", pd.Series(dtype=str)).astype(str).str.strip().ne("").sum()
    comparator_filled = e.get("comparator", pd.Series(dtype=str)).astype(str).str.strip().ne("").sum()
    units = e.get("outcome_unit", pd.Series(dtype=str)).replace("", np.nan).dropna().nunique()
    score = 0
    score += min(25, int(25 * total / 10))
    score += min(25, int(25 * complete_numeric / max(1, total)))
    score += min(20, int(20 * effect_numeric / max(1, total)))
    score += min(15, int(15 * outcome_filled / max(1, total)))
    score += min(10, int(10 * comparator_filled / max(1, total)))
    score += 5 if units <= 2 and units > 0 else 0
    reasons = []
    if total < 5:
        reasons.append("Jumlah studi include kurang dari 5, sehingga meta-analysis masih lemah.")
    if complete_numeric < max(3, total * 0.5):
        reasons.append("Data mean, SD, dan n untuk kelompok intervensi/kontrol belum cukup.")
    if effect_numeric < 3:
        reasons.append("Effect size numerik masih minim.")
    if units > 2:
        reasons.append("Satuan outcome beragam; perlu standardisasi atau subgroup analysis.")
    if not reasons:
        reasons.append("Data awal cukup menjanjikan untuk meta-analysis. Lanjutkan pemeriksaan heterogenitas dan model efek.")
    status = "Siap awal" if score >= 75 else "Cukup potensial" if score >= 55 else "Belum siap"
    table = pd.DataFrame([{
        "included_studies": total,
        "complete_mean_sd_n_rows": int(complete_numeric),
        "numeric_effect_size_rows": int(effect_numeric),
        "outcome_filled_rows": int(outcome_filled),
        "comparator_filled_rows": int(comparator_filled),
        "unique_outcome_units": int(units),
        "meta_readiness_score": int(score),
        "status": status,
    }])
    return {"score": int(score), "status": status, "reasons": reasons, "table": table}


def novelty_gap_df():
    gaps = generate_gaps()
    p = st.session_state.project
    e = st.session_state.extraction
    rows = []
    for gap in gaps:
        rows.append({"gap_type": "Evidence/Method Gap", "gap_or_insight": gap, "how_to_use_in_manuscript": "Gunakan pada Introduction sebagai novelty atau Discussion sebagai limitation/future research."})
    if not e.empty:
        outcomes = e.get("main_outcome", pd.Series(dtype=str)).replace("", np.nan).dropna().value_counts()
        interventions = e.get("intervention", pd.Series(dtype=str)).replace("", np.nan).dropna().value_counts()
        if len(outcomes) > 0:
            rows.append({"gap_type": "Outcome Pattern", "gap_or_insight": f"Outcome dominan adalah {outcomes.index[0]}; outcome lain masih jarang muncul.", "how_to_use_in_manuscript": "Jelaskan dominasi outcome dan rekomendasikan standardisasi outcome."})
        if len(interventions) > 0:
            rows.append({"gap_type": "Intervention Pattern", "gap_or_insight": f"Intervensi paling sering adalah {interventions.index[0]}; variasi dosis/durasi perlu dibahas.", "how_to_use_in_manuscript": "Gunakan sebagai dasar subgroup/sensitivity atau arah riset masa depan."})
    rows.append({"gap_type": "Novelty Statement Draft", "gap_or_insight": f"Review ini berkontribusi dengan memetakan bukti terkait {p.get('intervention','intervention/exposure')} terhadap {p.get('outcome','main outcome')} pada {p.get('population','target population')}, sekaligus menilai kualitas bukti dan kesiapan meta-analysis.", "how_to_use_in_manuscript": "Masukkan ke akhir Introduction sebagai kontribusi utama."})
    return pd.DataFrame(rows)


def journal_targeting_df():
    p = st.session_state.project
    target = p.get("target_level", "Q1/Q2")
    title_score = analyze_title(p)["score"]
    evidence = infer_evidence_strength()
    prisma_ok = (prisma_compliance_df()["status"] == "Lengkap").mean()
    search_ok = (prisma_s_audit_df()["status"] == "Lengkap").mean()
    meta = meta_analysis_readiness()["score"]
    rows = []
    risk = "Sedang"
    if target == "Q1/Q2" and (title_score < 80 or prisma_ok < 0.65 or evidence["strength"] in ["Terbatas", "Belum dapat dinilai"]):
        risk = "Tinggi"
    elif title_score >= 80 and prisma_ok >= 0.7 and search_ok >= 0.65:
        risk = "Rendah-Sedang"
    rows.append({"aspect": "Scope fit", "score_or_status": "Perlu cek manual", "insight": "Cocokkan domain, outcome, dan jenis artikel dengan Aims & Scope jurnal target.", "recommendation": "Pilih jurnal agro/peternakan/teknik pertanian dan biosistem yang rutin menerbitkan systematic review/meta-analysis."})
    rows.append({"aspect": "Methodological readiness", "score_or_status": f"{prisma_ok*100:.0f}% PRISMA ready", "insight": "Kesiapan metode ditentukan oleh PRISMA, PRISMA-S, risk of bias, dan extraction.", "recommendation": "Lengkapi item PRISMA yang masih Perlu revisi."})
    rows.append({"aspect": "Search transparency", "score_or_status": f"{search_ok*100:.0f}% PRISMA-S ready", "insight": "Search strategy harus bisa direplikasi.", "recommendation": "Simpan search string per database dan tanggal pencarian."})
    rows.append({"aspect": "Evidence strength", "score_or_status": evidence["strength"], "insight": f"Average quality {evidence['avg_quality']:.2f}/8; dominant effect {evidence['dominant_effect']}.", "recommendation": "Gunakan certainty/risk of bias untuk menahan klaim berlebihan."})
    rows.append({"aspect": "Meta-analysis potential", "score_or_status": f"{meta}/100", "insight": meta_analysis_readiness()["status"], "recommendation": "Lengkapi mean, SD, n, satuan outcome, dan effect size bila target Q1/Q2."})
    rows.append({"aspect": "Risk of rejection", "score_or_status": risk, "insight": "Risiko penolakan turun jika metode transparan, novelty kuat, dan hasil tidak hanya deskriptif.", "recommendation": "Gunakan Reviewer Check sebelum submit."})
    return pd.DataFrame(rows)


def reviewer_check_df():
    p = st.session_state.project
    checks = []
    def add(section, issue, severity, action):
        checks.append({"section": section, "potential_reviewer_comment": issue, "severity": severity, "recommended_action": action})
    title = analyze_title(p)
    if title["score"] < 80:
        add("Title/Objective", "Judul dan objective belum cukup spesifik untuk target Q-level.", "Major", "Perbaiki population, intervention/exposure, comparator, outcome, dan jenis review.")
    if (prisma_compliance_df()["status"] == "Lengkap").mean() < 0.7:
        add("Methods", "Pelaporan PRISMA belum lengkap dan metode sulit direplikasi.", "Major", "Lengkapi checklist PRISMA dan jelaskan semua proses screening/extraction.")
    if (prisma_s_audit_df()["status"] == "Lengkap").mean() < 0.65:
        add("Search Strategy", "Search strategy belum cukup transparan.", "Major", "Tuliskan search string per database, tanggal pencarian, filter, dan dokumentasi ekspor.")
    if st.session_state.quality.empty:
        add("Risk of Bias", "Quality/risk of bias assessment belum ada.", "Major", "Gunakan SYRCLE/JBI/ROSES/ROBINS-I sesuai desain studi.")
    if st.session_state.extraction.empty:
        add("Results", "Data extraction belum tersedia sehingga hasil tidak dapat disintesis.", "Major", "Isi tabel ekstraksi dan ringkas karakteristik studi.")
    if meta_analysis_readiness()["score"] < 55 and "Meta-Analysis" in p.get("review_type", ""):
        add("Analysis", "Judul menyebut meta-analysis, tetapi data belum siap untuk meta-analysis.", "Major", "Lengkapi data numerik atau ubah jenis naskah menjadi systematic review/narrative synthesis.")
    if not checks:
        add("Overall", "Naskah secara sistem sudah cukup siap untuk dikembangkan.", "Minor", "Lakukan proofreading, cek jurnal target, dan validasi manual oleh peneliti/pembimbing.")
    return pd.DataFrame(checks)


def build_manuscript_markdown():
    p = st.session_state.project
    counts = get_prisma_counts(True)
    evidence = infer_evidence_strength()
    gaps = novelty_gap_df()
    method = make_methods_template()
    return f"""# {p.get('title','Draft Systematic Review')}

## Abstract
Background: Evidence regarding {p.get('intervention','the intervention/exposure')} for {p.get('population','the target population')} remains fragmented across studies. Objective: This systematic review aimed to synthesize evidence on {p.get('outcome','main outcomes')} using the {p.get('framework','PICOS')} framework. Methods: {p.get('research_question','The research question has not been defined yet.')} Records were screened using predefined inclusion and exclusion criteria. Results: The current database contains {counts['records_database']} records, {counts['duplicates_removed']} duplicates removed, {counts['full_text_assessed']} full-text articles assessed, and {counts['studies_included']} studies included. Conclusion: The evidence strength is currently {evidence['strength']}. Claims should be adjusted to the final quality and risk of bias assessment.

## 1. Introduction
The topic of {p.get('intervention','intervention/exposure')} in {p.get('population','target population')} is relevant for agro, livestock, agricultural engineering and biosystems, food, aquaculture, and environmental research because it is linked to productivity, sustainability, and evidence-based decision making. However, individual studies often differ in design, sample size, treatment dose, duration, comparator, and outcome measures. A systematic review is therefore needed to synthesize the available evidence transparently.

### Research Gap and Novelty
{gaps.iloc[-1]['gap_or_insight'] if not gaps.empty else 'The novelty statement needs to be refined after data extraction.'}

### Objective
This review aims to answer the following question: {p.get('research_question','')}

## 2. Methods
{method}

## 3. Results
The PRISMA flow currently reports {counts['records_database']} database records, {counts['records_screened']} screened records, {counts['full_text_assessed']} full-text assessed records, and {counts['studies_included']} included studies. Study characteristics, outcome direction, and quality assessment should be presented in tables generated from the system.

## 4. Discussion
The current synthesis indicates an evidence strength of {evidence['strength']} with dominant effect direction: {evidence['dominant_effect']}. Discussion should address consistency across studies, heterogeneity sources, risk of bias, certainty of evidence, and practical implications for the target domain.

## 5. Limitations
Potential limitations include database coverage, language and year filters, heterogeneity of intervention/exposure characteristics, variation in outcome measurement, incomplete effect size reporting, and risk of bias in primary studies.

## 6. Implications and Future Research
Future research should standardize outcome reporting, provide complete numerical data for meta-analysis, and explore subgroup factors such as dose, duration, study design, species/commodity, and environmental context.

## 7. Conclusion
The conclusion should be finalized after screening, risk of bias assessment, and data extraction are complete. Avoid overclaiming and align conclusions with the certainty of evidence.
"""


def docx_from_markdown_bytes(markdown_text: str, title: str = "Systematic Review Draft") -> bytes:
    try:
        from docx import Document
        from docx.shared import Pt
    except Exception as exc:
        raise RuntimeError("python-docx belum terpasang. Jalankan: pip install python-docx") from exc
    doc = Document()
    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(11)
    current_list = False
    for raw in markdown_text.splitlines():
        line = raw.strip()
        if not line:
            doc.add_paragraph("")
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=0)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=2)
        elif line.startswith("- "):
            doc.add_paragraph(line[2:].strip(), style="List Bullet")
        elif re.match(r"^\d+\.\s+", line):
            doc.add_paragraph(re.sub(r"^\d+\.\s+", "", line), style="List Number")
        elif line.startswith("```"):
            continue
        else:
            doc.add_paragraph(line.replace("**", ""))
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()


def make_cover_letter_markdown():
    p = st.session_state.project
    return f"""# Cover Letter Template

Dear Editor,

We are pleased to submit our manuscript entitled "{p.get('title','[Manuscript Title]')}" for consideration in your journal. This manuscript presents a systematic review in the field of {p.get('domain','[domain]')} focusing on {p.get('intervention','[intervention/exposure]')} and {p.get('outcome','[outcome]')} in {p.get('population','[population]')}.

The review was structured using the {p.get('framework','PICOS/PECO')} framework and aims to answer the question: {p.get('research_question','[research question]')}

We believe this manuscript is relevant to your journal because it provides a transparent synthesis of current evidence, identifies methodological gaps, and offers implications for future research and practice. The manuscript has not been published or submitted elsewhere.

Sincerely,

[Author Name]
"""


def _json_safe_value(value):
    """Convert values from pandas/numpy into JSON-safe Python values."""
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    return value


def df_to_records_for_state(df: pd.DataFrame, columns: list) -> list:
    """Serialize a DataFrame while preserving the expected column order."""
    if df is None or df.empty:
        return []
    safe_df = df.copy()
    for col in columns:
        if col not in safe_df.columns:
            safe_df[col] = ""
    safe_df = safe_df[columns]
    records = []
    for row in safe_df.to_dict(orient="records"):
        records.append({k: _json_safe_value(v) for k, v in row.items()})
    return records


def records_to_df_from_state(records, columns: list) -> pd.DataFrame:
    """Restore a DataFrame from project-state records and normalize columns."""
    if not records:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(records)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns].fillna("")


def make_resume_project_state(current_page: str = "") -> dict:
    """Create a complete resumable project snapshot."""
    return {
        "app": APP_TITLE,
        "version": APP_VERSION,
        "state_schema": "sr_project_v2",
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "current_page": current_page,
        "project": st.session_state.project,
        "criteria": st.session_state.criteria,
        "terms": st.session_state.terms,
        "articles": df_to_records_for_state(st.session_state.articles, ARTICLE_COLUMNS),
        "quality": df_to_records_for_state(st.session_state.quality, QUALITY_COLUMNS),
        "extraction": df_to_records_for_state(st.session_state.extraction, EXTRACTION_COLUMNS),
        "prisma_manual": st.session_state.prisma_manual,
        "notes": st.session_state.notes,
        "sync_config": st.session_state.sync_config,
        "completion": completion_status()[0],
    }


def resume_project_state_bytes(current_page: str = "") -> bytes:
    return json.dumps(make_resume_project_state(current_page), ensure_ascii=False, indent=2).encode("utf-8")


def load_resume_project_state(uploaded_file):
    """Load a saved .srproj.json/.json project file into session state."""
    try:
        raw = uploaded_file.getvalue().decode("utf-8")
        data = json.loads(raw)
    except Exception as exc:
        return False, f"File tidak dapat dibaca sebagai JSON project: {exc}"

    required_any = ["project", "criteria", "terms"]
    if not any(key in data for key in required_any):
        return False, "File tidak dikenali sebagai project systematic review. Pastikan file berasal dari tombol Download Project State."

    # Support older project_state.json exports that only stored project/criteria/terms.
    st.session_state.project = data.get("project", st.session_state.project)
    st.session_state.criteria = data.get("criteria", st.session_state.criteria)
    st.session_state.terms = data.get("terms", st.session_state.terms)
    st.session_state.prisma_manual = data.get("prisma_manual", st.session_state.prisma_manual)
    st.session_state.notes = data.get("notes", st.session_state.notes)
    st.session_state.sync_config = data.get("sync_config", st.session_state.sync_config)

    st.session_state.articles = records_to_df_from_state(data.get("articles", []), ARTICLE_COLUMNS)
    st.session_state.quality = records_to_df_from_state(data.get("quality", []), QUALITY_COLUMNS)
    st.session_state.extraction = records_to_df_from_state(data.get("extraction", []), EXTRACTION_COLUMNS)

    # Normalize derived columns and relationships after restore.
    if not st.session_state.articles.empty:
        st.session_state.articles = flag_duplicates(st.session_state.articles)
        st.session_state.articles = update_dual_reviewer_consensus(st.session_state.articles)
        st.session_state.articles = apply_relevance_scoring(st.session_state.articles)
    sync_quality_extraction()
    st.session_state.sync_config["last_sync"] = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (project dilanjutkan dari file)"
    return True, "Project berhasil dimuat. Anda bisa melanjutkan dari langkah terakhir tanpa mulai dari awal."


def make_step_snapshot(step_name: str) -> bytes:
    """Create a smaller downloadable snapshot for the active step while still keeping the project resumable."""
    state = make_resume_project_state(step_name)
    state["step_snapshot"] = step_name
    return json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")



def make_ai_usage_guide_markdown() -> str:
    lines = [
        "# Panduan Penggunaan AI Insight",
        "",
        "Panduan ini membantu peneliti memilih model, jenis insight, dan instruksi tambahan agar output AI lebih sesuai untuk systematic review bidang agro, peternakan, pangan, perikanan, lingkungan, serta teknik pertanian dan biosistem.",
        "",
        "## 1. Saran memilih model",
    ]
    for strategy, tips in AI_MODEL_USAGE_GUIDANCE.items():
        lines.append(f"\n### {strategy}")
        for tip in tips:
            lines.append(f"- {tip}")
    lines.extend([
        "",
        "## 2. Saran berdasarkan jenis insight",
    ])
    for task, guide in AI_TASK_GUIDANCE.items():
        lines.append(f"\n### {task}")
        lines.append(f"**Tujuan:** {guide.get('tujuan', '-')}")
        lines.append(f"**Cocok digunakan jika:** {guide.get('cocok_jika', '-')}")
        inputs = guide.get("input_utama", [])
        if inputs:
            lines.append("**Data yang sebaiknya dilengkapi:** " + ", ".join(inputs))
        lines.append("**Contoh instruksi tambahan:**")
        for example in guide.get("instruksi_contoh", []):
            lines.append(f"- {example}")
        lines.append(f"**Ciri output yang baik:** {guide.get('output_baik', '-')}")
    lines.extend([
        "",
        "## 3. Prinsip agar hasil AI sesuai",
        "- Lengkapi judul, framework, population, intervention/exposure, comparator, outcome, dan study design sebelum meminta insight.",
        "- Lengkapi screening, quality assessment, dan data extraction agar AI tidak hanya memberi saran umum.",
        "- Beri instruksi tambahan yang spesifik, misalnya target Q1/Q2, bidang, komoditas, bagian naskah yang ingin diperbaiki, dan batas panjang output.",
        "- Jangan meminta AI membuat sitasi atau angka baru yang belum ada pada data project.",
        "- Validasi semua hasil AI dengan artikel asli dan kaidah PRISMA/ROSES sebelum digunakan dalam naskah.",
    ])
    return "\n".join(lines)

def make_export_zip():
    mem = BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("protocol_systematic_review.md", make_protocol_markdown())
        z.writestr("methods_template.md", make_methods_template())
        z.writestr("evidence_insight_report.md", build_insight_report())
        z.writestr("examples_and_guidance.md", make_guidance_markdown())
        z.writestr("ai_usage_guide.md", make_ai_usage_guide_markdown())
        z.writestr("q_level_manuscript_draft.md", build_manuscript_markdown())
        z.writestr("cover_letter_template.md", make_cover_letter_markdown())
        z.writestr("q_level_manuscript_draft.docx", docx_from_markdown_bytes(build_manuscript_markdown(), "Systematic Review Draft"))
        z.writestr("cover_letter_template.docx", docx_from_markdown_bytes(make_cover_letter_markdown(), "Cover Letter"))
        z.writestr("screening_results.xlsx", df_to_xlsx_bytes(st.session_state.articles, "Screening"))
        z.writestr("quality_assessment.xlsx", df_to_xlsx_bytes(st.session_state.quality, "Quality"))
        z.writestr("data_extraction.xlsx", df_to_xlsx_bytes(st.session_state.extraction, "Extraction"))
        z.writestr("prisma_counts.xlsx", df_to_xlsx_bytes(pd.DataFrame([get_prisma_counts(True)]), "PRISMA"))
        z.writestr("prisma_2020_compliance.xlsx", df_to_xlsx_bytes(prisma_compliance_df(), "PRISMA_Checklist"))
        z.writestr("prisma_s_search_audit.xlsx", df_to_xlsx_bytes(prisma_s_audit_df(), "PRISMA_S"))
        z.writestr("meta_analysis_readiness.xlsx", df_to_xlsx_bytes(meta_analysis_readiness()["table"], "Meta_Readiness"))
        z.writestr("novelty_gap_analysis.xlsx", df_to_xlsx_bytes(novelty_gap_df(), "Novelty_Gap"))
        z.writestr("journal_targeting.xlsx", df_to_xlsx_bytes(journal_targeting_df(), "Journal_Targeting"))
        z.writestr("reviewer_check.xlsx", df_to_xlsx_bytes(reviewer_check_df(), "Reviewer_Check"))
        for ai_name, ai_text in st.session_state.get("ai_outputs", {}).items():
            safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", str(ai_name)).strip("_").lower() or "ai_insight"
            z.writestr(f"online_ai_{safe_name}.md", str(ai_text))
        z.writestr("project_state.srproj.json", resume_project_state_bytes("Export ZIP"))
        z.writestr("project_state_README.txt", "Gunakan file project_state.srproj.json pada menu sidebar 'Simpan & lanjutkan project' untuk melanjutkan pekerjaan tanpa mulai dari awal. API key pribadi dan API Base URL tidak disimpan di file project/export.")
    mem.seek(0)
    return mem.getvalue()


def download_df_button(label, df, filename):
    if not filename.lower().endswith(".xlsx"):
        filename = filename.rsplit(".", 1)[0] + ".xlsx"
    st.download_button(
        label,
        df_to_xlsx_bytes(df, filename.rsplit(".", 1)[0][:31]),
        filename,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )



def clear_personal_api_key():
    """Remove the user-provided API key and cached model list from the current Streamlit session only."""
    for key in [
        "personal_openai_api_key", "openai_api_key_input", "personal_api_base_url", "api_base_url_input",
        "openai_available_models", "openai_models_last_checked", "openai_models_error", "openai_models_api_base",
        "manual_model_select", "manual_model_text",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def sanitize_api_key(raw_key: str) -> str:
    """Accept raw API keys or pasted Authorization headers and return only the token.

    Users sometimes paste `Bearer sk-...` or `Authorization: Bearer sk-...`.
    If we prepend Bearer again, providers reject it as an invalid key.
    This sanitizer prevents the common `Bearer Bearer ...` problem without
    storing or displaying the key.
    """
    value = str(raw_key or "").strip().strip('"').strip("'")
    if not value:
        return ""
    # Allow users to paste the full header line.
    value = re.sub(r"^Authorization\s*:\s*", "", value, flags=re.I).strip()
    value = re.sub(r"^Bearer\s+", "", value, flags=re.I).strip()
    # Keep the first non-empty line only, in case the pasted text contains notes.
    for line in value.splitlines():
        line = line.strip()
        if line:
            return line
    return value


def get_personal_api_key() -> str:
    """Read the optional personal API key from session state without persisting it."""
    return sanitize_api_key(st.session_state.get("personal_openai_api_key", ""))


def normalize_api_base_url(api_base: str) -> str:
    """Normalize user supplied API base so requests use {base}/v1/... consistently.

    Users may paste either a base URL such as `https://api-base`, `https://api-base/v1`,
    or the full endpoint `https://api-base/v1/chat/completions`. This function safely
    reduces all of them to `https://api-base`.
    """
    base = str(api_base or SLASHAI_DEFAULT_API_BASE).strip().rstrip("/")
    if not base:
        base = SLASHAI_DEFAULT_API_BASE
    lower = base.lower()
    for suffix in ["/v1/chat/completions", "/chat/completions", "/v1/models", "/models"]:
        if lower.endswith(suffix):
            base = base[: -len(suffix)].rstrip("/")
            lower = base.lower()
            break
    if lower.endswith("/v1"):
        base = base[:-3].rstrip("/")
    return base


def get_personal_api_base_url() -> str:
    """Read optional OpenAI-compatible API base URL from the current session only."""
    return normalize_api_base_url(st.session_state.get("personal_api_base_url", SLASHAI_DEFAULT_API_BASE))


def chat_completions_url(api_base: str) -> str:
    return f"{normalize_api_base_url(api_base)}/v1/chat/completions"


def models_url(api_base: str) -> str:
    return f"{normalize_api_base_url(api_base)}/v1/models"


def build_bearer_headers(api_key: str, model: str | None = None) -> dict:
    """Build headers for OpenAI-compatible APIs.

    Some gateway providers, including SlashAI-style routers, may document the model as
    a request header. The app therefore sends the selected model in the JSON body
    and, when available, also in a safe `model` header for compatibility.
    """
    safe_key = sanitize_api_key(api_key)
    headers = {
        "Authorization": f"Bearer {safe_key}",
        "Content-Type": "application/json",
    }
    if model:
        headers["model"] = str(model)
    return headers


def safe_json_loads_lenient(text: str):
    """Parse JSON from strict JSON, first JSON object, or simple SSE data lines.

    Some OpenAI-compatible gateways return a valid JSON object followed by extra
    text/newlines, or return SSE-like `data: {...}` lines. Python's standard
    `response.json()` raises `Extra data` in those cases. This helper keeps the
    app usable and falls back gracefully.
    """
    raw = str(text or "").strip()
    if not raw:
        raise ValueError("Respons kosong.")
    try:
        return json.loads(raw)
    except Exception as first_exc:
        # Server-sent-event style: data: {json}
        data_lines = []
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                content = line[5:].strip()
                if content and content != "[DONE]":
                    data_lines.append(content)
        for item in reversed(data_lines):
            try:
                return json.loads(item)
            except Exception:
                continue

        # Concatenated JSON / JSON followed by text: decode only the first object.
        try:
            decoder = json.JSONDecoder()
            payload, _ = decoder.raw_decode(raw)
            return payload
        except Exception:
            raise first_exc


def response_payload_lenient(response):
    """Return parsed JSON payload if possible, otherwise None."""
    try:
        return response.json()
    except Exception:
        try:
            return safe_json_loads_lenient(getattr(response, "text", ""))
        except Exception:
            return None


def extract_model_ids_from_payload_or_text(payload=None, text: str = "") -> list[str]:
    """Extract model IDs from common JSON structures or SlashAI-style text lists."""
    models = []
    if isinstance(payload, dict):
        candidates = payload.get("data") or payload.get("models") or payload.get("model") or []
        if isinstance(candidates, str):
            candidates = [candidates]
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict):
                    mid = item.get("id") or item.get("name") or item.get("model")
                    if mid:
                        models.append(str(mid))
                elif isinstance(item, str):
                    models.append(item)
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                mid = item.get("id") or item.get("name") or item.get("model")
                if mid:
                    models.append(str(mid))
            elif isinstance(item, str):
                models.append(item)

    raw_text = str(text or "")
    if raw_text:
        # Supports the user's pasted SlashAI list: "slashai/gpt-5.5", etc.
        models.extend(re.findall(r"slashai/[A-Za-z0-9_.\-]+", raw_text))
        # Also supports plain OpenAI-compatible IDs if a provider returns one per line.
        for line in raw_text.splitlines():
            candidate = line.strip().strip("`*•- ")
            if re.match(r"^(gpt|o\d|claude|gemini|deepseek|qwen|glm|kimi|minimax|mimo|step)[A-Za-z0-9_./\-]*$", candidate, re.I):
                models.append(candidate)

    return sort_model_ids([m for m in dict.fromkeys(models) if is_probable_text_model(m)])


def compact_api_error(response) -> str:
    """Create a safe error message without exposing key/header values."""
    payload = response_payload_lenient(response)
    if isinstance(payload, dict):
        detail = payload.get("error") or payload.get("message") or payload
        if isinstance(detail, dict):
            detail = detail.get("message") or detail.get("type") or detail
        return str(detail)[:500]
    text = str(getattr(response, "text", "") or "").strip()
    return text[:500] if text else f"HTTP {getattr(response, 'status_code', '')}"


def classify_api_error(status_code: int, detail: str, endpoint: str = "", model: str = "") -> str:
    """Return a more precise, user-facing API error diagnosis.

    Many OpenAI-compatible gateways return 403 for reasons other than a revoked key.
    SlashAI may return `access_denied` with `Deposit required to unlock pre`. In that
    case the correct action is topping up/unlocking the provider access or choosing
    a model that the account can access, not retyping the key repeatedly.
    """
    d = str(detail or "")
    dl = d.lower()
    prefix = f"Endpoint: {endpoint}. Model: {model}. Detail server: {d}"

    if "deposit required" in dl or "unlock pre" in dl or "saldo" in dl or "top up" in dl or "topup" in dl:
        return (
            "Server menolak request karena akun/API key belum memiliki akses saldo/deposit untuk model yang dipilih. "
            "API key masih bisa benar, tetapi provider meminta deposit/akses premium terlebih dahulu. "
            "Solusi: lakukan deposit/top up di provider SlashAI, tunggu beberapa detik sesuai pesan server bila ada reset, "
            "atau coba mode `Pilih manual` dengan model yang lebih ringan/flash. "
            f"{prefix}"
        )
    if "access_denied" in dl or "access denied" in dl or "restricted" in dl or "not allowed" in dl:
        return (
            "Server menolak akses untuk model/API base yang dipilih. Ini belum tentu API key dicabut; "
            "bisa karena model belum terbuka untuk akun tersebut, region/provider membatasi akses, atau akun belum memenuhi syarat. "
            f"{prefix}"
        )
    if "invalid" in dl and ("key" in dl or "token" in dl or "api" in dl):
        return (
            "API key/token tampak tidak valid menurut server. Pastikan yang ditempel hanya token atau `Bearer <token>`, "
            "tanpa spasi/teks tambahan. "
            f"{prefix}"
        )
    if status_code == 401:
        return (
            "Server meminta autentikasi ulang (401). Biasanya karena API key kosong, salah format, atau tidak diterima provider. "
            f"{prefix}"
        )
    if status_code == 403:
        return (
            "Server menolak otorisasi (403). Ini bisa terjadi karena akses model tidak tersedia untuk API key, "
            "akun belum deposit/top up, atau API base tidak cocok. "
            f"{prefix}"
        )
    if status_code == 429:
        return (
            "Limit/rate limit API tercapai atau saldo/quota akun API tidak mencukupi. "
            "Coba ulang setelah beberapa saat, ganti model yang lebih ringan, atau cek saldo/provider. "
            f"{prefix}"
        )
    if status_code == 404:
        return (
            "Endpoint atau model tidak ditemukan. Pastikan API Base benar dan model memakai ID yang didukung provider. "
            f"{prefix}"
        )
    return f"Gagal memanggil API ({status_code}). {prefix}"


def build_ai_project_context(max_records: int = 25) -> str:
    """Create a compact JSON context for optional online AI insight.

    The context intentionally excludes API keys, Streamlit session internals, and raw files.
    It only includes systematic-review project data that the user has entered/imported.
    """
    counts = get_prisma_counts(True)
    evidence = infer_evidence_strength()
    title_result = analyze_title(st.session_state.project)

    def limited_records(df: pd.DataFrame, cols: list, limit: int = max_records):
        if df is None or df.empty:
            return []
        available = [c for c in cols if c in df.columns]
        return df[available].head(limit).fillna("").to_dict(orient="records")

    payload = {
        "project": st.session_state.project,
        "criteria": st.session_state.criteria,
        "framework": st.session_state.project.get("framework", "PICOS"),
        "search_strategy": build_search_string(st.session_state.terms),
        "search_terms": st.session_state.terms,
        "prisma_counts": counts,
        "offline_title_analysis": title_result,
        "offline_evidence_summary": evidence,
        "recommendations_rule_based": generate_recommendations(),
        "screening_sample": limited_records(
            st.session_state.articles,
            ["id", "title", "year", "journal", "country", "source_database", "picos_relevance_score", "reviewer1_decision", "reviewer2_decision", "consensus_decision", "screening_decision", "full_text_decision", "exclusion_reason"],
        ),
        "quality_sample": limited_records(
            st.session_state.quality,
            ["id", "title", "quality_score", "quality_category", "overall_risk_of_bias", "certainty_of_evidence", "grade_downgrade_reason"],
        ),
        "extraction_sample": limited_records(
            st.session_state.extraction,
            ["id", "title", "species_or_crop", "intervention", "comparator", "main_outcome", "outcome_unit", "effect_direction", "effect_size", "key_finding", "limitations", "implication", "novelty_note"],
        ),
        "notes": st.session_state.notes,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)



SLASHAI_MODEL_CATALOG = {
    "Claude": [
        "slashai/claude-haiku-4.5",
        "slashai/claude-opus-4.5",
        "slashai/claude-opus-4.6",
        "slashai/claude-opus-4.7",
        "slashai/claude-sonnet-4.5",
        "slashai/claude-sonnet-4.6",
        "slashai/claude-sonnet-4.7",
    ],
    "GPT / Codex": [
        "slashai/gpt-5-codex",
        "slashai/gpt-5-codex-mini",
        "slashai/gpt-5-codex-mini-review",
        "slashai/gpt-5-codex-review",
        "slashai/gpt-5-mini",
        "slashai/gpt-5-nano",
        "slashai/gpt-5.1",
        "slashai/gpt-5.1-codex",
        "slashai/gpt-5.1-codex-max",
        "slashai/gpt-5.1-codex-max-review",
        "slashai/gpt-5.1-codex-mini",
        "slashai/gpt-5.1-codex-mini-high",
        "slashai/gpt-5.1-codex-mini-high-review",
        "slashai/gpt-5.1-codex-mini-review",
        "slashai/gpt-5.1-codex-review",
        "slashai/gpt-5.1-review",
        "slashai/gpt-5.2",
        "slashai/gpt-5.2-codex",
        "slashai/gpt-5.2-codex-review",
        "slashai/gpt-5.2-review",
        "slashai/gpt-5.3-codex",
        "slashai/gpt-5.3-codex-high",
        "slashai/gpt-5.3-codex-high-review",
        "slashai/gpt-5.3-codex-low",
        "slashai/gpt-5.3-codex-low-review",
        "slashai/gpt-5.3-codex-none",
        "slashai/gpt-5.3-codex-none-review",
        "slashai/gpt-5.3-codex-review",
        "slashai/gpt-5.3-codex-spark",
        "slashai/gpt-5.3-codex-spark-review",
        "slashai/gpt-5.3-codex-xhigh",
        "slashai/gpt-5.3-codex-xhigh-review",
        "slashai/gpt-5.4",
        "slashai/gpt-5.4-mini",
        "slashai/gpt-5.4-nano",
        "slashai/gpt-5.4-pro",
        "slashai/gpt-5.4-review",
        "slashai/gpt-5.5",
        "slashai/gpt-5.5-instant",
        "slashai/gpt-5.5-review",
    ],
    "DeepSeek": [
        "slashai/deepseek-3.2",
        "slashai/deepseek-v3.2",
        "slashai/deepseek-v4-flash",
        "slashai/deepseek-v4-pro",
    ],
    "Gemini": [
        "slashai/gemini-3-flash",
        "slashai/gemini-3.1-pro",
    ],
    "Kimi": [
        "slashai/Kimi-K2.5",
        "slashai/Kimi-K2.6",
    ],
    "Qwen": [
        "slashai/qwen3-coder-next",
        "slashai/Qwen3.6-Max-Preview",
        "slashai/Qwen3.6-Plus",
    ],
    "GLM": [
        "slashai/GLM-5",
        "slashai/GLM-5.1",
    ],
    "MiniMax": [
        "slashai/MiniMax-M2.5",
        "slashai/MiniMax-M2.7",
    ],
    "MiMo": [
        "slashai/mimo-v2-flash",
        "slashai/mimo-v2-omni",
        "slashai/mimo-v2-pro",
        "slashai/mimo-v2.5",
        "slashai/mimo-v2.5-pro",
    ],
    "Step": [
        "slashai/Step-3.5-Flash",
    ],
}

SLASHAI_ALL_MODELS = [m for group in SLASHAI_MODEL_CATALOG.values() for m in group]

ECONOMY_MODEL_FALLBACK = "slashai/gemini-3-flash"
QUALITY_MODEL_FALLBACK = "slashai/gemini-3.1-pro"
ECONOMY_MODEL_PRIORITY = [
    # Prioritise lighter/flash models first because some premium/pre models may require deposit.
    "slashai/gemini-3-flash",
    "slashai/deepseek-v4-flash",
    "slashai/mimo-v2-flash",
    "slashai/Step-3.5-Flash",
    "slashai/gpt-5.4-nano",
    "slashai/gpt-5-nano",
    "slashai/gpt-5.4-mini",
    "slashai/gpt-5-mini",
    "slashai/gpt-5-codex-mini",
    "slashai/claude-haiku-4.5",
    "slashai/gpt-5.5-instant",
    "gpt-5.5-instant", "gpt-5.4-mini", "gpt-5-mini", "gpt-4.1-mini", "gpt-4o-mini", "o4-mini", "o3-mini",
]
QUALITY_MODEL_PRIORITY = [
    # Start with stronger non-GPT/provider-generic choices first. SlashAI GPT 5.x premium models may require deposit.
    "slashai/gemini-3.1-pro",
    "slashai/deepseek-v4-pro",
    "slashai/Qwen3.6-Max-Preview",
    "slashai/claude-sonnet-4.7",
    "slashai/GLM-5.1",
    "slashai/gemini-3-flash",
    "slashai/deepseek-v4-flash",
    "slashai/mimo-v2-pro",
    "slashai/gpt-5.5",
    "slashai/gpt-5.4-pro",
    "slashai/gpt-5.4",
    "slashai/gpt-5.2",
    "slashai/gpt-5.1",
    "slashai/claude-opus-4.7",
    "gpt-5.5", "gpt-5.4", "gpt-5.2", "gpt-5.1", "gpt-5", "gpt-4.1", "gpt-4o", "o3",
]

SAFE_RETRY_MODEL_PRIORITY = [
    "slashai/gemini-3-flash",
    "slashai/deepseek-v4-flash",
    "slashai/mimo-v2-flash",
    "slashai/Step-3.5-Flash",
    "slashai/gpt-5.4-nano",
    "slashai/gpt-5-nano",
    "slashai/gpt-5-mini",
]


def is_probable_text_model(model_id: str) -> bool:
    """Keep model choices relevant for text insight generation, including SlashAI router IDs."""
    mid = str(model_id or "").strip().lower()
    if not mid:
        return False
    excluded_fragments = [
        "embedding", "moderation", "tts", "transcribe", "whisper", "image", "dall", "realtime",
        "audio", "vision", "computer-use", "search", "guardrail",
    ]
    if any(fragment in mid for fragment in excluded_fragments):
        return False
    allowed_fragments = [
        "gpt", "codex", "claude", "deepseek", "gemini", "kimi", "qwen", "glm", "minimax", "mimo", "step",
    ]
    if mid.startswith("slashai/"):
        return any(fragment in mid for fragment in allowed_fragments)
    return mid.startswith("gpt-") or re.match(r"^o\d", mid) is not None or any(fragment in mid for fragment in allowed_fragments)


def sort_model_ids(model_ids: list[str]) -> list[str]:
    """Sort text model IDs with SlashAI economy/quality choices first while keeping deterministic order."""
    cleaned = sorted({str(m).strip() for m in model_ids if str(m).strip()})
    priority_order = {m.lower(): i for i, m in enumerate(ECONOMY_MODEL_PRIORITY + QUALITY_MODEL_PRIORITY)}

    def rank(mid: str):
        m = mid.lower()
        if m in priority_order:
            group = 0
            pos = priority_order[m]
        elif m.startswith("slashai/gpt"):
            group = 1
            pos = 0
        elif "claude" in m:
            group = 2
            pos = 0
        elif "gemini" in m:
            group = 3
            pos = 0
        elif any(x in m for x in ["deepseek", "qwen", "glm", "kimi", "minimax", "mimo", "step"]):
            group = 4
            pos = 0
        elif m.startswith("gpt-5"):
            group = 5
            pos = 0
        elif m.startswith("gpt-4.1"):
            group = 6
            pos = 0
        elif m.startswith("gpt-4o"):
            group = 7
            pos = 0
        elif re.match(r"^o\d", m):
            group = 8
            pos = 0
        else:
            group = 9
            pos = 0
        size_bonus = 0 if any(x in m for x in ["instant", "nano", "mini", "flash"]) else 1
        return (group, pos, size_bonus, m)

    return sorted(cleaned, key=rank)


def list_openai_models_with_key(api_key: str, api_base: str | None = None) -> tuple[bool, list[str] | str]:
    """List text-capable model IDs via OpenAI-compatible GET {api_base}/v1/models."""
    if not api_key:
        return False, "API key belum diisi."
    base = normalize_api_base_url(api_base or get_personal_api_base_url())
    try:
        response = requests.get(
            models_url(base),
            headers=build_bearer_headers(api_key),
            timeout=45,
        )
        if response.status_code >= 400:
            detail = compact_api_error(response)
            msg = classify_api_error(response.status_code, detail, models_url(base), "model-list")
            # Reading /v1/models is optional. Keep the app usable with built-in SlashAI models.
            st.session_state.openai_models_error = msg
            st.session_state.openai_available_models = sort_model_ids(SLASHAI_ALL_MODELS)
            st.session_state.openai_models_last_checked = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.openai_models_api_base = base
            return True, st.session_state.openai_available_models

        payload = response_payload_lenient(response)
        models = extract_model_ids_from_payload_or_text(payload, getattr(response, "text", ""))
        if not models:
            msg = (
                "Endpoint /v1/models tidak mengembalikan daftar model dalam format JSON/list yang bisa dibaca. "
                "Ini tidak menghambat Online AI; sistem tetap memakai daftar model bawaan SlashAI. "
                "Anda juga bisa memilih/menulis model manual seperti slashai/gpt-5.5-instant atau slashai/gpt-5.5."
            )
            st.session_state.openai_models_error = msg
            st.session_state.openai_available_models = sort_model_ids(SLASHAI_ALL_MODELS)
            st.session_state.openai_models_last_checked = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.openai_models_api_base = base
            return True, st.session_state.openai_available_models
        st.session_state.openai_available_models = models
        st.session_state.openai_models_last_checked = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.openai_models_api_base = base
        if "openai_models_error" in st.session_state:
            del st.session_state["openai_models_error"]
        return True, models
    except requests.exceptions.RequestException as exc:
        msg = f"Gagal terhubung ke API base {base}: {exc}"
        st.session_state.openai_models_error = msg
        return False, msg
    except Exception as exc:
        msg = f"Gagal membaca daftar model: {exc}"
        st.session_state.openai_models_error = msg
        return False, msg


def choose_model_from_available(available_models: list[str], strategy: str) -> tuple[str, str]:
    """Resolve the effective model from automatic/manual strategy."""
    available = sort_model_ids(available_models or [])
    available_lc = {m.lower(): m for m in available}
    priority = ECONOMY_MODEL_PRIORITY if strategy == "Auto pilih model hemat biaya" else QUALITY_MODEL_PRIORITY

    for candidate in priority:
        if candidate.lower() in available_lc:
            return available_lc[candidate.lower()], "daftar model API"
    for candidate in priority:
        prefix_matches = [m for m in available if m.lower().startswith(candidate.lower() + "-")]
        if prefix_matches:
            return prefix_matches[0], "daftar model API"
    if available:
        # For economy, prefer mini/smaller if present; for quality, prefer the first ranked high-capability model.
        if strategy == "Auto pilih model hemat biaya":
            mini = [m for m in available if "mini" in m.lower()]
            if mini:
                return mini[0], "daftar model API"
        return available[0], "daftar model API"
    fallback = ECONOMY_MODEL_FALLBACK if strategy == "Auto pilih model hemat biaya" else QUALITY_MODEL_FALLBACK
    return fallback, "fallback default"


def get_effective_ai_model(api_key: str = "") -> tuple[str, str]:
    """Return model ID and source without persisting API key."""
    ai_cfg = st.session_state.get("ai_config", {})
    strategy = ai_cfg.get("model_selection", "Auto pilih model hemat biaya")
    available = st.session_state.get("openai_available_models", [])

    if strategy == "Pilih manual":
        manual = str(ai_cfg.get("manual_model") or ai_cfg.get("model") or ECONOMY_MODEL_FALLBACK).strip()
        return manual or ECONOMY_MODEL_FALLBACK, "pilihan manual"

    model, source = choose_model_from_available(available, strategy)
    ai_cfg["model"] = model
    ai_cfg["selected_model_source"] = source
    st.session_state.ai_config = ai_cfg
    return model, source


def is_deposit_or_access_error(message: str) -> bool:
    """Detect provider-side model access/deposit errors from a user-facing message."""
    text = str(message or "").lower()
    return any(token in text for token in [
        "deposit required", "unlock premium", "unlock pre", "saldo", "top up", "topup",
        "access_denied", "access restricted", "belum memiliki akses saldo", "akses premium",
    ])


def build_retry_model_list(primary_model: str, strategy: str = "") -> list[str]:
    """Return safe fallback models without repeating the primary model."""
    candidates = []
    # For high-quality automatic mode, try pro/non-GPT first, then safe flash.
    if strategy == "Auto pilih model kualitas tinggi":
        candidates.extend(["slashai/gemini-3.1-pro", "slashai/deepseek-v4-pro", "slashai/Qwen3.6-Max-Preview"])
    candidates.extend(SAFE_RETRY_MODEL_PRIORITY)
    seen = {str(primary_model or "").strip().lower()}
    out = []
    for model_id in candidates:
        key = str(model_id).strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(model_id)
    return out


def call_chat_completions_once(api_key: str, model: str, user_prompt: str, api_base: str | None = None) -> tuple[bool, str]:
    """Single OpenAI-compatible Chat Completions request without automatic retry."""
    if not api_key:
        return False, "API key belum diisi. Gunakan Offline Mode atau masukkan API key pribadi terlebih dahulu."
    base = normalize_api_base_url(api_base or get_personal_api_base_url())
    url = chat_completions_url(base)
    system_message = (
        "You are an academic systematic review assistant for agriculture, livestock, aquaculture, food science, "
        "agricultural engineering and biosystems, and environmental evidence synthesis. Analyze only the provided project data. "
        "Do not fabricate citations, databases, study counts, or numerical results. Write in formal Bahasa Indonesia, "
        "concise but useful for manuscript improvement toward reputable journals. When evidence is insufficient, say exactly "
        "what is missing and what the researcher should complete."
    )
    body = {
        "model": model or ECONOMY_MODEL_FALLBACK,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 2200,
        "stream": False,
    }

    try:
        response = requests.post(
            url,
            headers=build_bearer_headers(api_key, model),
            json=body,
            timeout=120,
        )
        if response.status_code >= 400:
            detail = compact_api_error(response)
            return False, classify_api_error(response.status_code, detail, url, model)

        payload = response_payload_lenient(response)
        if isinstance(payload, dict):
            choices = payload.get("choices", [])
            if choices:
                message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
                content = message.get("content") if isinstance(message, dict) else None
                if isinstance(content, list):
                    parts = []
                    for part in content:
                        if isinstance(part, dict):
                            parts.append(str(part.get("text") or part.get("content") or ""))
                        else:
                            parts.append(str(part))
                    content = "\n".join([part for part in parts if part])
                if content:
                    return True, str(content)
                if isinstance(choices[0], dict) and choices[0].get("text"):
                    return True, str(choices[0].get("text"))
            for key in ["content", "text", "message", "response", "output"]:
                if payload.get(key):
                    return True, str(payload.get(key))
            return True, json.dumps(payload, ensure_ascii=False, indent=2)

        raw_text = str(getattr(response, "text", "") or "").strip()
        if raw_text:
            return True, raw_text[:8000]
        return False, "API mengembalikan respons kosong atau format yang belum dikenali."
    except requests.exceptions.RequestException as exc:
        return False, f"Gagal terhubung ke API base {base}: {exc}"
    except Exception as exc:
        return False, f"Gagal membuat AI insight: {exc}"

def call_openai_responses_api(api_key: str, model: str, user_prompt: str, api_base: str | None = None) -> tuple[bool, str]:
    """Call Chat Completions API; retry lighter models when SlashAI denies premium/deposit access."""
    if not api_key:
        return False, "API key belum diisi. Gunakan Offline Mode atau masukkan API key pribadi terlebih dahulu."

    ai_cfg = st.session_state.get("ai_config", {})
    strategy = ai_cfg.get("model_selection", "Auto pilih model hemat biaya")
    primary_model = model or ECONOMY_MODEL_FALLBACK

    ok, result = call_chat_completions_once(api_key, primary_model, user_prompt, api_base)
    if ok:
        st.session_state["last_successful_ai_model"] = primary_model
        return True, result

    # Manual mode should respect the model chosen by the user and show a clear diagnosis.
    if strategy == "Pilih manual" or not is_deposit_or_access_error(result):
        return False, result

    tried = [primary_model]
    retry_errors = []
    for fallback_model in build_retry_model_list(primary_model, strategy):
        tried.append(fallback_model)
        ok2, result2 = call_chat_completions_once(api_key, fallback_model, user_prompt, api_base)
        if ok2:
            st.session_state["last_successful_ai_model"] = fallback_model
            note = (
                f"\n\n---\nCatatan sistem: model awal `{primary_model}` ditolak oleh provider karena akses/deposit. "
                f"Sistem otomatis memakai fallback `{fallback_model}`. Model yang dicoba: {', '.join(tried)}."
            )
            return True, str(result2) + note
        retry_errors.append(f"{fallback_model}: {str(result2)[:280]}")

    return False, (
        f"Model awal `{primary_model}` ditolak dan semua fallback ringan juga gagal. "
        "Ini biasanya karena akun/API key belum memiliki saldo/deposit atau provider membatasi akses model. "
        "Coba lakukan deposit/top up di SlashAI, tunggu reset yang disebut server, atau pilih manual model lain. "
        f"Model yang dicoba: {', '.join(tried)}. Detail terakhir: {retry_errors[-1] if retry_errors else result}"
    )


def test_chat_completion_connection(api_key: str, model: str, api_base: str | None = None) -> tuple[bool, str]:
    """Send a tiny chat completion request to verify API key, model, and endpoint together."""
    if not api_key:
        return False, "API key belum diisi."
    ok, result = call_openai_responses_api(
        api_key=api_key,
        model=model or ECONOMY_MODEL_FALLBACK,
        user_prompt="Balas hanya dengan kata OK jika koneksi berhasil.",
        api_base=api_base or get_personal_api_base_url(),
    )
    if ok:
        preview = str(result).strip().replace("\n", " ")[:200]
        return True, f"Koneksi Chat Completions berhasil. Respons ringkas: {preview}"
    return False, result



AI_TASK_GUIDANCE = {
    "Novelty & Gap Insight": {
        "tujuan": "Mencari celah riset, kontribusi ilmiah, dan arah novelty yang bisa ditulis di Introduction dan Discussion.",
        "input_utama": ["judul", "PICO/PICOS/PECO", "artikel include", "quality assessment", "data extraction", "catatan novelty"],
        "cocok_jika": "Peneliti ingin memastikan topik tidak hanya rangkuman biasa, tetapi punya kontribusi ilmiah yang jelas.",
        "instruksi_contoh": [
            "Fokuskan novelty pada bidang agro tropis dan implikasi praktis untuk petani/peternak.",
            "Bedakan gap metodologis, gap populasi/komoditas, gap outcome, dan gap wilayah penelitian.",
            "Buatkan 3 alternatif novelty statement untuk bagian akhir Introduction.",
        ],
        "output_baik": "Berisi gap spesifik, alasan gap penting, bagaimana gap didukung data project, dan kalimat novelty yang tidak berlebihan.",
    },
    "Discussion Draft": {
        "tujuan": "Membantu membuat narasi Discussion awal berbasis data, bukan sekadar mengulang hasil.",
        "input_utama": ["arah efek", "outcome utama", "risk of bias", "certainty of evidence", "keterbatasan studi", "implikasi"],
        "cocok_jika": "Data extraction dan quality assessment sudah mulai terisi sehingga AI punya bahan untuk interpretasi.",
        "instruksi_contoh": [
            "Susun discussion dalam 4 paragraf: pola temuan, penyebab heterogenitas, kualitas bukti, dan implikasi praktis.",
            "Jangan membuat angka baru; gunakan istilah sebagian besar/studi terbatas hanya jika sesuai data project.",
            "Tulis dengan gaya artikel jurnal internasional, tetapi tetap dalam Bahasa Indonesia formal.",
        ],
        "output_baik": "Diskusi mengaitkan temuan, mekanisme kemungkinan, heterogenitas, bias, keterbatasan, dan implikasi tanpa klaim berlebihan.",
    },
    "Reviewer Simulation": {
        "tujuan": "Mensimulasikan komentar reviewer jurnal Q-level sebelum submit.",
        "input_utama": ["protocol", "search strategy", "PRISMA", "quality assessment", "manuscript draft", "target jurnal"],
        "cocok_jika": "Peneliti ingin mengetahui kelemahan naskah sebelum dikirim ke jurnal.",
        "instruksi_contoh": [
            "Berikan komentar seperti reviewer Q1/Q2: major concern, minor concern, dan rekomendasi revisi.",
            "Nilai apakah search strategy sudah replikatif dan apakah PRISMA sudah cukup transparan.",
            "Beri prioritas revisi dari yang paling berisiko menyebabkan desk rejection.",
        ],
        "output_baik": "Komentar tajam, spesifik, dapat ditindaklanjuti, dan tidak sekadar pujian umum.",
    },
    "Manuscript Improvement Plan": {
        "tujuan": "Menyusun rencana perbaikan naskah dari title sampai conclusion.",
        "input_utama": ["judul", "abstract", "methods", "results", "discussion", "checker PRISMA", "journal targeting"],
        "cocok_jika": "Peneliti sudah punya kerangka naskah tetapi belum yakin bagian mana yang harus diperbaiki.",
        "instruksi_contoh": [
            "Buat rencana revisi bertahap selama 7 hari kerja.",
            "Pisahkan perbaikan wajib, perbaikan penting, dan perbaikan opsional.",
            "Fokuskan pada kesiapan naskah untuk jurnal Scopus Q1/Q2 bidang agro/peternakan/biosistem.",
        ],
        "output_baik": "Rencana praktis, berurutan, dan langsung menunjukkan bagian naskah mana yang perlu diperbaiki.",
    },
    "Meta-analysis Advice": {
        "tujuan": "Menilai apakah data cukup untuk meta-analysis dan data apa yang masih kurang.",
        "input_utama": ["mean", "SD", "n", "outcome unit", "comparator", "effect direction", "study design"],
        "cocok_jika": "Peneliti ingin menentukan apakah review cukup narrative synthesis atau bisa dilanjutkan ke meta-analysis.",
        "instruksi_contoh": [
            "Cek kesiapan meta-analysis untuk outcome utama dan sebutkan data numerik yang belum lengkap.",
            "Sarankan subgroup analysis berdasarkan dosis, komoditas, durasi, lokasi, atau jenis teknologi/perlakuan.",
            "Jelaskan kapan sebaiknya tidak memaksakan meta-analysis karena heterogenitas terlalu tinggi.",
        ],
        "output_baik": "Ada diagnosis kesiapan data, outcome prioritas, data yang hilang, dan strategi sintesis yang realistis.",
    },
}

AI_MODEL_USAGE_GUIDANCE = {
    "Auto pilih model hemat biaya": [
        "Gunakan untuk cek cepat, ringkasan awal, novelty sederhana, dan saran revisi singkat.",
        "Cocok saat project masih awal dan data artikel belum banyak.",
        "Jika hasil kurang mendalam, lengkapi data extraction lalu ulangi dengan mode kualitas tinggi atau manual.",
    ],
    "Auto pilih model kualitas tinggi": [
        "Gunakan untuk draft Discussion, reviewer simulation, novelty-gap yang lebih tajam, dan manuscript improvement plan.",
        "Cocok saat screening, quality assessment, dan extraction sudah terisi cukup lengkap.",
        "Jika provider menolak karena deposit/premium, sistem akan mencoba fallback ringan atau gunakan mode manual.",
    ],
    "Pilih manual": [
        "Gunakan saat ingin memilih model tertentu dari SlashAI atau saat model otomatis terkena pembatasan deposit.",
        "Model flash/ringan cocok untuk cek cepat; model pro/opus/GPT premium cocok untuk analisis panjang jika akses tersedia.",
        "Pastikan nama model memakai format lengkap, misalnya slashai/gemini-3-flash.",
    ],
}


def render_ai_model_suggestions(strategy: str):
    tips = AI_MODEL_USAGE_GUIDANCE.get(strategy, [])
    if tips:
        st.markdown("**Saran penggunaan model:**")
        for tip in tips:
            st.caption(f"• {tip}")
    st.caption(
        "Agar hasil sesuai, lengkapi minimal judul, framework, population, intervention/exposure, comparator, outcome, "
        "kriteria inklusi-eksklusi, dan beberapa data artikel. AI tidak akan membuat sitasi atau angka baru jika data belum tersedia."
    )


def render_ai_task_suggestions(task: str):
    guide = AI_TASK_GUIDANCE.get(task, {})
    if not guide:
        return
    with st.expander("💡 Saran agar hasil AI sesuai", expanded=True):
        st.markdown(f"**Tujuan:** {guide.get('tujuan', '-')}")
        st.markdown(f"**Cocok digunakan jika:** {guide.get('cocok_jika', '-')}")
        inputs = guide.get("input_utama", [])
        if inputs:
            st.markdown("**Data yang sebaiknya sudah dilengkapi:** " + ", ".join(inputs))
        examples = guide.get("instruksi_contoh", [])
        if examples:
            st.markdown("**Contoh instruksi tambahan yang bisa diberikan:**")
            for idx, example in enumerate(examples, start=1):
                st.markdown(f"{idx}. {example}")
        st.markdown(f"**Ciri output yang baik:** {guide.get('output_baik', '-')}")
        st.info(
            "Gunakan instruksi tambahan yang spesifik. Contoh: sebutkan target jurnal, bidang, jenis komoditas, "
            "apakah ingin output ringkas/mendalam, dan bagian naskah mana yang ingin diperkuat."
        )

def make_ai_task_prompt(task: str) -> str:
    context = build_ai_project_context()
    task_instructions = {
        "Novelty & Gap Insight": "Buat analisis novelty dan research gap. Jelaskan gap utama, kekuatan topik, kelemahan data, dan cara menulis novelty pada Introduction dan Discussion.",
        "Discussion Draft": "Buat draft narasi Discussion awal berbasis data project. Jangan mengarang angka. Hubungkan arah efek, kualitas bukti, risiko bias, heterogenitas, dan implikasi praktis.",
        "Reviewer Simulation": "Bertindak sebagai reviewer jurnal Q-level. Berikan komentar major dan minor, risiko penolakan, serta tindakan revisi prioritas.",
        "Manuscript Improvement Plan": "Buat rencana perbaikan naskah langkah demi langkah dari title, abstract, methods, results, discussion, limitation, sampai conclusion.",
        "Meta-analysis Advice": "Nilai kesiapan meta-analysis. Jelaskan data apa yang kurang, outcome yang potensial, dan subgroup analysis yang disarankan.",
    }
    instruction = task_instructions.get(task, task_instructions["Novelty & Gap Insight"])
    output_depth = st.session_state.get("ai_output_depth", "Standar")
    target_focus = st.session_state.get("ai_target_focus", "Kesiapan jurnal Q-level")
    extra_instruction = str(st.session_state.get("ai_user_extra_instruction", "") or "").strip()
    extra_block = ""
    if extra_instruction:
        extra_block = f"\nInstruksi tambahan dari peneliti:\n{extra_instruction}\n"
    return f"""Tugas: {instruction}

Preferensi output:
- Kedalaman: {output_depth}
- Fokus utama: {target_focus}
{extra_block}
Data project systematic review:
```json
{context}
```

Format jawaban yang diminta:
1. Ringkasan diagnosis
2. Insight utama
3. Bagian naskah yang perlu diperbaiki
4. Rekomendasi tindakan praktis
5. Catatan kehati-hatian agar peneliti tidak menyimpulkan berlebihan

Aturan penting:
- Jangan membuat sitasi, jumlah artikel, atau angka baru yang tidak ada pada data project.
- Jika data belum cukup, sebutkan data apa yang harus dilengkapi peneliti.
- Gunakan Bahasa Indonesia formal, akademik, jelas, dan bisa langsung membantu penyusunan naskah systematic review.
"""


def render_online_ai_insight_panel(location: str = ""):
    """Render optional online AI insight tools using a temporary personal API key."""
    ai_cfg = st.session_state.get("ai_config", {})
    mode = ai_cfg.get("mode", "Offline Mode")
    api_key = get_personal_api_key()
    model, model_source = get_effective_ai_model(api_key)

    st.subheader("Online AI Insight Opsional")
    st.caption("Fitur ini opsional. Tanpa API key, seluruh sistem tetap berjalan menggunakan Offline Mode berbasis rule, checklist, dan template. Online Mode default memakai API kompatibel OpenAI dari SlashAI: POST https://api.slashai.my.id/v1/chat/completions dengan Authorization: Bearer <key>. Model dikirim pada body `model` dan header `model` untuk kompatibilitas SlashAI.")

    if mode != "Online AI Mode":
        st.info("Online AI Mode belum aktif. Aktifkan dari sidebar bila ingin memakai API key pribadi sementara.")
        return

    if not api_key:
        st.warning("Online AI Mode aktif, tetapi API key pribadi belum diisi di sidebar. Masukkan API key atau kembali ke Offline Mode.")
        return

    st.success("Online AI Mode aktif menggunakan API key pribadi dari sesi ini. API key tidak disimpan ke project state, ZIP export, XLSX, DOCX, atau Markdown.")
    st.caption(f"Model yang akan dipakai: `{model}` ({model_source}). Data project hanya dikirim saat Anda menekan tombol insight.")
    st.caption("Pastikan tidak ada data sensitif yang tidak ingin Anda kirim ke layanan API.")

    task = st.selectbox(
        "Pilih jenis insight online",
        ["Novelty & Gap Insight", "Discussion Draft", "Reviewer Simulation", "Manuscript Improvement Plan", "Meta-analysis Advice"],
        key=f"ai_task_select_{location}",
    )
    render_ai_task_suggestions(task)

    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(
            "Kedalaman output",
            ["Ringkas", "Standar", "Mendalam"],
            index=["Ringkas", "Standar", "Mendalam"].index(st.session_state.get("ai_output_depth", "Standar")) if st.session_state.get("ai_output_depth", "Standar") in ["Ringkas", "Standar", "Mendalam"] else 1,
            key="ai_output_depth",
            help="Ringkas untuk cek cepat, Standar untuk laporan umum, Mendalam untuk naskah jurnal yang lebih serius.",
        )
    with c2:
        st.selectbox(
            "Fokus output",
            [
                "Kesiapan jurnal Q-level",
                "Perbaikan metode PRISMA/ROSES",
                "Novelty dan research gap",
                "Discussion dan implication",
                "Meta-analysis readiness",
                "Reviewer comment simulation",
            ],
            index=0,
            key="ai_target_focus",
            help="Pilih fokus agar jawaban AI lebih sesuai dengan kebutuhan peneliti saat ini.",
        )

    st.text_area(
        "Instruksi tambahan untuk AI",
        key="ai_user_extra_instruction",
        height=100,
        placeholder=(
            "Contoh: Fokuskan pada bidang Teknik Pertanian dan Biosistem; buat output untuk target jurnal Q2; "
            "jangan terlalu panjang; beri rekomendasi perbaikan methods dan discussion; jangan buat sitasi baru."
        ),
        help="Opsional. Isi arahan spesifik agar output AI lebih sesuai dengan kebutuhan project.",
    )

    with st.expander("Lihat ringkasan data yang akan dikirim ke API", expanded=False):
        st.code(build_ai_project_context(max_records=10), language="json")

    if st.button("🤖 Buat AI Insight Online", key=f"make_ai_insight_{location}", use_container_width=True):
        prompt = make_ai_task_prompt(task)
        with st.spinner("Membuat AI insight online berdasarkan data project..."):
            ok, result = call_openai_responses_api(api_key, model, prompt, get_personal_api_base_url())
        if ok:
            st.session_state.ai_outputs[task] = result
            st.success("AI insight berhasil dibuat.")
        else:
            st.error(result)

    if st.session_state.get("ai_outputs"):
        st.markdown("### Hasil AI Insight Terakhir")
        for name, text in st.session_state.ai_outputs.items():
            with st.expander(name, expanded=(name == task)):
                st.markdown(text)
                st.download_button(
                    f"Download {name}.md",
                    text.encode("utf-8"),
                    f"online_ai_{re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_').lower()}.md",
                    "text/markdown",
                    use_container_width=True,
                    key=f"download_ai_{location}_{name}",
                )


def reset_project_state():
    """Reset all user-entered project data and return the app to its initial state."""
    keys_to_remove = [
        "project", "criteria", "terms", "articles", "quality", "extraction",
        "prisma_manual", "notes", "sync_config", "ai_config", "ai_outputs",
        "personal_openai_api_key", "openai_api_key_input", "personal_api_base_url", "api_base_url_input",
        "openai_available_models", "openai_models_last_checked", "openai_models_error", "openai_models_api_base", "manual_model_select",
        "manual_model_text", "ai_user_extra_instruction", "ai_output_depth", "ai_target_focus",
        "reset_confirm_checkbox", "reset_confirm_text",
        "reset_success_message",
    ]
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    # Clean possible widget-generated reset keys without touching Streamlit internals.
    for key in list(st.session_state.keys()):
        if str(key).startswith("reset_"):
            del st.session_state[key]
    init_state()
    st.session_state.reset_success_message = True

def render_sidebar():
    checks, pct = completion_status()
    st.sidebar.title("Workflow")
    cfg = st.session_state.sync_config
    cfg["auto_sync"] = st.sidebar.toggle("Auto-sync antarmenu", value=cfg.get("auto_sync", True), help="Jika aktif, isi Protocol, Search Strategy, Screening Score, PRISMA, Quality, Extraction, Insight, dan Export otomatis mengikuti menu sebelumnya.")
    cfg["overwrite_generated"] = st.sidebar.toggle("Timpa isi otomatis", value=cfg.get("overwrite_generated", True), help="Jika aktif, sistem akan memperbarui research question, kriteria, dan search terms dari Judul & PICOS/PECO. Matikan jika ingin menjaga edit manual.")
    cfg["auto_apply_domain_example"] = st.sidebar.toggle("Auto-isi contoh saat bidang berubah", value=cfg.get("auto_apply_domain_example", True), help="Jika aktif, saat Bidang/Kerangka diubah, judul, Population, Intervention/Exposure, Comparator, Outcome, Study Design, Research Question, dan Search Terms akan diisi dari contoh bidang terkait.")
    st.sidebar.caption(f"Sinkron terakhir: {cfg.get('last_sync', 'Belum pernah sinkron')}")
    st.sidebar.progress(pct / 100)
    st.sidebar.caption(f"Progress: {pct}%")
    for label, ok in checks.items():
        st.sidebar.write(("✅" if ok else "⬜") + " " + label)
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Sinkronkan semua modul", use_container_width=True):
        sync_downstream_from_project(reason="tombol sidebar")
        st.sidebar.success("Semua menu sudah mengikuti isi menu sebelumnya.")

    with st.sidebar.expander("🤖 Online AI Insight (opsional)", expanded=False):
        ai_cfg = st.session_state.ai_config
        mode_options = ["Offline Mode", "Online AI Mode"]
        current_mode = ai_cfg.get("mode", "Offline Mode")
        ai_cfg["mode"] = st.radio(
            "Mode analisis",
            mode_options,
            index=mode_options.index(current_mode) if current_mode in mode_options else 0,
            key="ai_mode_radio",
            help="Offline Mode tidak membutuhkan API. Online AI Mode memakai API key pribadi user hanya selama sesi berjalan.",
        )

        model_selection_options = ["Auto pilih model hemat biaya", "Auto pilih model kualitas tinggi", "Pilih manual"]
        current_selection = ai_cfg.get("model_selection", "Auto pilih model hemat biaya")
        ai_cfg["model_selection"] = st.radio(
            "Pemilihan model",
            model_selection_options,
            index=model_selection_options.index(current_selection) if current_selection in model_selection_options else 0,
            key="ai_model_selection_radio",
            help="Mode otomatis memilih dari daftar model yang tersedia pada API base/API key. Jika daftar belum dicek, aplikasi memakai daftar bawaan SlashAI dan fallback default.",
        )
        render_ai_model_suggestions(ai_cfg["model_selection"])

        with st.expander("📌 Saran memilih model AI", expanded=False):
            st.markdown(
                """
**Gunakan model hemat biaya** untuk:
- cek cepat kualitas judul/protocol;
- ringkasan novelty awal;
- daftar revisi singkat;
- validasi apakah data project sudah cukup.

**Gunakan model kualitas tinggi** untuk:
- draft Discussion yang lebih matang;
- reviewer simulation;
- manuscript improvement plan;
- analisis gap dan implikasi yang lebih mendalam.

**Gunakan pilih manual** jika:
- model otomatis ditolak provider;
- muncul pesan deposit/premium;
- ingin mencoba model flash/ringan tertentu;
- ingin memakai model yang diberikan provider tetapi belum terbaca di daftar.

Agar hasil sesuai, lengkapi data project terlebih dahulu. AI akan jauh lebih berguna jika artikel include, quality assessment, dan data extraction sudah terisi.
"""
            )

        if st.button("Hapus API key dari sesi ini", use_container_width=True):
            clear_personal_api_key()
            st.success("API key pribadi dan cache daftar model sudah dihapus dari sesi aplikasi.")
            st.rerun()

        st.text_input(
            "API Key pribadi / Bearer token",
            type="password",
            key="personal_openai_api_key",
            help="Opsional. Boleh isi raw key saja, atau paste `Bearer ...` / `Authorization: Bearer ...`; sistem akan membersihkan formatnya. API key tidak disimpan ke project state, ZIP, XLSX, DOCX, atau Markdown.",
        )
        st.text_input(
            "API Base URL",
            value=st.session_state.get("personal_api_base_url", SLASHAI_DEFAULT_API_BASE),
            key="personal_api_base_url",
            help="Default memakai endpoint SlashAI: https://api.slashai.my.id/v1/chat/completions. Boleh isi base URL (https://api.slashai.my.id), /v1, atau endpoint penuh /v1/chat/completions; sistem akan menormalkan otomatis.",
        )
        api_key = get_personal_api_key()
        st.caption(f"Endpoint chat yang digunakan: `{chat_completions_url(get_personal_api_base_url())}`")
        st.caption(f"Daftar model bawaan SlashAI tersedia: {len(SLASHAI_ALL_MODELS)} model. Contoh ringan: `slashai/gemini-3-flash`, `slashai/deepseek-v4-flash`; contoh kualitas tinggi: `slashai/gpt-5.5`, `slashai/claude-sonnet-4.7`.")

        if api_key:
            if st.button("🔎 Cek model tersedia dari API key", use_container_width=True):
                ok, result = list_openai_models_with_key(api_key, get_personal_api_base_url())
                if ok:
                    if st.session_state.get("openai_models_error"):
                        st.warning(st.session_state.openai_models_error)
                        st.info(f"Daftar bawaan/fallback aktif: {len(result)} model dapat dipilih.")
                    else:
                        st.success(f"Berhasil membaca {len(result)} model text-generation dari API key.")
                else:
                    st.warning(result)
                    st.info("Sistem tetap bisa dipakai dengan daftar model bawaan SlashAI atau pilihan manual.")

        available_models = st.session_state.get("openai_available_models", [])
        if available_models:
            last_checked = st.session_state.get("openai_models_last_checked", "")
            st.caption(f"Daftar model terakhir dicek: {last_checked}. Total model text: {len(available_models)}")
        elif st.session_state.get("openai_models_error"):
            st.caption(st.session_state.openai_models_error)
            st.caption("Sistem tetap menyediakan daftar model bawaan SlashAI untuk mode otomatis/manual.")
        else:
            st.caption("Belum ada daftar model dari API key. Mode otomatis/manual memakai daftar bawaan SlashAI sampai tombol cek model dijalankan.")

        if ai_cfg.get("model_selection") == "Pilih manual":
            manual_options = available_models if available_models else sort_model_ids(SLASHAI_ALL_MODELS)
            source_label = "daftar model dari API key" if available_models else "daftar bawaan SlashAI"
            current_manual = ai_cfg.get("manual_model", ai_cfg.get("model", ECONOMY_MODEL_FALLBACK))
            if current_manual and current_manual not in manual_options:
                manual_options = [current_manual] + manual_options
            default_index = manual_options.index(current_manual) if current_manual in manual_options else 0
            selected_manual = st.selectbox(
                "Pilih model manual",
                manual_options,
                index=default_index,
                key="manual_model_select",
                help=f"Pilihan berasal dari {source_label}. Model dikirim sebagai body `model` dan header `model`.",
            )
            custom_manual = st.text_input(
                "Atau tulis model manual",
                value="",
                key="manual_model_text",
                placeholder="contoh: slashai/gemini-3-flash, slashai/deepseek-v4-flash, atau slashai/gpt-5.5",
                help="Isi hanya jika ingin memakai model yang tidak ada di daftar. Jika kosong, sistem memakai pilihan dropdown.",
            ).strip()
            ai_cfg["manual_model"] = custom_manual or selected_manual or ECONOMY_MODEL_FALLBACK
            st.caption(f"Model manual aktif: `{ai_cfg['manual_model']}` ({source_label}).")
        else:
            effective_model, source = get_effective_ai_model(api_key)
            ai_cfg["model"] = effective_model
            ai_cfg["selected_model_source"] = source
            st.caption(f"Model terpilih otomatis: `{effective_model}` ({source}).")
            if "gpt-5.5" in str(effective_model).lower():
                st.caption("Jika muncul pesan `Deposit required`, coba `Pilih manual` lalu gunakan `slashai/gemini-3-flash` atau `slashai/deepseek-v4-flash`.")

        if ai_cfg.get("mode") == "Online AI Mode" and api_key:
            current_model_for_test, _ = get_effective_ai_model(api_key)
            if st.button("🧪 Tes Chat Completions", use_container_width=True):
                with st.spinner("Menguji koneksi endpoint, model, dan API key..."):
                    ok, msg = test_chat_completion_connection(api_key, current_model_for_test, get_personal_api_base_url())
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                    st.info("Coba pastikan API Base tetap `https://api.slashai.my.id`, model memakai awalan `slashai/`, dan field API key tidak berisi spasi/teks tambahan. Jika detail server menyebut `Deposit required`, lakukan deposit/top up di provider atau pilih model lain yang lebih ringan lewat mode manual.")

        if ai_cfg.get("mode") == "Online AI Mode" and api_key:
            st.success("Online AI aktif untuk sesi ini.")
        elif ai_cfg.get("mode") == "Online AI Mode":
            st.warning("Online AI aktif, tetapi API key belum diisi.")
        else:
            st.info("Offline Mode aktif. Sistem tetap berjalan tanpa API.")
        st.caption("Catatan: data project hanya dikirim ke API saat Anda menekan tombol Buat AI Insight Online.")

    with st.sidebar.expander("💾 Simpan & lanjutkan project", expanded=False):
        st.caption("Unduh file project setelah menyelesaikan langkah apa pun. File ini dapat diunggah kembali untuk melanjutkan pekerjaan tanpa mulai dari awal.")
        st.download_button(
            "⬇️ Download Project State (.srproj.json)",
            resume_project_state_bytes("Sidebar snapshot"),
            "systematic_review_project_state.srproj.json",
            "application/json",
            use_container_width=True,
        )
        resume_upload = st.file_uploader(
            "Upload project untuk dilanjutkan",
            type=["json", "srproj"],
            key="resume_project_upload",
            help="Gunakan file .srproj.json yang sebelumnya diunduh dari aplikasi ini.",
        )
        if resume_upload is not None:
            st.caption(f"File terpilih: {resume_upload.name}")
            replace_confirm = st.checkbox("Saya paham project aktif akan diganti dengan isi file ini.", key="resume_replace_confirm")
            if st.button("📂 Muat dan lanjutkan project", use_container_width=True, disabled=not replace_confirm):
                ok, msg = load_resume_project_state(resume_upload)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with st.sidebar.expander("⚠️ Hapus / reset data project"):
        st.warning("Reset akan menghapus judul, protocol, search terms, artikel, PRISMA, quality assessment, data extraction, catatan, dan konfigurasi sementara. Gunakan export terlebih dahulu jika data masih diperlukan.")
        confirm_checkbox = st.checkbox("Saya paham bahwa semua data project sementara akan dihapus.", key="reset_confirm_checkbox")
        confirm_text = st.text_input("Ketik RESET untuk konfirmasi", key="reset_confirm_text", placeholder="RESET")
        reset_ready = confirm_checkbox and confirm_text.strip().upper() == "RESET"
        if st.button("🗑️ Hapus data dan kembali ke awal", use_container_width=True, disabled=not reset_ready):
            reset_project_state()
            st.rerun()
        if not reset_ready:
            st.caption("Tombol hapus aktif setelah checkbox dicentang dan kata RESET diketik dengan benar.")

    st.sidebar.caption(APP_VERSION)


def page_workflow():
    st.title(f"🌾 {APP_TITLE}")
    st.caption(APP_VERSION)
    st.info("Gunakan halaman ini sebagai peta kerja. Setiap langkah menghasilkan output yang dipakai oleh langkah berikutnya. Mode auto-sync membuat menu berikutnya langsung menyesuaikan isi menu sebelumnya.")
    render_sync_status()
    st.download_button(
        "💾 Download snapshot langkah saat ini",
        make_step_snapshot("Panduan Workflow"),
        "step_00_workflow_snapshot.srproj.json",
        "application/json",
        use_container_width=True,
    )

    steps = [
        ("1", "Judul & PICOS/PECO", "Masukkan judul, bidang termasuk Teknik Pertanian dan Biosistem, target jurnal, dan komponen PICOS/PECO.", "Output: skor kesiapan judul, kelemahan, rekomendasi judul, research question."),
        ("2", "Protocol & Search Strategy", "Rapikan protocol, kriteria inklusi-eksklusi, dan Boolean search.", "Output: protocol awal dan search string yang bisa dipakai di Scopus/WoS/database lain."),
        ("3", "Import Artikel", "Unggah hasil ekspor XLSX/XLS/RIS dari database.", "Output: data artikel yang sudah dinormalisasi dan dideduplikasi."),
        ("4", "Screening", "Gunakan skor relevansi PICOS sebagai bantuan, lalu tetapkan keputusan Include/Maybe/Exclude.", "Output: daftar artikel eligible untuk full-text."),
        ("5", "PRISMA", "Pantau jumlah record dari identifikasi sampai studi include final.", "Output: angka PRISMA untuk naskah."),
        ("6", "Quality Assessment", "Nilai kualitas studi berdasarkan checklist.", "Output: kategori Low/Moderate/High."),
        ("7", "Data Extraction", "Isi outcome, effect direction, effect size, mean, SD, n, temuan kunci, limitasi, dan implikasi.", "Output: matriks bukti untuk sintesis dan kesiapan meta-analysis."),
        ("8", "Q-Level Tools", "Cek PRISMA, PRISMA-S, risk of bias, GRADE, meta-analysis readiness, novelty-gap, journal targeting, manuscript draft, dan reviewer check.", "Output: checklist kesiapan jurnal Q-level, draft manuscript DOCX, cover letter, dan file audit XLSX."),
        ("9", "Insight & Export", "Sistem membaca seluruh hasil dan menyusun insight otomatis.", "Output: Evidence Insight Report, protocol, methods template, DOCX/XLSX, dan export ZIP."),
    ]
    for no, title, desc, out in steps:
        with st.container(border=True):
            st.subheader(f"Langkah {no}. {title}")
            st.write(desc)
            st.caption(out)

    st.subheader("Cara kerja integrasi otomatis")
    st.markdown("""
- Perubahan pada **Langkah 1** membentuk ulang research question, inclusion-exclusion criteria, dan Boolean search.
- Perubahan pada **Langkah 2** langsung memperbarui skor relevansi artikel pada Screening.
- Keputusan **Screening** langsung mengubah angka PRISMA dan daftar artikel pada Quality Assessment serta Data Extraction.
- Hasil **Quality Assessment** dan **Data Extraction** langsung dibaca oleh Q-Level Tools, Evidence Insight Report, dan Export ZIP.
- Q-Level Tools membantu mengecek kesiapan PRISMA, PRISMA-S, risk of bias/GRADE, meta-analysis, novelty, jurnal target, dan draft manuscript.
""")

    st.subheader("Ringkasan cepat proyek")
    p = st.session_state.project
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Skor judul", f"{analyze_title(p)['score']}/100")
    c2.metric("Artikel", len(st.session_state.articles))
    c3.metric("Include final", get_prisma_counts(True)["studies_included"])
    c4.metric("Kekuatan bukti", infer_evidence_strength()["strength"])


def page_title_protocol():
    st.header("1. Judul, PICOS/PECO, dan Kelayakan Naskah")
    render_sync_status()
    st.download_button(
        "💾 Simpan progress Langkah 1",
        make_step_snapshot("Langkah 1 - Judul & PICOS/PECO"),
        "step_01_title_picos_snapshot.srproj.json",
        "application/json",
        use_container_width=True,
    )

    p = st.session_state.project
    cfg = st.session_state.sync_config

    st.subheader("A. Pilih bidang dan kerangka review")
    st.caption("Jika bidang atau kerangka diubah, sistem dapat langsung mengisi contoh yang relevan agar peneliti lebih mudah menyesuaikan topik.")
    d1, d2, d3, d4 = st.columns(4)
    domains = ["Peternakan", "Agro/Agronomi", "Teknik Pertanian dan Biosistem", "Perikanan/Akuakultur", "Pangan", "Lingkungan", "Otomatis"]
    frameworks = ["PICOS", "PECO", "PICO"]
    targets = ["Q1/Q2", "Q2/Q3", "Scopus awal", "Sinta/Kampus"]
    scopes = ["Global", "Asia", "Indonesia", "Lokal/Daerah"]

    selected_domain = d1.selectbox(
        "Bidang",
        domains,
        index=domains.index(p.get("domain", "Peternakan")) if p.get("domain", "Peternakan") in domains else 0,
        help="Saat bidang berubah, contoh judul dan komponen review akan mengikuti bidang ini.",
    )
    selected_framework = d2.selectbox(
        "Kerangka",
        frameworks,
        index=frameworks.index(p.get("framework", "PICOS")) if p.get("framework", "PICOS") in frameworks else 0,
        help="PICOS/PICO untuk intervensi, PECO untuk paparan/exposure.",
    )
    p["target_level"] = d3.selectbox(
        "Target",
        targets,
        index=targets.index(p.get("target_level", "Q1/Q2")) if p.get("target_level", "Q1/Q2") in targets else 0,
    )
    p["geographical_scope"] = d4.selectbox(
        "Cakupan",
        scopes,
        index=scopes.index(p.get("geographical_scope", "Global")) if p.get("geographical_scope", "Global") in scopes else 0,
    )

    auto_apply = st.toggle(
        "Otomatis isi contoh sesuai bidang/kerangka",
        value=cfg.get("auto_apply_domain_example", True),
        help="Jika aktif, perubahan Bidang/Kerangka akan mengisi ulang judul, population, intervention/exposure, comparator, outcome, study design, research question, dan search terms berdasarkan contoh bidang tersebut.",
    )
    cfg["auto_apply_domain_example"] = auto_apply

    domain_changed = selected_domain != p.get("domain", "Peternakan")
    framework_changed = selected_framework != p.get("framework", "PICOS")
    if domain_changed or framework_changed:
        if auto_apply and selected_domain != "Otomatis":
            applied = apply_domain_framework_autofill(selected_domain, selected_framework, source="auto-isi contoh karena bidang/kerangka berubah")
            st.success(f"Bidang/kerangka berubah. Contoh untuk {selected_domain} - {selected_framework} sudah diterapkan: {applied.get('title','')}")
            st.rerun()
        else:
            p["domain"] = selected_domain
            p["framework"] = selected_framework
            sync_downstream_from_project(reason="bidang/kerangka berubah tanpa auto-isi")
            st.info("Bidang/kerangka sudah berubah. Klik tombol terapkan contoh di bawah jika ingin mengisi komponen review dari contoh bidang tersebut.")
            st.rerun()

    render_current_domain_example_preview(p.get("domain", "Peternakan"), p.get("framework", "PICOS"))
    c_apply, c_note = st.columns([1, 2])
    if c_apply.button("Terapkan contoh bidang ini sekarang", use_container_width=True):
        applied = apply_domain_framework_autofill(p.get("domain", "Peternakan"), p.get("framework", "PICOS"), source="tombol terapkan contoh bidang")
        st.success(f"Contoh diterapkan: {applied.get('title','')}")
        st.rerun()
    c_note.caption("Gunakan tombol ini bila ingin mengembalikan komponen review ke contoh bawaan bidang setelah mengedit manual.")

    st.subheader("B. Sesuaikan judul dan komponen review")
    c1, c2 = st.columns(2)
    p["title"] = st.text_area("Judul sementara", value=p.get("title", ""), height=90)
    p["population"] = c1.text_input("Population / Problem", value=p.get("population", ""))
    p["intervention"] = c2.text_input("Intervention / Exposure", value=p.get("intervention", ""))
    p["comparator"] = c1.text_input("Comparator", value=p.get("comparator", ""))
    p["outcome"] = c2.text_input("Outcome", value=p.get("outcome", ""))
    p["study_design"] = c1.text_input("Study design", value=p.get("study_design", ""))
    p["year_range"] = c2.text_input("Rentang tahun", value=p.get("year_range", "2015-2026"))
    p["language"] = c1.text_input("Bahasa artikel", value=p.get("language", "English and Bahasa Indonesia"))
    review_types = ["Systematic Review", "Systematic Review and Meta-Analysis", "Systematic Map", "Scoping Review"]
    p["review_type"] = c2.selectbox(
        "Jenis review",
        review_types,
        index=review_types.index(p.get("review_type", "Systematic Review and Meta-Analysis")) if p.get("review_type", "Systematic Review and Meta-Analysis") in review_types else 1,
    )

    b1, b2 = st.columns(2)
    if b1.button("Simpan perubahan manual dan sinkronkan", use_container_width=True):
        st.session_state.project = p
        sync_downstream_from_project(reason="perubahan manual Langkah 1")
        st.success("Perubahan manual disimpan. Protocol, Search Strategy, Screening Score, PRISMA, Quality, Data Extraction, Insight, dan Export sudah menyesuaikan.")
    if b2.button("Buat ulang RQ, kriteria, dan search terms dari isian saat ini", use_container_width=True):
        st.session_state.project = p
        st.session_state.project["research_question"] = make_auto_research_question(st.session_state.project)
        st.session_state.criteria = make_auto_criteria(st.session_state.project)
        st.session_state.terms = suggest_terms_from_project(st.session_state.project)
        sync_downstream_from_project(reason="generate ulang dari isian manual")
        st.success("Research question, kriteria, dan search terms dibuat ulang berdasarkan isian saat ini.")
        st.rerun()

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
        sync_downstream_from_project(reason="RQ pertama diterapkan")
        st.success("Research question diterapkan dan menu berikutnya disinkronkan.")

    render_framework_domain_guidance(st.session_state.project)

def page_protocol_search():
    st.header("2. Protocol dan Search Strategy")
    sync_if_auto(reason="membuka protocol & search")
    render_sync_status()
    st.download_button("💾 Simpan progress Langkah 2", make_step_snapshot("Langkah 2 - Protocol & Search"), "step_02_protocol_search_snapshot.srproj.json", "application/json", use_container_width=True)
    p = st.session_state.project
    c = st.session_state.criteria
    if st.button("Ambil ulang otomatis dari Judul & PICOS/PECO", use_container_width=True):
        sync_downstream_from_project(reason="regenerate protocol/search")
        st.success("Protocol, kriteria, dan search terms sudah dibuat ulang dari menu sebelumnya.")
        st.rerun()
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
        sync_quality_extraction()
        st.session_state.sync_config["last_sync"] = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (protocol/search disimpan)"
        st.success("Protocol dan Search Strategy tersimpan. Screening score, PRISMA, Quality Assessment, Data Extraction, Insight, dan Export ikut diperbarui.")

    result = analyze_title(st.session_state.project)
    profile = DOMAIN_PROFILES.get(result["domain"], DOMAIN_PROFILES["Peternakan"])
    c1, c2 = st.columns(2)
    c1.subheader("Database disarankan")
    c1.markdown("\n".join([f"- {db}" for db in profile["databases"]]))
    c2.subheader("Quality tool disarankan")
    c2.write(profile["quality_tool"])
    st.subheader("Boolean Search String")
    st.code(build_search_string(st.session_state.terms), language="text")
    with st.expander("Lihat contoh dan informasi sesuai pilihan saat ini"):
        render_framework_domain_guidance(st.session_state.project)
    st.download_button("Download protocol.md", make_protocol_markdown().encode("utf-8"), "protocol_systematic_review.md", "text/markdown", use_container_width=True)
    with st.expander("Preview protocol"):
        st.markdown(make_protocol_markdown())


def page_import_screening():
    st.header("3-4. Import Artikel dan Screening Terintegrasi")
    sync_if_auto(reason="membuka import & screening")
    render_sync_status()
    st.download_button("💾 Simpan progress Langkah 3-4", make_step_snapshot("Langkah 3-4 - Import & Screening"), "step_03_04_import_screening_snapshot.srproj.json", "application/json", use_container_width=True)
    st.write("Unggah hasil ekspor dari database dalam format XLSX, XLS, atau RIS. Sistem akan menormalisasi kolom, mendeteksi duplikasi, dan memberi skor relevansi berdasarkan PICOS/PECO yang aktif dari menu sebelumnya.")
    st.info(f"Screening score saat ini memakai kerangka {st.session_state.project.get('framework', 'PICOS')} untuk: {st.session_state.project.get('population','')} | {st.session_state.project.get('intervention','')} | {st.session_state.project.get('outcome','')}")
    sample_path = "data/sample_articles.xlsx"
    with open(sample_path, "rb") as f:
        st.download_button("Download template/sample XLSX", f.read(), "sample_articles.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    upload = st.file_uploader("Upload file artikel", type=["xlsx", "xls", "ris"])
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
        df = pd.read_excel(sample_path)
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
            "reviewer1_decision": st.column_config.SelectboxColumn("Reviewer 1", options=["Belum dinilai", "Include", "Maybe", "Exclude"]),
            "reviewer2_decision": st.column_config.SelectboxColumn("Reviewer 2", options=["Belum dinilai", "Include", "Maybe", "Exclude"]),
            "screening_conflict": st.column_config.CheckboxColumn("Conflict"),
            "consensus_decision": st.column_config.SelectboxColumn("Consensus", options=["Belum dinilai", "Include", "Maybe", "Exclude", "Perlu diskusi"]),
            "screening_decision": st.column_config.SelectboxColumn("Screening decision", options=["Belum dinilai", "Include", "Maybe", "Exclude"]),
            "full_text_decision": st.column_config.SelectboxColumn("Full-text decision", options=["Belum dinilai", "Include", "Exclude"]),
            "exclusion_reason": st.column_config.SelectboxColumn("Exclusion reason", options=["", "Tidak relevan", "Bukan studi empiris", "Populasi tidak sesuai", "Intervensi tidak sesuai", "Outcome tidak sesuai", "Duplikat", "Data tidak lengkap"]),
            "full_text_exclusion_reason": st.column_config.SelectboxColumn("Full-text exclusion reason", options=["", "Full text tidak tersedia", "Data outcome tidak lengkap", "Metode tidak sesuai", "Populasi/intervensi/outcome tidak sesuai", "Duplikat", "Artikel bukan peer-reviewed"]),
        },
        key="screening_editor"
    )
    if st.button("Simpan hasil screening dan sinkronkan", use_container_width=True):
        st.session_state.articles = flag_duplicates(update_dual_reviewer_consensus(edited))
        st.session_state.articles = apply_relevance_scoring(st.session_state.articles)
        sync_quality_extraction()
        st.success("Screening disimpan. PRISMA, Quality Assessment, dan Data Extraction sudah disinkronkan.")
    download_df_button("Download screening_results.xlsx", st.session_state.articles, "screening_results.xlsx")


def page_prisma_quality():
    st.header("5-6. PRISMA dan Quality Assessment")
    sync_if_auto(reason="membuka PRISMA & quality")
    render_sync_status()
    st.download_button("💾 Simpan progress Langkah 5-6", make_step_snapshot("Langkah 5-6 - PRISMA & Quality"), "step_05_06_prisma_quality_snapshot.srproj.json", "application/json", use_container_width=True)
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
    download_df_button("Download prisma_counts.xlsx", prisma_df, "prisma_counts.xlsx")

    st.subheader("Quality Assessment")
    sync_quality_extraction()
    q = calculate_quality(st.session_state.quality)
    if q.empty:
        st.info("Belum ada artikel include untuk dinilai kualitasnya.")
        return
    edited = st.data_editor(
        q,
        use_container_width=True,
        disabled=["quality_score", "quality_category", "overall_risk_of_bias", "certainty_of_evidence"],
        column_config={
            "clear_objective": st.column_config.CheckboxColumn("Clear objective"),
            "appropriate_design": st.column_config.CheckboxColumn("Appropriate design"),
            "adequate_sample": st.column_config.CheckboxColumn("Adequate sample"),
            "clear_intervention": st.column_config.CheckboxColumn("Clear intervention"),
            "valid_outcome": st.column_config.CheckboxColumn("Valid outcome"),
            "adequate_statistics": st.column_config.CheckboxColumn("Adequate statistics"),
            "bias_control": st.column_config.CheckboxColumn("Bias control"),
            "complete_reporting": st.column_config.CheckboxColumn("Complete reporting"),
            "selection_bias": st.column_config.SelectboxColumn("Selection bias", options=["Low", "High", "Unclear"]),
            "performance_bias": st.column_config.SelectboxColumn("Performance bias", options=["Low", "High", "Unclear"]),
            "detection_bias": st.column_config.SelectboxColumn("Detection bias", options=["Low", "High", "Unclear"]),
            "attrition_bias": st.column_config.SelectboxColumn("Attrition bias", options=["Low", "High", "Unclear"]),
            "reporting_bias": st.column_config.SelectboxColumn("Reporting bias", options=["Low", "High", "Unclear"]),
            "other_bias": st.column_config.SelectboxColumn("Other bias", options=["Low", "High", "Unclear"]),
            "overall_risk_of_bias": st.column_config.SelectboxColumn("Overall RoB", options=["Low", "High", "Unclear"]),
            "certainty_of_evidence": st.column_config.SelectboxColumn("Certainty", options=["Not assessed", "High", "Moderate", "Low", "Very Low"]),
        },
        key="quality_editor"
    )
    if st.button("Simpan quality assessment", use_container_width=True):
        st.session_state.quality = calculate_quality(edited)
        st.success("Quality assessment disimpan.")
    if not st.session_state.quality.empty:
        st.bar_chart(st.session_state.quality["quality_category"].value_counts())
    download_df_button("Download quality_assessment.xlsx", st.session_state.quality, "quality_assessment.xlsx")


def page_extraction():
    st.header("7. Data Extraction")
    sync_if_auto(reason="membuka data extraction")
    render_sync_status()
    st.download_button("💾 Simpan progress Langkah 7", make_step_snapshot("Langkah 7 - Data Extraction"), "step_07_data_extraction_snapshot.srproj.json", "application/json", use_container_width=True)
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
            "sample_size": st.column_config.NumberColumn("Sample size"),
            "n_intervention": st.column_config.NumberColumn("N intervention"),
            "n_control": st.column_config.NumberColumn("N control"),
            "mean_intervention": st.column_config.NumberColumn("Mean intervention"),
            "sd_intervention": st.column_config.NumberColumn("SD intervention"),
            "mean_control": st.column_config.NumberColumn("Mean control"),
            "sd_control": st.column_config.NumberColumn("SD control"),
            "effect_size": st.column_config.NumberColumn("Effect size"),
            "p_value": st.column_config.NumberColumn("p-value"),
            "effect_direction": st.column_config.SelectboxColumn("Effect direction", options=["", "Positive", "Negative", "No effect", "Mixed"]),
            "key_finding": st.column_config.TextColumn("Key finding", width="large"),
            "limitations": st.column_config.TextColumn("Limitations", width="large"),
            "implication": st.column_config.TextColumn("Implication", width="large"),
            "novelty_note": st.column_config.TextColumn("Novelty note", width="large"),
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
    download_df_button("Download data_extraction.xlsx", st.session_state.extraction, "data_extraction.xlsx")




def page_qlevel_tools():
    st.header("8. Q-Level Manuscript Tools")
    sync_if_auto(reason="membuka Q-level tools")
    render_sync_status()
    st.download_button("💾 Simpan progress Langkah 8", make_step_snapshot("Langkah 8 - Q-Level Tools"), "step_08_qlevel_tools_snapshot.srproj.json", "application/json", use_container_width=True)
    st.write("Halaman ini mengecek kesiapan naskah sebelum dikembangkan untuk jurnal bereputasi. Semua indikator membaca data dari menu sebelumnya.")

    tabs = st.tabs([
        "PRISMA 2020",
        "PRISMA-S Search Audit",
        "Risk of Bias & GRADE",
        "Meta-Analysis Readiness",
        "Novelty & Gap",
        "Journal Targeting",
        "Manuscript Builder",
        "Reviewer Check",
        "Online AI Insight",
    ])

    with tabs[0]:
        st.subheader("PRISMA 2020 Compliance Checker")
        df = prisma_compliance_df()
        complete = (df["status"] == "Lengkap").mean() if not df.empty else 0
        st.metric("Kelengkapan PRISMA", f"{complete*100:.0f}%")
        st.dataframe(df, use_container_width=True)
        download_df_button("Download prisma_2020_compliance.xlsx", df, "prisma_2020_compliance.xlsx")

    with tabs[1]:
        st.subheader("PRISMA-S Search Strategy Audit")
        df = prisma_s_audit_df()
        complete = (df["status"] == "Lengkap").mean() if not df.empty else 0
        st.metric("Kelengkapan PRISMA-S", f"{complete*100:.0f}%")
        st.dataframe(df, use_container_width=True)
        st.info("Catatan: untuk submit jurnal, search string idealnya dicatat per database karena sintaks Scopus, Web of Science, PubMed, dan CAB Abstracts bisa berbeda.")
        p = st.session_state.project
        p["search_date"] = st.date_input("Tanggal pencarian terakhir", value=pd.to_datetime(p.get("search_date", str(date.today()))).date() if p.get("search_date") else date.today()).isoformat()
        download_df_button("Download prisma_s_search_audit.xlsx", df, "prisma_s_search_audit.xlsx")

    with tabs[2]:
        st.subheader("Risk of Bias dan Certainty of Evidence")
        if st.session_state.quality.empty:
            st.warning("Belum ada artikel include. Lakukan screening/full-text include terlebih dahulu.")
        else:
            q = calculate_quality(st.session_state.quality)
            st.session_state.quality = q
            c1, c2, c3 = st.columns(3)
            c1.metric("Rata-rata quality score", f"{pd.to_numeric(q['quality_score'], errors='coerce').fillna(0).mean():.2f}/8")
            c2.metric("High quality", int((q["quality_category"] == "High").sum()))
            c3.metric("Low risk of bias", int((q["overall_risk_of_bias"] == "Low").sum()))
            st.dataframe(q[["id", "title", "quality_score", "quality_category", "overall_risk_of_bias", "certainty_of_evidence", "grade_downgrade_reason"]], use_container_width=True)
            download_df_button("Download risk_of_bias_grade.xlsx", q, "risk_of_bias_grade.xlsx")

    with tabs[3]:
        st.subheader("Meta-Analysis Readiness Checker")
        readiness = meta_analysis_readiness()
        c1, c2 = st.columns(2)
        c1.metric("Meta-analysis readiness score", f"{readiness['score']}/100")
        c2.metric("Status", readiness["status"])
        for reason in readiness["reasons"]:
            st.write("- " + reason)
        if not readiness["table"].empty:
            st.dataframe(readiness["table"], use_container_width=True)
            download_df_button("Download meta_analysis_readiness.xlsx", readiness["table"], "meta_analysis_readiness.xlsx")
        st.info("Agar siap meta-analysis, isi kolom mean, SD, n, unit outcome, effect size, dan comparator pada Data Extraction.")

    with tabs[4]:
        st.subheader("Novelty & Gap Analyzer")
        df = novelty_gap_df()
        st.dataframe(df, use_container_width=True)
        download_df_button("Download novelty_gap_analysis.xlsx", df, "novelty_gap_analysis.xlsx")

    with tabs[5]:
        st.subheader("Journal Targeting Assistant")
        df = journal_targeting_df()
        st.dataframe(df, use_container_width=True)
        st.warning("Sistem membantu mengecek kecocokan dan kesiapan, tetapi tidak menjamin artikel diterima di jurnal Q1/Q2. Validasi manual scope, APC, indexing, dan author guidelines tetap wajib.")
        download_df_button("Download journal_targeting.xlsx", df, "journal_targeting.xlsx")

    with tabs[6]:
        st.subheader("Q-Level Manuscript Builder")
        manuscript = build_manuscript_markdown()
        st.markdown(manuscript)
        col1, col2, col3 = st.columns(3)
        col1.download_button("Download manuscript_draft.md", manuscript.encode("utf-8"), "q_level_manuscript_draft.md", "text/markdown", use_container_width=True)
        col2.download_button("Download manuscript_draft.docx", docx_from_markdown_bytes(manuscript, "Systematic Review Draft"), "q_level_manuscript_draft.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        cover = make_cover_letter_markdown()
        col3.download_button("Download cover_letter.docx", docx_from_markdown_bytes(cover, "Cover Letter"), "cover_letter_template.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

    with tabs[7]:
        st.subheader("Pre-Submission Reviewer Check")
        df = reviewer_check_df()
        st.dataframe(df, use_container_width=True)
        major = int((df["severity"] == "Major").sum()) if not df.empty else 0
        if major:
            st.error(f"Masih ada {major} catatan major yang sebaiknya diperbaiki sebelum submit.")
        else:
            st.success("Tidak ada catatan major otomatis. Tetap lakukan validasi manual oleh peneliti/pembimbing.")
        download_df_button("Download reviewer_check.xlsx", df, "reviewer_check.xlsx")

    with tabs[8]:
        render_online_ai_insight_panel("qlevel")

def page_insight_export():
    st.header("9. Evidence Insight Report dan Export")
    sync_if_auto(reason="membuka insight & export")
    render_sync_status()
    st.download_button("💾 Simpan progress Langkah 9", make_step_snapshot("Langkah 9 - Insight & Export"), "step_09_insight_export_snapshot.srproj.json", "application/json", use_container_width=True)
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

    render_online_ai_insight_panel("insight_export")

    st.subheader("Export")
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download protocol.md", make_protocol_markdown().encode("utf-8"), "protocol_systematic_review.md", "text/markdown", use_container_width=True)
    c2.download_button("Download methods_template.md", make_methods_template().encode("utf-8"), "methods_template.md", "text/markdown", use_container_width=True)
    c3.download_button("Download insight_report.md", report.encode("utf-8"), "evidence_insight_report.md", "text/markdown", use_container_width=True)
    st.download_button("Download examples_and_guidance.md", make_guidance_markdown().encode("utf-8"), "examples_and_guidance.md", "text/markdown", use_container_width=True)
    st.download_button("Download project_state.srproj.json untuk dilanjutkan nanti", resume_project_state_bytes("Insight & Export"), "project_state.srproj.json", "application/json", use_container_width=True)
    st.download_button("Download semua hasil sebagai ZIP", make_export_zip(), "systematic_review_export_package.zip", "application/zip", use_container_width=True)


def main():
    init_state()
    render_sidebar()
    if st.session_state.get("reset_success_message"):
        st.success("Data project sudah dihapus. Tampilan dan isi sistem telah dikembalikan ke kondisi awal.")
        st.session_state.reset_success_message = False
    page = st.sidebar.radio(
        "Menu utama",
        [
            "Panduan Workflow",
            "1. Judul & PICOS/PECO",
            "2. Protocol & Search",
            "3-4. Import & Screening",
            "5-6. PRISMA & Quality",
            "7. Data Extraction",
            "8. Q-Level Tools",
            "9. Insight & Export",
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
    elif page == "8. Q-Level Tools":
        page_qlevel_tools()
    elif page == "9. Insight & Export":
        page_insight_export()


if __name__ == "__main__":
    main()
