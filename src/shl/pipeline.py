import argparse
from typing import Dict, Any
from .scraper import run as scrape_run
from .indexer import index as index_run
from .evaluator import evaluate as eval_run, predict_test as predict_run
import uvicorn


def do_scrape() -> Dict[str, Any]:
    return scrape_run()


def do_index() -> Dict[str, Any]:
    return index_run()


def do_evaluate() -> Dict[str, Any]:
    return eval_run()


def do_predict() -> str:
    return predict_run()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd")
    args = p.parse_args()
    if args.cmd == "scrape":
        r = do_scrape()
        print(r)
    elif args.cmd == "index":
        r = do_index()
        print(r)
    elif args.cmd == "evaluate":
        r = do_evaluate()
        print(r)
    elif args.cmd == "predict":
        r = do_predict()
        print(r)
    elif args.cmd == "serve":
        uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=False)
    else:
        print({"error": "unknown cmd"})


if __name__ == "__main__":
    main()

