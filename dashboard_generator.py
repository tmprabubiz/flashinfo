import os, csv, json

CSV_INPUT = 'data/flash_info_output.csv'
HTML_OUTPUT = 'docs/index.html'

def generate():
    rows = []
    if os.path.exists(CSV_INPUT):
        with open(CSV_INPUT, 'r', encoding='utf-8-sig') as f:
            rows = [r for r in csv.DictReader(f) if r.get('title')]
    
    rows.sort(key=lambda x: x.get('date', ''), reverse=True)
    domains = sorted(list(set(r['domain'] for r in rows)))

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FLASH INFO | V23 Sovereign</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #020617; color: #f8fafc; font-family: sans-serif; }}
            .glass {{ background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }}
            .tab-active {{ border-bottom: 3px solid #38bdf8; color: #38bdf8; }}
        </style>
    </head>
    <body class="p-4 md:p-10">
        <header class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6 mb-12">
            <h1 onclick="unlockAdmin()" class="text-4xl font-black text-sky-400 cursor-pointer">FLASH INFO</h1>
            <div class="flex flex-wrap gap-2">
                <select id="domFilt" onchange="filter()" class="glass rounded-xl px-4 py-2 text-xs">
                    <option value="ALL">All Domains</option>
                    {"".join([f'<option value="{d}">{d}</option>' for d in domains])}
                </select>
                <input type="text" id="search" oninput="filter()" placeholder="Search..." class="glass rounded-xl px-4 py-2 text-xs w-40 md:w-64">
            </div>
        </header>

        <nav class="max-w-7xl mx-auto mb-10 flex gap-6 border-b border-slate-800 text-[10px] font-bold tracking-widest uppercase">
            <button onclick="tab('ALL')" id="t-ALL" class="tab-btn pb-4 tab-active">ALL</button>
            <button onclick="tab('SPARK')" id="t-SPARK" class="tab-btn pb-4 text-slate-500">SPARKS</button>
            <button onclick="tab('CONTEXT')" id="t-CONTEXT" class="tab-btn pb-4 text-slate-500">CONTEXT</button>
            <button id="adminBtn" onclick="tab('ADMIN')" class="hidden pb-4 text-red-500">ADMIN</button>
        </nav>

        <main id="grid" class="max-w-7xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"></main>

        <script>
            const data = {json.dumps(rows)};
            let curTab = 'ALL';

            function render() {{
                const grid = document.getElementById('grid');
                grid.innerHTML = '';
                
                if(curTab === 'ADMIN') {{
                    grid.innerHTML = `
                        <div class="glass p-8 rounded-3xl col-span-full">
                            <h2 class="text-xl font-bold mb-6 text-sky-400">ADMIN: Add New Source</h2>
                            <div class="flex flex-col gap-4 max-w-lg">
                                <input id="newDom" placeholder="Domain (e.g. History_Cuba)" class="glass p-3 rounded-lg text-sm">
                                <input id="newUrl" placeholder="URL (RSS or Static)" class="glass p-3 rounded-lg text-sm">
                                <button onclick="addSource()" class="bg-sky-600 p-3 rounded-lg font-bold">Check & Generate Entry</button>
                                <div id="adminOut" class="mt-4 text-xs font-mono text-slate-400"></div>
                            </div>
                        </div>`;
                    return;
                }}

                const s = document.getElementById('search').value.toLowerCase();
                const d = document.getElementById('domFilt').value;

                data.filter(i => {{
                    const mTab = curTab === 'ALL' || i.source_group === curTab;
                    const mDom = d === 'ALL' || i.domain === d;
                    const mSea = (i.title + i.summary_snippet).toLowerCase().includes(s);
                    return mTab && mDom && mSea;
                }}).slice(0, 30).forEach(i => {{
                    const c = document.createElement('div');
                    c.className = 'glass p-6 rounded-3xl flex flex-col justify-between';
                    c.innerHTML = `<div><div class="flex justify-between mb-4"><span class="text-[10px] text-sky-500 font-bold">${{i.domain}}</span><span class="text-[10px] text-slate-600">${{i.date}}</span></div><h3 class="font-bold mb-2">${{i.title}}</h3><p class="text-xs text-slate-400 leading-relaxed">${{i.summary_snippet}}</p></div><a href="${{i.url}}" target="_blank" class="mt-4 text-[10px] text-sky-400 font-bold">SOURCE &rarr;</a>`;
                    grid.appendChild(c);
                }});
            }}

            function addSource() {{
                const dom = document.getElementById('newDom').value;
                const url = document.getElementById('newUrl').value;
                const exists = data.some(i => i.url === url);
                if(exists) alert("Deduplication Alert: URL already exists in database!");
                else document.getElementById('adminOut').innerText = '"' + dom + '": "' + url + '", (Copy to sources.json)';
            }}

            function tab(t) {{ curTab = t; document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('tab-active', 'text-sky-400')); document.getElementById('t-'+(t==='ADMIN'?'ALL':t)).classList.add('tab-active', 'text-sky-400'); render(); }}
            function filter() {{ render(); }}
            let clicks = 0; function unlockAdmin() {{ clicks++; if(clicks===5) {{ document.getElementById('adminBtn').classList.remove('hidden'); alert('Admin Unlocked'); }} }}
            render();
        </script>
    </body>
    </html>
    """
    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f: f.write(html)
generate()
