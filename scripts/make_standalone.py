#!/usr/bin/env python3
"""Generate a fully self-contained standalone.html for deployment.
Supports Next.js out/ build export and legacy dist/ output.
Output: standalone.html.
"""
import base64, os, sys, glob

out_dir = os.path.join(os.path.dirname(__file__), '..', 'out')
dist_dir = os.path.join(os.path.dirname(__file__), '..', 'dist')
public_dir = os.path.join(os.path.dirname(__file__), '..', 'public')
out_path = os.path.join(os.path.dirname(__file__), '..', 'standalone.html')

css_content = ""
js_content = ""

if os.path.exists(out_dir):
    css_files = glob.glob(os.path.join(out_dir, '_next', 'static', 'css', '*.css'))
    for f in css_files:
        with open(f, 'r') as cf:
            css_content += cf.read() + "\n"
    
    js_files = glob.glob(os.path.join(out_dir, '_next', 'static', 'chunks', '**', '*.js'), recursive=True)
    for f in js_files:
        with open(f, 'r') as jf:
            js_content += jf.read() + "\n"
elif os.path.exists(dist_dir):
    dist_assets = os.path.join(dist_dir, 'assets')
    css_file = next((f for f in os.listdir(dist_assets) if f.endswith('.css')), None)
    js_file = next((f for f in os.listdir(dist_assets) if f.endswith('.js')), None)
    if css_file:
        with open(os.path.join(dist_assets, css_file)) as f: css_content = f.read()
    if js_file:
        with open(os.path.join(dist_assets, js_file)) as f: js_content = f.read()

if not css_content and not js_content:
    print("ERROR: Neither out/ nor dist/ build assets found. Run 'npm run build' first.", file=sys.stderr)
    sys.exit(1)

def b64(path):
    if not os.path.exists(path):
        return ""
    with open(path, 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

ail = b64(os.path.join(public_dir, 'brand-assets', 'ail-header.png'))
fav = b64(os.path.join(public_dir, 'favicon.png'))

for old, new in [
    ('`/brand-assets/ail-header.png`', f'`{ail}`'),
    ('"/brand-assets/ail-header.png"', f'"{ail}"'),
    ('`/favicon.png`', f'`{fav}`'),
    ('"/favicon.png"', f'"{fav}"'),
]:
    if ail:
        js_content = js_content.replace(old, new)

html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/png" href="{fav}" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ART Investigation Lab</title>
  <style>
{css_content}
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="module">
{js_content}
  </script>
</body>
</html>'''

with open(out_path, 'w') as f:
    f.write(html)

size_kb = os.path.getsize(out_path) / 1024
img_hits = js_content.count('data:image/png;base64')
print(f"standalone.html written: {size_kb:.1f} KB  (base64 images in JS: {img_hits})")
