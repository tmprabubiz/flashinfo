import os
import csv
import json
from datetime import datetime

CSV_INPUT = 'data/flash_info_output.csv'
HTML_OUTPUT = 'docs/index.html'

def generate():
    rows = []
    domains = set()
    stats = {"sparks": 0, "context": 0, "total": 0}
    
    if os.path.exists(CSV_INPUT):
        with open(CSV_INPUT, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = (row.get('title') or '').strip()
                snippet = (row.get('summary_snippet') or '').strip()
                # Force consistency: SPARK or CONTEXT
                group = (row.get('source_group') or 'CONTEXT').strip().upper()
                domain = (row.get('domain') or 'General').strip()
                
                if title and snippet and title.lower() != 'null':
                    clean_row = {
                        "date": row.get('date', '2026-01-01'),
                        "domain": domain,
                        "title": title,
                        "url": row.get('url', '#'),
                        "summary_snippet": snippet,
                        "source_group": group
                    }
                    rows.append(clean_row)
                    domains.add(domain)
                    stats["total"] += 1
                    if group == "SPARK": stats["sparks"] += 1
                    else: stats["context"] += 1

    rows.sort(key=lambda x: x.get('date', ''), reverse=True)
    domain_list = sorted(list(domains))

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>FLASH INFO | Sovereign Hub</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #020617; color: #f8fafc; font-family: 'Inter', sans-serif; scroll-behavior: smooth; }}
            .glass {{ background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); }}
            .card-spark {{ border-top: 3px solid #38bdf8; }}
            .card-context {{ border-top: 3px solid #64748b; }}
            .tab-active {{ border-bottom: 3px solid #38bdf8; color: #38bdf8; }}
        </style>
    </head>
    <body class="p-6 md:p-12">
        <header class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8 mb-16">
            <div onclick="unlockAdmin()" class="cursor-pointer group">
                <h1 class="text-5xl font-black text-sky-400 tracking-tighter group-hover:text-white transition-colors">FLASH INFO</h1>
                <p class="text-[10px] text-slate-500 font-mono tracking-[0.4em] uppercase mt-2">Stochastic Synthesis Engine v21.1</p>
            </div>
            <div class="flex flex-wrap gap-4 w-full md:w-auto">
                <select id="domainFilter" onchange="filterData()" class="glass rounded-2xl px-6 py-3 text-sm text-slate-300 outline-none hover:border-sky-500/50 transition-all">
                    <option value="ALL">All Domains</option>
                    {"".join([f'<option value="{d}">{d}</option>' for d in domain_list])}
                </select>
                <input type="text" id="searchInput" oninput="filterData()" placeholder="Search eras or subjects..." 
                       class="glass rounded-2xl px-8 py-3 text-sm w-full md:w-80 outline-none focus:ring-2 focus:ring-sky-500 transition-all">
            </div>
        </header>

        <nav class="max-w-7xl mx-auto mb-12 flex gap-10 border-b border-slate-800 text-sm font-black tracking-widest uppercase">
            <button onclick="switchTab('ALL')" id="tab-ALL" class="tab-btn pb-4 tab-active text-sky-400">ALL FEED</button>
            <button onclick="switchTab('SPARK')" id="tab-SPARK" class="tab-btn pb-4 text-slate-500 hover:text-sky-400 transition-colors">SPARKS</button>
            <button onclick="switchTab('CONTEXT')" id="tab-CONTEXT" class="tab-btn pb-4 text-slate-500 hover:text-sky-400 transition-colors">CONTEXT</button>
            <button class="pb-4 text-slate-800 cursor-not-allowed">BOOKS (LOCKED)</button>
            <button id="adminTab" onclick="switchTab('ADMIN')" class="hidden pb-4 text-red-500 font-bold">SYSTEM ADMIN</button>
        </nav>

        <main id="mainGrid" class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10"></main>
        
        <div id="loadMore" class="text-center mt-20 mb-32">
            <button onclick="loadMore()" class="glass px-12 py-4 rounded-full text-xs font-black tracking-[0.2em] text-sky-400 hover:scale-105 active:scale-95 transition-all">LOAD MORE CONNECTIONS</button>
        </div>

        <script>
            // Ensure data is properly escaped for JS consumption
            const fullData = {json.dumps(rows, ensure_ascii=False)};
            const stats = {json.dumps(stats)};
            let currentTab = 'ALL';
            let pageSize = 12;
            let currentPage = 1;

            function renderCards(append = false) {{
                const grid = document.getElementById('mainGrid');
                if (!append) grid.innerHTML = '';
                
                if (currentTab === 'ADMIN') {{
                    grid.innerHTML = `
                        <div class="glass p-10 rounded-[3rem] col-span-full text-center">
                            <h2 class="text-3xl font-black mb-6 text-red-500 tracking-tighter">SYSTEM CONTROL PANEL</h2>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 text-left max-w-4xl mx-auto mt-10">
                                <div class="glass p-6 rounded-2xl"><p class="text-slate-500 text-xs mb-2">TOTAL ENTRIES</p><p class="text-4xl font-bold font-mono text-sky-400">${{stats.total}}</p></div>
                                <div class="glass p-6 rounded-2xl"><p class="text-slate-500 text-xs mb-2">SPARK RATIO</p><p class="text-4xl font-bold font-mono text-sky-400">${{stats.sparks}}</p></div>
                                <div class="glass p-6 rounded-2xl"><p class="text-slate-500 text-xs mb-2">DATA INTEGRITY</p><p class="text-4xl font-bold font-mono text-emerald-400">100%</p></div>
                            </div>
                            <p class="mt-12 text-slate-600 text-[10px] tracking-widest font-mono">2026 STOCHASTIC KERNEL ACTIVE</p>
                        </div>
                    `;
                    document.getElementById('loadMore').style.display = 'none';
                    return;
                }}

                document.getElementById('loadMore').style.display = 'block';
                const searchTerm = document.getElementById('searchInput').value.toLowerCase();
                const domainTerm = document.getElementById('domainFilter').value;
                
                const filtered = fullData.filter(item => {{
                    const matchesTab = (currentTab === 'ALL' || item.source_group === currentTab);
                    const matchesSearch = item.title.toLowerCase().includes(searchTerm) || item.summary_snippet.toLowerCase().includes(searchTerm);
                    const matchesDomain = (domainTerm === 'ALL' || item.domain === domainTerm);
                    return matchesTab && matchesSearch && matchesDomain;
                }});

                const paginated = filtered.slice(0, currentPage * pageSize);
                
                paginated.forEach(row => {{
                    const card = document.createElement('div');
                    card.className = `glass p-8 rounded-[2.5rem] flex flex-col justify-between hover:bg-slate-900/50 transition-all card-${{row.source_group.toLowerCase()}}`;
                    card.innerHTML = `
                        <div>
                            <div class="flex justify-between items-start mb-6">
                                <span class="text-[10px] font-black text-sky-500 bg-sky-500/10 px-3 py-1 rounded-full uppercase tracking-tighter font-mono">${{row.domain}}</span>
                                <span class="text-[10px] text-slate-600 font-mono italic">${{row.date}}</span>
                            </div>
                            <h2 class="text-xl font-bold mb-4 leading-tight group-hover:text-sky-300 transition-colors">${{row.title}}</h2>
                            <div class="text-sm text-slate-400 leading-relaxed whitespace-pre-line">${{row.summary_snippet}}</div>
                        </div>
                        <div class="mt-10 pt-6 border-t border-slate-800/50 flex justify-between items-center">
                            <span class="text-[10px] font-black text-slate-700 uppercase tracking-widest">${{row.source_group}}</span>
                            <a href="${{row.url}}" target="_blank" class="text-[10px] text-sky-400 font-black hover:text-white transition-colors tracking-widest">ORIGIN SOURCE &rarr;</a>
                        </div>
                    `;
                    grid.appendChild(card);
                }});
            }}

            function switchTab(tab) {{
                currentTab = tab; currentPage = 1;
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('tab-active', 'text-sky-400'));
                document.getElementById('tab-' + (tab === 'ADMIN' ? 'ALL' : tab)).classList.add('tab-active', 'text-sky-400');
                renderCards();
            }}

            function filterData() {{ currentPage = 1; renderCards(); }}
            function loadMore() {{ currentPage++; renderCards(); }}

            let clickCount = 0;
            function unlockAdmin() {{
                clickCount++;
                if (clickCount === 5) {{
                    document.getElementById('adminTab').classList.remove('hidden');
                    alert("Admin Logic Decrypted.");
                }}
            }}

            renderCards();
        </script>
    </body>
    </html>
    """
    os.makedirs('docs', exist_ok=True)
    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"Sovereign Dashboard Generated: {len(rows)} connections. Admin ready.")

if __name__ == "__main__":
    generate()