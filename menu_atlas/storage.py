import json
import sqlite3
from pathlib import Path
from time import perf_counter
import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
 id TEXT PRIMARY KEY, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 source TEXT NOT NULL, image_sha256 TEXT NOT NULL, restaurant TEXT,
 model TEXT NOT NULL, status TEXT NOT NULL, elapsed_seconds REAL,
 input_tokens INTEGER, output_tokens INTEGER, thinking_tokens INTEGER, estimated_cost_usd REAL,
 item_count INTEGER, missing_cells INTEGER, required_cells INTEGER, reasonable_prices INTEGER,
 raw_json TEXT NOT NULL, validation_json TEXT NOT NULL, error TEXT
);
CREATE TABLE IF NOT EXISTS items (
 id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(id),
 category TEXT, name TEXT, description TEXT, price REAL, currency TEXT,
 attributes TEXT NOT NULL, status TEXT NOT NULL, issues TEXT NOT NULL
);
"""

def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    return conn

def persist(path, run, started):
    quality = run.get("quality", {})
    extraction = run.get("extraction", {})
    menu = extraction.get("menu", {})
    with connect(path) as conn:
        conn.execute("""INSERT INTO runs (id,source,image_sha256,restaurant,model,status,
        input_tokens,output_tokens,thinking_tokens,estimated_cost_usd,item_count,missing_cells,
        required_cells,reasonable_prices,raw_json,validation_json,error)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            run["id"], run["source"], run["sha256"], menu.get("restaurant"), extraction.get("model", "unknown"), run["status"],
            extraction.get("input_tokens"), extraction.get("output_tokens"), extraction.get("thinking_tokens"), extraction.get("estimated_cost_usd"),
            quality.get("item_count", 0), quality.get("missing_cells", 0), quality.get("required_cells", 0), quality.get("reasonable_prices", 0),
            json.dumps(menu, ensure_ascii=False), json.dumps(quality, ensure_ascii=False), run.get("error")))
        for row in quality.get("items", []):
            conn.execute("INSERT INTO items (run_id,category,name,description,price,currency,attributes,status,issues) VALUES (?,?,?,?,?,?,?,?,?)", (
                run["id"], row["category"], row["name"], row["description"], row["price"], row["currency"],
                json.dumps(row["attributes"], ensure_ascii=False), row["status"], json.dumps(row["issues"])))
    # Mede até o commit de dados; grava a medição em transação separada.
    elapsed = perf_counter() - started
    with connect(path) as conn:
        conn.execute("UPDATE runs SET elapsed_seconds=? WHERE id=?", (elapsed, run["id"]))
    run["elapsed_seconds"] = elapsed
    return run

def tables(path):
    with connect(path) as conn:
        return (pd.read_sql_query("SELECT * FROM runs ORDER BY created_at DESC", conn),
                pd.read_sql_query("SELECT * FROM items", conn))

def summarize(runs):
    done = runs[runs.status != "failed"]
    cells = int(done.required_cells.sum())
    items = int(done.item_count.sum())
    return {"attempts": len(runs), "processed": len(done), "failed": int((runs.status == "failed").sum()),
            "items": items, "missing_pct": 100 * done.missing_cells.sum() / cells if cells else None,
            "reasonable_price_pct": 100 * done.reasonable_prices.sum() / items if items else None,
            "mean_latency_seconds": float(done.elapsed_seconds.mean()) if len(done) else None,
            "mean_cost_usd": float(done.estimated_cost_usd.mean()) if len(done) and done.estimated_cost_usd.notna().all() else None,
            "cost_known_runs": int(done.estimated_cost_usd.notna().sum()),
            "input_tokens": int(done.input_tokens.fillna(0).sum()),
            "output_tokens": int(done.output_tokens.fillna(0).sum()),
            "thinking_tokens": int(done.thinking_tokens.fillna(0).sum())}
