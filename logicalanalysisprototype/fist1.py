import spacy
from sentence_transformers import SentenceTransformer, util

nlp = spacy.load("ja_ginza", exclude=["compound_splitter"])
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

DISCOURSE_MARKERS = ["しかし", "一方で", "そのため", "したがって", "だから", "でも", "ところが"]
HUMAN_WORDS = ["彼", "彼女", "私", "僕", "俺", "あなた", "君", "先生", "社長"]
ABSTRACT_WORDS = ["それ", "これ", "あれ", "こと", "もの", "ため", "わけ"]
ABSTRACT_TRIGGERS = ["重要", "可能性", "示唆", "考えられる", "必要", "有用", "影響", "検討", "課題", "観点"]

def classify_subject_type(word):
    if any(h in word for h in HUMAN_WORDS): return "human"
    if any(a in word for a in ABSTRACT_WORDS): return "abstract"
    return "entity"

def adjust_confidence(base, sentence):
    if "好き" in sentence or "思う" in sentence or "感じ" in sentence: base -= 0.2
    if sentence.endswith("だ。") or sentence.endswith("である。"): base -= 0.1
    return round(max(0.0, min(base, 1.0)), 2)

def analyze_sentence_structure(doc):
    results = []
    for sent in doc.sents:
        subj = root = obj = None
        subj_conf = subj_type = None
        for token in sent:
            if token.dep_ == "nsubj":
                if token.head.dep_ in ("acl", "relcl", "compound"): continue
                subj = token.text
                subj_type = classify_subject_type(token.text)
                if any(c.text == "が" for c in token.children): base = 0.95
                elif any(c.text == "は" for c in token.children): base = 0.75
                else: base = 0.55
                subj_conf = adjust_confidence(base, sent.text)
            if token.dep_ == "ROOT": root = token.lemma_
            if token.dep_ in ("obj", "dobj"): obj = token.text
        results.append({
            "sentence": sent.text,
            "subject": subj,
            "subject_type": subj_type,
            "subject_confidence": subj_conf,
            "predicate": root,
            "object": obj
        })
    return results

def detect_subject_missing(structure_results):
    return [{"sentence": r["sentence"], "alert": "主語不在アラート"}
            for r in structure_results if r["subject"] is None]

def classify_jump(score):
    if score < 0: return "トピックジャンプ"
    if score < 0.2: return "弱い関連"
    return None

def semantic_coherence(doc, min_len=5):
    sentences = [sent.text for sent in doc.sents]
    embeddings = model.encode(sentences, convert_to_tensor=True)
    alerts = []
    for i in range(len(sentences) - 1):
        s1, s2 = sentences[i], sentences[i+1]
        if len(s1) < min_len or len(s2) < min_len: continue
        if any(m in s2 for m in DISCOURSE_MARKERS): continue
        score = util.cos_sim(embeddings[i], embeddings[i+1]).item()
        threshold = 0.1 if any(m in s1 for m in DISCOURSE_MARKERS) else 0.2
        jump_type = classify_jump(score) if score < threshold else None
        if jump_type:
            alerts.append({"pair": (s1, s2), "similarity": round(score, 3), "alert": jump_type})
    return alerts

# 抽象語トリガーで弱い主張を検出
def detect_weak_claims(doc):
    alerts = []
    for sent in doc.sents:
        if any(word in sent.text for word in ABSTRACT_TRIGGERS):
            alerts.append({
                "sentence": sent.text,
                "alert": "弱い主張",
                "reason": "抽象表現が多く、具体性が不足"
            })
    return alerts

# 抽象語密度（論文ポエム検出）
def abstract_density(doc):
    tokens = [t for t in doc if not t.is_punct]
    if not tokens: return 0
    count = sum(1 for t in tokens if t.text in ABSTRACT_TRIGGERS)
    return round(count / len(tokens), 3)

def detect_poetic_density(doc, threshold=0.6, min_tokens=10):
    tokens = [t for t in doc if not t.is_punct]
    if len(tokens) < min_tokens: return None
    adj_adv = sum(1 for t in tokens if t.pos_ in ("ADJ", "ADV"))
    content = sum(1 for t in tokens if t.pos_ in ("NOUN", "PROPN", "VERB"))
    if content == 0: return None
    ratio = adj_adv / content
    density = abstract_density(doc)
    # 形容詞・副詞ベース + 抽象語密度の両方で判定
    alert = None
    if ratio > threshold: alert = "ポエム検知（深夜ラブレター）"
    elif density > 0.15: alert = "抽象度過多"
    return {"ratio": round(ratio, 3), "abstract_density": density, "alert": alert}

def compute_score(structure, subject_alerts, coherence_alerts, weak_claims, poetic):
    confs = [s["subject_confidence"] for s in structure if s["subject_confidence"]]
    subject_score = round(sum(confs) / len(confs) * 100, 1) if confs else 0.0
    subject_score = max(0, subject_score - len(subject_alerts) * 15)

    logic_score = 100
    for a in coherence_alerts:
        if a["alert"] == "トピックジャンプ": logic_score -= 30
        elif a["alert"] == "弱い関連": logic_score -= 15
    logic_score = max(0, logic_score)

    poetic_penalty = 0
    if poetic and poetic["alert"]:
        poetic_penalty = min(30, int(poetic.get("ratio", 0) * 30) + int(poetic.get("abstract_density", 0) * 50))

    overall = round((subject_score * 0.4 + logic_score * 0.6) - poetic_penalty, 1)

    return {
        "総合スコア": max(0, overall),
        "主語明確性": subject_score,
        "論理整合性": logic_score,
        "ポエム減点": poetic_penalty,
        "問題数": {
            "主語": len(subject_alerts),
            "論理": len(coherence_alerts),
            "表現": len(weak_claims),
            "ポエム": 1 if poetic and poetic["alert"] else 0
        }
    }

def full_analysis(text):
    doc = nlp(text)
    structure = analyze_sentence_structure(doc)
    subject_alerts = detect_subject_missing(structure)
    coherence_alerts = semantic_coherence(doc)
    weak_claims = detect_weak_claims(doc)
    poetic = detect_poetic_density(doc)
    score = compute_score(structure, subject_alerts, coherence_alerts, weak_claims, poetic)
    return {
        "score": score,
        "structure": structure,
        "subject_alerts": subject_alerts,
        "coherence_alerts": coherence_alerts,
        "weak_claims": weak_claims,
        "poetic": poetic
    }
