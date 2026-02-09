import re

def parse_dividends():
    with open("debug_i10_stock.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Procurar tabela de dividendos
    table_match = re.search(r'<table id="table-dividends-history"(.*?)</table>', html, re.DOTALL)
    
    if table_match:
        table_html = table_match.group(1)
        print("Tabela encontrada!")
        
        # Parse rows (lidar com atributos na tag tr)
        rows = re.findall(r'<tr.*?>(.*?)</tr>', table_html, re.DOTALL)
        print(f"Número de linhas: {len(rows)}")
        
        for row in rows[:5]: # Print first 5 rows
            # Parse columns (data-title or just td content)
            cols = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)
            clean_cols = []
            for c in cols:
                # Remove spans and tags inside td
                txt = re.sub(r'<[^>]+>', '', c).strip()
                clean_cols.append(txt)
            
            if clean_cols:
                print(clean_cols)
    else:
        print("Tabela 'table-dividends-history' não encontrada.")

if __name__ == "__main__":
    parse_dividends()
