import os
import sys
from datetime import datetime, timezone
import yaml

POSTS_DIR = "posts"
DIST_DIR = "dist"
OUTPUT_POSTS_DIR = os.path.join(DIST_DIR, "posts")
BLOG_YAML = "blog.yaml"


FAVICON_FILES = ["favicon.svg", "favicon-96x96.png", "favicon.ico", "apple-touch-icon.png"]


def ensure_dirs():
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_POSTS_DIR, exist_ok=True)
    import shutil
    for icon in FAVICON_FILES:
        if os.path.exists(icon):
            shutil.copy2(icon, os.path.join(DIST_DIR, icon))


def extract_title(tex_path: str) -> str:
    with open(tex_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith(r"\title{") and line.endswith("}"):
                return line[7:-1].strip()
    return os.path.splitext(os.path.basename(tex_path))[0]


def load_yaml(path: str = BLOG_YAML):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    return []


def save_yaml(data, path: str = BLOG_YAML):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


def generate_viewer(post_id: str, title: str) -> None:
    html_path = os.path.join(OUTPUT_POSTS_DIR, f"{post_id}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="icon" type="image/png" href="../favicon-96x96.png" sizes="96x96" />
  <link rel="icon" type="image/svg+xml" href="../favicon.svg" />
  <link rel="shortcut icon" href="../favicon.ico" />
  <link rel="apple-touch-icon" sizes="180x180" href="../apple-touch-icon.png" />
  <style>
    body {{ margin: 0; background: #f7f3ed; }}
    #pdf-viewer {{ width: 100vw; height: 100vh; overflow: auto; }}
    canvas {{ display: block; margin: 0 auto; }}
  </style>
</head>
<body>
  <div id="pdf-viewer"></div>
  <script src="https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js"></script>
  <script>
    const url = '{post_id}.pdf';
    const viewer = document.getElementById('pdf-viewer');
    pdfjsLib.GlobalWorkerOptions.workerSrc =
      'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js';
    const CMAP_URL = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/';

    (async () => {{
      const pdf = await pdfjsLib.getDocument({{
        url,
        cMapUrl: CMAP_URL,
        cMapPacked: true,
        useSystemFonts: true
      }}).promise;

      const cssScale = 1.5;
      const outputScale = window.devicePixelRatio || 1;

      for (let i = 1; i <= pdf.numPages; i++) {{
        const page = await pdfjsLib.getDocument ? await pdf.getPage(i) : null;
        const viewport = page.getViewport({{ scale: cssScale }});
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.style.width = `${{viewport.width}}px`;
        canvas.style.height = `${{viewport.height}}px`;
        viewer.appendChild(canvas);
        await page.render({{
          canvasContext: context,
          viewport,
          transform: outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null
        }}).promise;
      }}
    }})();
  </script>
</body>
</html>
''')


def update_index(tex_files):
    ensure_dirs()
    existing = {item["file"]: item for item in load_yaml()}
    updated = {}

    for tex in tex_files:
      name = os.path.splitext(os.path.basename(tex))[0]
      title = extract_title(tex)
      pdf_src = f"{name}.pdf"
      pdf_dst = os.path.join(OUTPUT_POSTS_DIR, pdf_src)
      if os.path.exists(pdf_src):
          if os.path.exists(pdf_dst):
              os.remove(pdf_dst)
          os.replace(pdf_src, pdf_dst)

      first_date = existing.get(name, {}).get("date", datetime.now().strftime("%Y-%m-%d"))
      updated[name] = {
          "file": name,
          "title": title,
          "date": first_date,
          "publish": existing.get(name, {}).get("publish", True),
      }
      generate_viewer(name, title)

    combined = list(updated.values()) + [v for k, v in existing.items() if k not in updated]
    save_yaml(combined)


def generate_front_page():
    items = [p for p in load_yaml() if p.get("publish", True)]
    items.sort(key=lambda p: p.get("date", ""), reverse=True)
    with open(os.path.join(DIST_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LaTeX Blog Template</title>
  <meta name="description" content="A LaTeX blog template with GitHub Actions compilation and a blog-style landing page.">
  <link rel="icon" type="image/png" href="favicon-96x96.png" sizes="96x96">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="shortcut icon" href="favicon.ico">
  <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="wrapper">
    <header class="hero">
      <p class="eyebrow">Your Name</p>
      <h1>LaTeX Blog Template</h1>
      <p class="hero-copy">A blog-style LaTeX template that compiles posts with GitHub Actions.</p>
    </header>

    <section class="manifesto" id="manifesto">
      <div class="manifesto-kicker">Manifesto</div>
      <div class="manifesto-body">
        <p>Write with the clarity of LaTeX, publish with the ease of GitHub Pages.</p>
      </div>
    </section>

    <section class="index-block">
      <div class="index-heading">
        <h2>Posts</h2>
        <span>latest first</span>
      </div>
      <nav><ul>
''')
        for post in items:
            fh.write(f'      <li><a href="posts/{post["file"]}.html">{post["title"]}</a><time datetime="{post["date"]}">{post["date"]}</time></li>\n')
        fh.write('''      </ul></nav>
    </section>

    <p class="footer-note">Generated from `posts/*.tex` by GitHub Actions.</p>
  </div>
</body>
</html>
''')


def _rfc822(dt_str: str) -> str:
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def _pdf_size_bytes(slug: str) -> str:
    pdf_path = os.path.join(OUTPUT_POSTS_DIR, f"{slug}.pdf")
    try:
        return str(os.path.getsize(pdf_path))
    except OSError:
        return "0"


def generate_feed(out_path: str = os.path.join(DIST_DIR, "feed.xml")) -> None:
    items = [it for it in load_yaml() if it.get("publish", True)]
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    channel_title = "LaTeX Blog Template"
    channel_link = "https://latex-blog-template.stonezhang.com/"
    channel_desc = "A blog-style LaTeX template with automated GitHub Actions compilation."
    last_build = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        f'    <title>{channel_title}</title>',
        f'    <link>{channel_link}</link>',
        f'    <description>{channel_desc}</description>',
        '    <language>en-us</language>',
        f'    <lastBuildDate>{last_build}</lastBuildDate>',
        f'    <atom:link href="{channel_link}feed.xml" rel="self" type="application/rss+xml" />',
        ''
    ]
    for it in items:
        slug = it['file']
        title = it.get('title', slug)
        date = _rfc822(it.get('date', '1970-01-01'))
        url = f'{channel_link}posts/{slug}.html'
        pdf_url = f'{channel_link}posts/{slug}.pdf'
        size = _pdf_size_bytes(slug)
        lines += [
            '    <item>',
            f'      <title>{title}</title>',
            f'      <link>{url}</link>',
            f'      <guid isPermaLink="true">{url}</guid>',
            f'      <enclosure url="{pdf_url}" type="application/pdf" length="{size}" />',
            f'      <pubDate>{date}</pubDate>',
            '    </item>',
            ''
        ]
    lines += ['  </channel>', '</rss>']
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != 'from_tex':
        print('Usage: python build_blog.py from_tex posts/blog0.tex posts/blog1.tex ...')
        sys.exit(1)
    tex_files = sys.argv[2:]
    ensure_dirs()
    update_index(tex_files)
    generate_front_page()
    generate_feed()
