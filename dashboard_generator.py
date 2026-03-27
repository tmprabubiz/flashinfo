import os
import csv
import json

CSV_INPUT = 'data/flash_info_output.csv'
HTML_OUTPUT = 'docs/index.html'

def generate():
    rows = []
    domains = set()
    
    if os.path.exists(CSV_INPUT):
        with open(CSV_INPUT, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # SCRUBBING: Remove Nulls and junk data
                title = (row.get('title') or '').strip()
                snippet = (row.get('summary_snippet') or '').strip()
                domain = (row.get('domain') or 'General').strip()
                
                if title and snippet and title.lower() != 'null' and len(snippet) > 10:
                    row['title'] = title
                    row['summary_snippet'] = snippet
                    row['domain'] = domain
                    rows.append(row)
                    domains.add(domain)

    # Sort Newest First
    rows.sort(key=lambda x: x.get('date', ''), reverse=True)
    domain_list = sorted(list(domains))

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><title>FLASH INFO | Sovereign Hub</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #020617; color: #f8fafc; font-family: 'Inter', sans-serif; }}
            .glass {{ background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.05); }}
            .card-spark {{ border-top: 3px solid #38bdf8; box-shadow: 0 0 20px rgba(56, 189, 248, 0.1); }}
            .tab-active {{ border-bottom: 2px solid #38bdf8; color: #38bdf8; }}
            .hidden-admin {{ display: none; }}
        </style>
    </head>
    <body class="p-6">
        <header class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6 mb-12">
            <div onclick="checkAdmin()" class="cursor-pointer">
                <h1 class="text-4xl font-black text-sky-400 tracking-tighter">FLASH INFO</h1>
                <p class="text-[10px] text-slate-500 font-mono tracking-widest uppercase">Stochastic Synthesis Engine v21</p>
            </div>
            
            <div class="flex flex-wrap gap-4 w-full md:w-auto">
                <select id="domainFilter" onchange="filterData()" class="glass rounded-xl px-4 py-2 text-sm text-slate-300 outline-none">
                    <option value="ALL">All Domains</option>
                    {"".join([f'<option value="{d}">{d}</option>' for d in domain_list])}
                </select>
                <input type="text" id="searchInput" oninput="filterData()" placeholder="Search eras or subjects..." 
                       class="glass rounded-xl px-6 py-2 text-sm w-full md:w-64 outline-none focus:ring-2 focus:ring-sky-500">
            </div>
        </header>

        <nav class="max-w-7xl mx-auto mb-8 flex gap-8 border-b border-slate-800 text-sm font-bold tracking-tight">
            <button onclick="switchTab('ALL')" id="tab-ALL" class="tab-btn pb-3 tab-active">ALL FEED</button>
            <button onclick="switchTab('SPARK')" id="tab-SPARK" class="tab-btn pb-3 text-slate-500 hover:text-sky-400">SPARKS</button>
            <button onclick="switchTab('CONTEXT')" id="tab-CONTEXT" class="tab-btn pb-3 text-slate-500 hover:text-sky-400">CONTEXT</button>
            <button onclick="switchTab('BOOKS')" id="tab-BOOKS" class="tab-btn pb-3 text-slate-700">BOOKS</button>
            <button id="adminLink" onclick="switchTab('ADMIN')" class="hidden-admin tab-btn pb-3 text-red-500">ADMIN</button>
        </nav>

        <main id="mainGrid" class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"></main>
        
        <div id="loadMore" class="text-center mt-12 mb-20">
            <button onclick="loadMore()" class="glass px-10 py-3 rounded-full text-xs font-bold tracking-widest text-sky-400 hover:bg-sky-500/10 transition-all">LOAD MORE CONNECTIONS</button>
        </div>

        <script>
            const fullData = {json.dumps(rows)};
            let currentTab = 'ALL';
            let pageSize = 15;
            let currentPage = 1;

            function renderCards(append = false) {{
                const grid = document.getElementById('mainGrid');
                if (!append) grid.innerHTML = '';
                
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
                    card.className = `glass p-8 rounded-3xl flex flex-col justify-between hover:bg-slate-900/50 transition-all card-${{row.source_group.toLowerCase()}}`;
                    card.innerHTML = `
                        <div>
                            <div class="flex justify-between mb-6">
                                <span class="text-[10px] font-bold text-sky-500 bg-sky-500/10 px-2 py-1 rounded uppercase tracking-tighter font-mono">${{row.domain}}</span>
                                <span class="text-[10px] text-slate-600 font-mono">${{row.date}}</span>
                            </div>
                            <h2 class="text-lg font-bold mb-4 leading-tight">${{row.title}}</h2>
                            <p class="text-sm text-slate-400 leading-relaxed">${{row.summary_snippet.replace(/\\n/g, '<br>')}}</p>
                        </div>
                        <div class="mt-8 pt-6 border-t border-slate-800 flex justify-between items-center">
                            <span class="text-[10px] font-bold text-slate-700 uppercase tracking-widest">${{row.source_group}}</span>
                            <a href="${{row.url}}" target="_blank" class="text-[10px] text-sky-400 font-black hover:text-white transition-colors">ORIGIN &rarr;</a>
                        </div>
                    `;
                    grid.appendChild(card);
                }});
            }}

            function switchTab(tab) {{
                currentTab = tab;
                currentPage = 1;
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('tab-active', 'text-sky-400'));
                document.getElementById('tab-' + tab).classList.add('tab-active', 'text-sky-400');
                renderCards();
            }}

            function filterData() {{ currentPage = 1; renderCards(); }}
            function loadMore() {{ currentPage++; renderCards(); }}

            let clickCount = 0;
            function checkAdmin() {{
                clickCount++;
                if (clickCount === 5) {{
                    document.getElementById('adminLink').style.display = 'block';
                    alert("Admin Access Unlocked");
                }}
            }}

            renderCards();
        </script>
    </body>
    </html>
    """
    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"Sovereign Dashboard Generated: {len(rows)} connections.")

if __name__ == "__main__":
    generate()