"""Optional report refresh from legacy Python layout; requires Dash, pandas and Plotly.
The normal static build does not import this script or require these packages.
Run from any directory after updating the checked analysis artifacts.
"""
import sys,json,html
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import dash
from dash.development.base_component import Component
import research_page as page
root=ROOT
figures=[]
def render(node):
    if node is None: return ''
    if isinstance(node,(list,tuple)): return ''.join(map(render,node))
    if not isinstance(node,Component): return html.escape(str(node))
    obj=node.to_plotly_json(); props=obj['props']; tag=obj['type'].lower()
    if obj['namespace']=='dash_core_components':
        assert tag=='graph'
        index=len(figures); figures.append(json.loads(props['figure'].to_json()))
        return f'<div class="chart" id="chart-{index}" role="img" aria-label="{["Speaking pace distribution","Clip duration and speaking rate","Speaking pace by recording"][index]}"><p>Loading interactive chart…</p></div>'
    attrs=[]
    for key,value in props.items():
        if key=='children' or value is None: continue
        key={'className':'class','htmlFor':'for'}.get(key,key)
        if key=='src': value=value.lstrip('/')
        if isinstance(value,bool):
            if value: attrs.append(key)
        else: attrs.append(f'{key}="{html.escape(str(value),quote=True)}"')
    return '<'+tag+(' '+ ' '.join(attrs) if attrs else '')+'>'+render(props.get('children'))+'</'+tag+'>'
dash.get_asset_url=lambda name:'assets/'+name
body=render(page.layout())
(root/'index.html').write_text('''<!doctype html>
<html lang="en" data-mantine-color-scheme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="CosyVoice 3 Somali adaptation: corpus preparation, model fine-tuning, and frozen-component strategy.">
<title>Somali Voice Training</title>
<link rel="icon" href="assets/favicon.ico">
<link rel="stylesheet" href="assets/dashboard.css">
<script defer src="assets/plotly.min.js"></script>
<script defer src="assets/dashboard.js"></script>
</head><body>'''+body+'\n</body></html>\n',encoding='utf-8')
(root/'assets/charts.json').write_text(json.dumps(figures,separators=(',',':')),encoding='utf-8')
css=(root/'assets/styles.css').read_text()
start=css.index('.single-page {'); end=css.index('@media (max-width: 680px)',start); end=css.index('\n',end)
(root/'assets/dashboard.css').write_text('''* { box-sizing: border-box; }
html { scroll-behavior: smooth; background: #16171a; color-scheme: dark; }
body { margin: 0; }
.chart { width: 100%; min-height: 390px; }
.chart-error { padding: 24px; border: 1px solid #777d86; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
'''+css[start:end]+'\n',encoding='utf-8')
from plotly.offline import get_plotlyjs
(root/'assets/plotly.min.js').write_text(get_plotlyjs(),encoding='utf-8')
print('Exported HTML, original chart figures, styles, and bundled Plotly.js')
