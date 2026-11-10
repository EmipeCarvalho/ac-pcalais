import io
import json
from time import perf_counter
from PIL import Image
from menu_atlas.quality import validate_menu
from menu_atlas.storage import persist, tables, summarize
from menu_atlas.pipeline import process_menu

GOOD={"restaurant":"Café", "categories":["Bebidas"], "items":[{"category":"Bebidas","name":"Café expresso","price":8.5,"currency":"BRL"}], "warnings":[]}

def test_valid_menu():
    q=validate_menu(GOOD)
    assert not q["needs_review"]
    assert q["reasonable_price_pct"] == 100
    assert q["missing_pct"] == 0
    assert len(q["checks"]) == 9

def test_guardrails_do_not_hide_errors():
    raw={"categories":["Bebidas"],"items":[
        {"name":"Café","category":"Bebidas","price":-1,"currency":"BRL"},
        {"name":"Café","category":"Bebidas","price":-1,"currency":"BRL"},
        {"name":" ","category":"Outra","price":None,"currency":None}]}
    q=validate_menu(raw)
    assert q["needs_review"] and q["missing_cells"] == 3
    assert q["reasonable_prices"] == 0
    assert "possible_duplicate" in q["items"][0]["issues"]
    assert "unknown_category" in q["items"][2]["issues"]
    assert any(not c["success"] for c in q["checks"])

def test_empty_is_review_not_perfect():
    q=validate_menu({"items":[]})
    assert q["needs_review"] and q["missing_pct"] is None

def test_append_and_metrics(tmp_path):
    db=str(tmp_path/"test.sqlite")
    q=validate_menu(GOOD)
    for id_ in ["one","two"]:
        persist(db,{"id":id_,"source":"test","sha256":id_,"status":"valid","quality":q,
          "extraction":{"menu":GOOD,"model":"test","input_tokens":5,"output_tokens":2,"thinking_tokens":0,"estimated_cost_usd":None}},perf_counter())
    runs,items=tables(db)
    assert len(runs)==2 and len(items)==2
    m=summarize(runs)
    assert m["missing_pct"]==0 and m["mean_cost_usd"] is None

def test_full_flow_mocked_provider(tmp_path,monkeypatch):
    import menu_atlas.pipeline as pipeline
    monkeypatch.setattr(pipeline,"extract_image",lambda *a: {"menu":GOOD,"model":"mock","input_tokens":10,"output_tokens":10,"thinking_tokens":0,"estimated_cost_usd":None})
    image=io.BytesIO(); Image.new("RGB",(40,40),"white").save(image,"PNG")
    result=process_menu(image.getvalue(),db_path=str(tmp_path/"flow.sqlite"))
    assert result["status"]=="valid"
    assert result["elapsed_seconds"]>0
    assert len(tables(str(tmp_path/"flow.sqlite"))[1])==1

def test_corrupt_image_recorded_as_failure(tmp_path):
    result=process_menu(b"not an image",db_path=str(tmp_path/"failure.sqlite"))
    assert result["status"]=="failed"
    assert tables(str(tmp_path/"failure.sqlite"))[0].iloc[0].status=="failed"

def test_extraction_free_tier_counts_tokens(monkeypatch):
    from types import SimpleNamespace
    import menu_atlas.extraction as extraction
    usage=SimpleNamespace(prompt_token_count=100,candidates_token_count=20,thoughts_token_count=5)
    class Client:
        def __init__(self, **kwargs):
            self.models=SimpleNamespace(generate_content=lambda **kw: SimpleNamespace(text=json.dumps(GOOD),usage_metadata=usage))
        def __enter__(self): return self
        def __exit__(self,*args): pass
    monkeypatch.setattr(extraction.genai,'Client',Client)
    monkeypatch.setenv('GEMINI_PRICING_TIER','free')
    result=extraction.extract_image(b'fake-image',api_key='test-only')
    assert result['estimated_cost_usd']==0
    assert result['thinking_tokens']==5
    monkeypatch.delenv('GEMINI_PRICING_TIER')
    monkeypatch.setenv('INPUT_USD_PER_MILLION','1')
    monkeypatch.setenv('OUTPUT_USD_PER_MILLION','2')
    result=extraction.extract_image(b'fake-image',api_key='test-only')
    assert abs(result['estimated_cost_usd']-0.00015)<1e-10
