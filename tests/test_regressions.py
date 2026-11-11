import io
import time
from pathlib import Path
import pandas as pd
import pytest
from PIL import Image
from pipeline import config, extractor, flow, storage, validation
from pipeline.metrics import compute_metrics
from pipeline.schemas import MenuExtraction


def frame(prices):
    return pd.DataFrame([dict(category='Pratos', item_name=f'Prato {i}', price=v,
                             variant_label=None, currency='BRL', empty_categories=0)
                         for i, v in enumerate(prices)])


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ITEMS_CSV', tmp_path/'items.csv')
    monkeypatch.setattr(config, 'RUNS_CSV', tmp_path/'runs.csv')
    monkeypatch.setattr(config, 'REPORTS_DIR', tmp_path)


@pytest.mark.parametrize('prices', [[None,None,20], [2000,300,400,500], [-5,20,30]])
def test_critical_quality_failures_require_review(prices):
    result = validation.validate(validation.add_row_flags(frame(prices)))
    assert result['status'] == 'revisao_humana'


def test_valid_menu_passes():
    result = validation.validate(validation.add_row_flags(frame([10,20,30])))
    assert result['status'] == 'aprovado'


def test_prices_include_missing_in_denominator():
    m = compute_metrics(frame([None,None,20]), pd.DataFrame(columns=storage.RUN_COLUMNS))
    assert m['pct_precos_razoaveis'] == 33.33
    assert m['precos_ausentes'] == 2
    assert m['custo_medio_usd'] is None


def test_retries_and_unknown_cost(monkeypatch):
    assert flow.extract.retries == 0
    monkeypatch.setattr(config, 'PRICE_INPUT_PER_1M', None)
    assert extractor.estimate_cost({'input_tokens':10,'output_tokens':20}) is None


def test_real_flow_persists_post_write_latency(isolated_storage, monkeypatch):
    menu = MenuExtraction(is_menu=True,restaurant_name='Teste',currency='BRL',legibility='boa',notes=None,
        categories=[{'name':'Bebidas','items':[{'name':'Suco','description':None,'price':10,'variants':[],'attributes':[]}]}])
    monkeypatch.setattr(extractor, 'extract_menu', lambda *a: (menu,dict(model='mock',input_tokens=10,output_tokens=10,cost_usd=None)))
    original = storage.append_items
    def slow(df):
        time.sleep(.2)
        original(df)
    monkeypatch.setattr(storage, 'append_items', slow)
    b=io.BytesIO();Image.new('RGB',(30,30)).save(b,'PNG')
    result=flow.menu_pipeline(b.getvalue(),'test.png')
    saved=storage.read_runs().iloc[0]
    assert result['run']['status']=='aprovado'
    assert saved.latency_s >= .2
    assert saved.latency_s == result['run']['latency_s']
    assert len(saved.image_sha256)==64
    assert compute_metrics()['menus_distintos_sem_erro']==1


def test_ui_empty_result_and_only_errors(isolated_storage):
    from streamlit.testing.v1 import AppTest
    app=Path(__file__).resolve().parents[1]/'backend/app.py'
    baseline=AppTest.from_file(str(app), default_timeout=30).run()
    assert not baseline.exception
    empty=AppTest.from_string('''from app import show_result
show_result({'items': [],'run': {'status':'revisao_humana','is_menu':False,'n_items':0,'n_categories':0,'latency_s':1,'input_tokens':10,'output_tokens':10,'cost_usd':None},'validation': {'checks':[],'passed':0,'total':15},'menu':{}},'vazia.jpg')''',default_timeout=30).run()
    assert not empty.exception
    storage.append_run(dict(run_id='error',source_file='bad.png',status='erro',error='test',latency_s=1))
    errors=AppTest.from_file(str(app), default_timeout=30).run()
    assert not errors.exception


def test_unknown_failed_cost_does_not_look_free():
    runs=pd.DataFrame([dict(status='erro',cost_usd=None)],columns=storage.RUN_COLUMNS)
    m=compute_metrics(pd.DataFrame(columns=storage.ITEM_COLUMNS),runs)
    assert m['custo_total_usd'] is None
    assert m['execucoes_custo_desconhecido']==1


def test_unique_hashes_not_execution_count():
    runs=pd.DataFrame([dict(status='aprovado',image_sha256='same',cost_usd=0.1)]*50,columns=storage.RUN_COLUMNS)
    m=compute_metrics(pd.DataFrame(columns=storage.ITEM_COLUMNS),runs)
    assert m['menus_distintos_sem_erro']==1
    assert not m['meta_50_cardapios_atingida']


def test_validation_failure_preserves_known_usage(isolated_storage, monkeypatch):
    menu = MenuExtraction(is_menu=True,restaurant_name='Teste',currency='BRL',legibility='boa',notes=None,
        categories=[{'name':'Bebidas','items':[{'name':'Suco','description':None,'price':10,'variants':[],'attributes':[]}]}])
    monkeypatch.setattr(extractor, 'extract_menu', lambda *a: (menu,dict(model='mock',input_tokens=10,output_tokens=10,cost_usd=.01)))
    def fail(*args):
        raise RuntimeError('simulated validation error')
    monkeypatch.setattr(validation, 'validate', fail)
    b=io.BytesIO();Image.new('RGB',(30,30)).save(b,'PNG')
    with pytest.raises(RuntimeError):
        flow.menu_pipeline(b.getvalue(),'test.png')
    saved = storage.read_runs().iloc[0]
    assert saved.status == 'erro'
    assert saved.cost_usd == .01
    assert saved.model == 'mock'


def test_iso_currency_inr_is_supported():
    df = frame([100,200,300])
    df["currency"] = "INR"
    result = validation.validate(validation.add_row_flags(df))
    assert result["status"] == "aprovado"
    df["currency"] = "ZZZ"
    result = validation.validate(validation.add_row_flags(df))
    assert result["status"] == "revisao_humana"
