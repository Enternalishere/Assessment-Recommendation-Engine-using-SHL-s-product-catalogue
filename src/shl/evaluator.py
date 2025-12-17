import os
import pandas as pd
from typing import List, Dict, Any
from .recommender import Recommender


DATASET_PATH = "Gen_AI Dataset.xlsx"
OUTPUT_DIR = "outputs"


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def read_train() -> List[Dict[str, Any]]:
    xls = pd.ExcelFile(DATASET_PATH)
    sn = None
    for s in xls.sheet_names:
        if "train" in s.lower():
            sn = s
            break
    if sn is None:
        sn = xls.sheet_names[0]
    df = xls.parse(sn)
    cols = [c for c in df.columns]
    q_col = None
    gt_col = None
    for c in cols:
        lc = c.lower()
        if "query" in lc:
            q_col = c
        if "url" in lc or "ground" in lc or "relevant" in lc:
            gt_col = c
    if q_col is None or gt_col is None:
        raise RuntimeError("train columns not found")
    rows = []
    for _, r in df.iterrows():
        q = str(r[q_col]).strip()
        gt = str(r[gt_col]).strip()
        gts = [x.strip() for x in gt.split(",") if x.strip()]
        rows.append({"query": q, "ground_truth": gts})
    return rows


def read_test() -> List[str]:
    xls = pd.ExcelFile(DATASET_PATH)
    sn = None
    for s in xls.sheet_names:
        if "test" in s.lower():
            sn = s
            break
    if sn is None:
        sn = xls.sheet_names[-1]
    df = xls.parse(sn)
    cols = [c for c in df.columns]
    q_col = None
    for c in cols:
        if "query" in c.lower():
            q_col = c
            break
    if q_col is None:
        q_col = cols[0]
    qs = [str(x).strip() for x in df[q_col].tolist() if str(x).strip()]
    return qs


def recall_at_10(pred: List[str], gt: List[str]) -> float:
    if not gt:
        return 0.0
    s_pred = set([x.strip().lower() for x in pred[:10]])
    s_gt = set([x.strip().lower() for x in gt])
    inter = s_pred.intersection(s_gt)
    return float(len(inter)) / float(len(s_gt))


def evaluate() -> Dict[str, Any]:
    ensure_dirs()
    rec = Recommender()
    train = read_train()
    rows = []
    vals = []
    for row in train:
        q = row["query"]
        gt = row["ground_truth"]
        items = rec.recommend(q, k=10)
        pred = [it["url"] for it in items]
        r = recall_at_10(pred, gt)
        rows.append({"query": q, "recall_at_10": r})
        vals.append(r)
    m = sum(vals) / len(vals) if vals else 0.0
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "train_recall.csv"), index=False)
    return {"mean_recall_at_10": m, "count": len(vals)}


def predict_test() -> str:
    ensure_dirs()
    rec = Recommender()
    tests = read_test()
    out_rows = []
    for q in tests:
        items = rec.recommend(q, k=10)
        for it in items:
            out_rows.append({"Query": q, "Assessment_URL": it["url"]})
    df = pd.DataFrame(out_rows)
    outp = os.path.join(OUTPUT_DIR, "test_predictions.csv")
    df.to_csv(outp, index=False)
    return outp

