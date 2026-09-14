"""Package the dashboard for GitHub Pages using only the Python standard library."""
from pathlib import Path
import shutil
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dist'

class AssetChecker(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('src', 'href') and value and not value.startswith(('#', 'https:', 'http:')):
                assert not value.startswith('/'), f'Asset must be relative for project Pages: {value}'
                assert (ROOT / value).is_file(), f'Missing asset: {value}'

if __name__ == '__main__':
    AssetChecker().feed((ROOT / 'index.html').read_text(encoding='utf-8'))
    OUTPUT.mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'index.html', OUTPUT / 'index.html')
    destination = OUTPUT / 'assets'
    destination.mkdir(exist_ok=True)
    for name in ('dashboard.css', 'dashboard.js', 'charts.json', 'plotly.min.js', 'favicon.ico'):
        shutil.copy2(ROOT / 'assets' / name, destination / name)
    shutil.copytree(ROOT / 'assets/audio', destination / 'audio', dirs_exist_ok=True)
    (OUTPUT / '.nojekyll').touch()
    print(f'Static dashboard built: {OUTPUT}')
