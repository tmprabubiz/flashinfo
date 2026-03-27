import os, csv, json
from pathlib import Path

base_path = Path(__file__).resolve().parent
CSV_INPUT = base_path / "data" / "flash_info_output.csv"
HTML_OUTPUT = base_path / "docs" / "index.html"

def generate():
    rows = []
    if CSV_INPUT.exists():
        with open(CSV_INPUT, 'r', encoding='utf-8-sig') as f:
            rows = [r for r in csv.DictReader(f) if r.get('title')]
    
    rows.sort(key=lambda x: x.get('date', ''), reverse=True)
    domains = sorted(list(set(r['domain'] for r in rows)))

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FLASH INFO | V26 Oracle</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #020617; color: #f8fafc; font-family: 'Inter', sans-serif; }}
            .glass {{ background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.05); }}
            .tab-active {{ border-bottom: 3px solid #38bdf8; color: #38bdf8; }}
        </style>
    </head>
    <body class="p-4 md:p-12">
        <header class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6 mb-16">
            <h1 onclick="unlockAdmin()" class="text-5xl font-black text-sky-400 cursor-pointer tracking-tighter">FLASH INFO</h1>
            <div class="flex flex-wrap justify-center gap-4">
                <select id="domFilt" onchange="filter()" class="glass rounded-2xl px-6 py-3 text-sm outline-none">
                    <option value="ALL">All Domains</option>
                    {"".join([f'<option value="{d}">{d}</option>' for d in domains])}
                </select>
                <input type="text" id="search" oninput="filter()" placeholder="Deep Search entire history..." class="glass rounded-2xl px-8 py-3 text-sm w-full md:w-80">
            </div>
        </header>

        <nav class="max-w-7xl mx-auto mb-10 flex gap-10 border-b border-slate-800 text-[10px] font-black tracking-widest uppercase">
            <button onclick="tab('ALL')" id="t-ALL" class="tab-btn pb-4 tab-active">ALL FEED</button>
            <button onclick="tab('SPARK')" id="t-SPARK" class="tab-btn pb-4 text-slate-500">SPARKS</button>
            <button onclick="tab('CONTEXT')" id="t-CONTEXT" class="tab-btn pb-4 text-slate-500">CONTEXT</button>
            <button id="adminBtn" onclick="tab('ADMIN')" class="hidden pb-4 text-red-500">ADMIN</button>
        </nav>

        <main id="grid" class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10"></main>
        <div id="loadMore" class="text-center mt-20 mb-32"><button onclick="load()" class="glass px-12 py-4 rounded-full text-xs font-black tracking-widest text-sky-400">LOAD MORE</button></div>

        <script>
            const fullData = {json.dumps(rows)};
            let curTab = 'ALL'; let page = 1;

            function filter() {{
                page = 1;
                const s = document.getElementById('search').value.toLowerCase();
                const d = document.getElementById('domFilt').value;
                const filtered = fullData.filter(i => {{
                    const mTab = curTab === 'ALL' || i.source_group.toUpperCase() === curTab;
                    const mDom = d === 'ALL' || i.domain === d;
                    // RECTIFICATION: GLOBAL SEARCH (Item 12)
                    const mSea = (i.title + i.summary_snippet + i.domain).toLowerCase().includes(s);
                    return mTab && mDom && mSea;
                }});
                render(filtered);
            }}

            function render(list) {{
                const grid = document.getElementById('grid');
                grid.innerHTML = '';
                list.slice(0, page * 12).forEach(i => {{
                    const c = document.createElement('div');
                    c.className = 'glass p-8 rounded-[2.5rem] flex flex-col justify-between hover:bg-slate-900/50 transition-all';
                    c.innerHTML = `<div><div class="flex justify-between mb-6"><span class="text-[10px] text-sky-500 font-bold uppercase tracking-widest">${{i.domain}}</span><span class="text-[10px] text-slate-600 font-mono">${{i.date}}</span></div><h3 class="text-xl font-bold mb-4 leading-tight">${{i.title}}</h3><p class="text-xs text-slate-400 leading-relaxed">${{i.summary_snippet}}</p></div><div class="mt-8 pt-6 border-t border-slate-800 flex justify-between items-center"><span class="text-[10px] font-bold text-slate-700 uppercase">${{i.source_group}}</span><a href="${{i.url}}" target="_blank" class="text-[10px] text-sky-400 font-black">ORIGIN &rarr;</a></div>`;
                    grid.appendChild(c);
                }});
            }}

            function tab(t) {{ curTab = t; document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('tab-active', 'text-sky-400')); document.getElementById('t-'+(t==='ADMIN'?'ALL':t)).classList.add('tab-active', 'text-sky-400'); filter(); }}
            function load() {{ page++; filter(); }}
            let clks = 0; function unlockAdmin() {{ clks++; if(clks===5) {{ document.getElementById('adminBtn').classList.remove('hidden'); alert('Oracle Admin Active'); }} }}
            filter();
        </script>
    </body>
    </html>
    """
    HTML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f: f.write(html)
generate()
