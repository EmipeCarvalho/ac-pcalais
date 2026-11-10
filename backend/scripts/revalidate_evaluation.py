"""Reaplica guardrails às extrações salvas, sem fazer novas chamadas à IA."""
import argparse
import json
from pathlib import Path
from time import perf_counter
import pandas as pd
from pipeline import config, storage, validation
from scripts.run_batch import write_report


def revalidate(directory):
    directory = Path(directory).resolve()
    config.ITEMS_CSV = directory/'menu_items.csv'
    config.RUNS_CSV = directory/'pipeline_runs.csv'
    config.REPORTS_DIR = directory
    runs = storage.read_runs()
    groups = []
    count = 0
    for path in sorted((directory/'extracoes').glob('*.json')):
        result = json.loads(path.read_text())
        if 'initial_run' in result:
            raise ValueError('Esta avaliação já foi revalidada. Preserve a medição original; não execute novamente.')
        started = perf_counter()
        df = pd.DataFrame(result['items'])
        if df.empty:
            df = pd.DataFrame(columns=storage.ITEM_COLUMNS)
        df['empty_categories'] = sum(not category['items'] for category in result['menu']['categories'])
        df = validation.add_row_flags(df)
        report = validation.validate(df)
        df['menu_status'] = report['status']
        elapsed = perf_counter()-started
        result['initial_run'] = dict(result['run'])
        result['initial_validation'] = result['validation']
        run = result['run']
        run.update(status=report['status'], gx_score=report['score'], gx_passed=report['passed'], gx_total=report['total'],
                   latency_initial_s=run['latency_s'], offline_revalidation_s=round(elapsed, 4),
                   latency_s=round(run['latency_s']+elapsed, 4))
        result['validation'] = report
        result['items'] = json.loads(df.drop(columns=['variant_key','empty_categories'],errors='ignore').to_json(orient='records',force_ascii=False))
        for key, value in run.items():
            if key not in runs:
                runs[key] = None
            runs.loc[runs.run_id==run['run_id'],key] = value
        groups.append(df.reindex(columns=storage.ITEM_COLUMNS))
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
        count += 1
    if groups:
        pd.concat(groups,ignore_index=True).to_csv(config.ITEMS_CSV,index=False)
    runs.to_csv(config.RUNS_CSV,index=False)
    metrics = write_report()
    print(json.dumps({'revalidated':count,'new_api_calls':0,'metrics':metrics},ensure_ascii=False))
    return metrics


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    revalidate(parser.parse_args().directory)
