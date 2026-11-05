from pathlib import Path
import csv,hashlib,json,re,zipfile
root=Path(__file__).resolve().parents[2]
with zipfile.ZipFile(root.parent/'d12-round1-review.zip') as z:
 old=list(csv.DictReader(z.read('experiments/d12-forecast-errors/practice/results/metrics.csv').decode().splitlines()))
 new=list(csv.DictReader((root/'experiments/d12-forecast-errors/practice/results/metrics.csv').read_text().splitlines()))
 assert len(old)==len(new)==42
 maxdiff=max(abs(float(a[k])-float(b[k])) for a,b in zip(old,new) for k in ('me','mae','rmse','wape'))
 assert all(format(float(a[k])*(100 if k=='wape' else 1),'.4f')==format(float(b[k])*(100 if k=='wape' else 1),'.4f') for a,b in zip(old,new) for k in ('me','mae','rmse','wape'))
 for name in ('daily_predictions.csv','five_day_windows.csv','manual_oracle.json'):
  assert z.read('experiments/d12-forecast-errors/practice/results/'+name)==(root/'experiments/d12-forecast-errors/practice/results'/name).read_bytes()
 article=(root/'content/blog/forecast-error-bias-metrics/index.md').read_text()
 numeric_rows=re.findall(r'<tr>(<td.*?</td>)</tr>',article)
 assert len(numeric_rows)==42
 actual=[re.findall(r'<td[^>]*>(.*?)</td>',cells) for cells in numeric_rows]
 expected=[]
 for case in ('hewei','apparel'):
  for scope in ('all','group'):
   expected += [r for r in new if r['case']==case and ((r['group']=='all')==(scope=='all'))]
 for vals,r in zip(actual,expected):
  assert vals[2]==r['n']
  assert vals[3:]==[format(float(r[k]),'.4f') for k in ('me','mae','rmse')]+[format(float(r['wape'])*100,'.4f')+'%']
 report={'v1_zip_sha256':hashlib.sha256((root.parent/'d12-round1-review.zip').read_bytes()).hexdigest(),'metric_rows':42,'displayed_numeric_values_verified':210,'all_displayed_values_unchanged':True,'maximum_metric_float_delta':maxdiff,'unchanged_results':['daily_predictions.csv','five_day_windows.csv','manual_oracle.json']}
 (root/'docs/d12-review/v2-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
