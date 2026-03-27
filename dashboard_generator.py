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
        <title>FLASH INFO | Sovereign V25</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #020617; color: #f8fafc; font-family: sans-serif; }}
            .glass {{ background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.05); }}
            .tab-active {{ border-bottom: 3px solid #38bdf8; color: #38bdf8; }}
        </style>
    </head>
    <body class="p-4 md:p-10">
        <header class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6 mb-12">
            <h1 onclick="unlockAdmin()" class="text-4xl font-black text-sky-400 cursor-pointer">FLASH INFO</h1>
            <div class="flex flex-wrap justify-center gap-2">
                <select id="domFilt" onchange="filter()" class="glass rounded-xl px-4 py-2 text-xs outline-none">
                    <option value="ALL">All Domains</option>
                    {"".join([f'<option value="{d}">{d}</option>' for d in domains])}
                </select>
                <input type="text" id="search" oninput="filter()" placeholder="Deep Search (e.g. Freud)..." class="glass rounded-xl px-6 py-2 text-xs w-64">
            </div>
        </header>

        <nav class="max-w-7xl mx-auto mb-10 flex gap-8 border-b border-slate-800 text-[10px] font-bold tracking-[0.2em] uppercase overflow-x-auto pb-1">
            <button onclick="tab('ALL')" id="t-ALL" class="tab-btn pb-4 tab-active">ALL</button>
            <button onclick="tab('SPARK')" id="t-SPARK" class="tab-btn pb-4 text-slate-500">SPARKS</button>
            <button onclick="tab('CONTEXT')" id="tab-CONTEXT" class="tab-btn pb-4 text-slate-500">CONTEXT</button>
            <button id="adminBtn" onclick="tab('ADMIN')" class="hidden pb-4 text-red-500">ADMIN</button>
        </nav>

        <main id="grid" class="max-w-7xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8"></main>

        <script>
            const fullData = {json.dumps(rows)};
            let curTab = 'ALL';

            function render(filtered) {{
                const grid = document.getElementById('grid');
                grid.innerHTML = '';
                
                if(curTab === 'ADMIN') {{
                    grid.innerHTML = `
                        <div class="glass p-8 rounded-[2.5rem] col-span-full">
                            <h2 class="text-xl font-bold mb-6 text-sky-400 uppercase tracking-widest">System Control</h2>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div class="space-y-4">
                                    <p class="text-xs text-slate-500 font-bold uppercase">Add API Preference</p>
                                    <input placeholder="New API Key" class="glass w-full p-3 rounded-xl text-xs">
                                    <input placeholder="Model Name (gemini-2.5-flash)" class="glass w-full p-3 rounded-xl text-xs">
                                    <button class="bg-sky-600 w-full p-3 rounded-xl text-xs font-bold">Update Preferences</button>
                                </div>
                                <div class="space-y-4">
                                    <p class="text-xs text-slate-500 font-bold uppercase">Add New Source</p>
                                    <input id="newDom" placeholder="Domain" class="glass w-full p-3 rounded-xl text-xs">
                                    <input id="newUrl" placeholder="URL" class="glass w-full p-3 rounded-xl text-xs">
                                    <button onclick="verifySource()" class="bg-slate-700 w-full p-3 rounded-xl text-xs font-bold">Verify & Add</button>
                                </div>
                            </div>
                        </div>`;
                    return;
                }}

                filtered.slice(0, 24).forEach(i => {{
                    const c = document.createElement('div');
                    c.className = 'glass p-8 rounded-[2rem] flex flex-col justify-between hover:border-sky-500/30 transition-all';
                    c.innerHTML = `<div><div class="flex justify-between mb-6 items-center"><span class="text-[10px] text-sky-500 font-black tracking-tighter uppercase px-2 py-1 bg-sky-500/10 rounded">${{i.domain}}</span><span class="text-[10px] text-slate-600 font-mono">${{i.date}}</span></div><h3 class="text-lg font-bold mb-4 leading-tight">${{i.title}}</h3><p class="text-xs text-slate-400 leading-relaxed">${{i.summary_snippet}}</p></div><div class="mt-8 pt-6 border-t border-slate-800 flex justify-between items-center"><span class="text-[10px] font-bold text-slate-700 uppercase">${{i.source_group}}</span><a href="${{i.url}}" target="_blank" class="text-[10px] text-sky-400 font-black">SOURCE &rarr;</a></div>`;
                    grid.appendChild(c);
                }});
            }}

            function filter() {{
                const s = document.getElementById('search').value.toLowerCase();
                const d = document.getElementById('domFilt').value;
                const filtered = fullData.filter(i => {{
                    const mTab = curTab === 'ALL' || i.source_group.toUpperCase() === curTab;
                    const mDom = d === 'ALL' || i.domain === d;
                    const mSea = (i.title + i.summary_snippet).toLowerCase().includes(s);
                    return mTab && mDom && mSea;
                }});
                render(filtered);
            }}

            function tab(t) {{ curTab = t; document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('tab-active', 'text-sky-400')); document.getElementById('t-'+(t==='ADMIN'?'ALL':t)).classList.add('tab-active', 'text-sky-400'); filter(); }}
            let clicks = 0; function unlockAdmin() {{ clicks++; if(clicks===5) {{ document.getElementById('adminBtn').classList.remove('hidden'); alert('Sovereign Admin Unlocked'); }} }}
            filter();
        </script>
    </body>
    </html>
    """
    os.makedirs('docs', exist_ok=True)
    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f: f.write(html)
generate()
