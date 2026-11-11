# =====================================================================
# NÁZOV PROJEKTU: Restaurant Management System (GastroFlow)
# Školský projekt / Obhajoba vlastného projektu (Téma č. 19)
# Framework: FastAPI + SQLite + Moderné HTML/CSS UI
# =====================================================================

from fastapi import FastAPI, HTTPException, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from contextlib import closing

app = FastAPI(
    title="GastroFlow - Systém správy reštaurácie",
    description="Kompletný databázový program reštaurácie pre školský projekt",
    version="3.6.0"
)

DATABASE = "restaurant.db"


# =====================================================================
# 1. SPRÁVA DATABÁZY A INICIALIZÁCIA TABULIEK
# =====================================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    with closing(get_db()) as db:
        # Vytvorenie tabuľky zamestnancov (Bod 1: Prihlásenie)
        db.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                pin TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

        # Vytvorenie tabuľky menu (Bod 2: Grafický zoznam jedál a nápojov)
        db.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                image_url TEXT,
                available INTEGER DEFAULT 1
            )
        """)

        # Vytvorenie tabuľky stolov (Bod 3: Zoznam stolov v reštaurácii)
        db.execute("""
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_number INTEGER UNIQUE NOT NULL,
                seats INTEGER NOT NULL,
                status TEXT DEFAULT 'voľný'
            )
        """)

        # Vytvorenie tabuľky objednávok/bločkov (Bod 4 a 5: Kasa a sumár)
        db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_number INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                item_name TEXT NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'vystavený',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Vloženie počiatočných testovacích údajov, ak je databáza prázdna
        emp_count = db.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if emp_count == 0:
            db.execute("INSERT INTO employees (username, pin, full_name, role) VALUES ('admin', '1234', 'Bc. Ján Hlavný (Manažér)', 'Admin')")
            db.execute("INSERT INTO employees (username, pin, full_name, role) VALUES ('casnik', '0000', 'Peter Čašník', 'Čašník')")

        table_count = db.execute("SELECT COUNT(*) FROM tables").fetchone()[0]
        if table_count == 0:
            for i in range(1, 9):
                db.execute("INSERT INTO tables (table_number, seats, status) VALUES (?, ?, 'voľný')", (i, 4 if i <= 6 else 8))

        menu_count = db.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0]
        if menu_count == 0:
            sample_data = [
                ("Vyprážaný syr s hranolkami", "Domáci eidam, tatárska omáčka, obloha", 8.90, "Hlavné jedlá", "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=500"),
                ("Kurací steak s ryžou", "Šťavnaté prsia, dusená ryža, bylinkový maslový výpek", 9.50, "Hlavné jedlá", "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?w=500"),
                ("Sviečková na smotane", "Hovädzie zadné, domáca knedľa, brusnice", 11.20, "Hlavné jedlá", "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=500"),
                ("Kofola originál 0.5l", "Čapovaná tradičná limonáda", 2.20, "Nápoje", "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=500"),
                ("Pivo Pilsner Urquell 0.5l", "Svetlý ležiak 12°", 2.80, "Nápoje", "https://images.unsplash.com/photo-1608270103729-0f0e8f54c03b?w=500"),
                ("Domáca palacinka", "Plnená džemom, preliata čokoládou", 4.50, "Dezerty", "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?w=500")
            ]
            for item in sample_data:
                db.execute("INSERT INTO menu_items (name, description, price, category, image_url) VALUES (?, ?, ?, ?, ?)", item)

        db.commit()


@app.on_event("startup")
def startup():
    init_database()


# =====================================================================
# 2. WEBOVÉ CESTY A AUTORIZÁCIA
# =====================================================================

@app.get("/", response_class=HTMLResponse)
def root(user: str = Cookie(None)):
    if not user:
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/dashboard", status_code=303)


# --- BOD 1: Prihlásenie zamestnancov ---
@app.get("/login", response_class=HTMLResponse)
def login_page(error: str = None):
    error_box = f'<div class="error-msg">{error}</div>' if error else ''
    return f"""
    <!DOCTYPE html>
    <html lang="sk">
    <head>
        <meta charset="UTF-8">
        <title>Prihlásenie do systému - GastroFlow</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: 'Inter', sans-serif; background: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; }}
            .login-container {{ background: #131d31; border: 1px solid #1e293b; padding: 40px; border-radius: 16px; width: 100%; max-width: 420px; box-shadow: 0 15px 35px rgba(0,0,0,0.6); }}
            h1 {{ color: #f59e0b; font-size: 26px; text-align: center; margin-bottom: 8px; }}
            p {{ color: #94a3b8; font-size: 14px; text-align: center; margin-bottom: 30px; }}
            label {{ display: block; font-size: 13px; color: #94a3b8; margin-bottom: 6px; font-weight: 500; }}
            input {{ width: 100%; padding: 12px 16px; background: #0b0f19; border: 1px solid #1e293b; border-radius: 8px; color: white; font-size: 14px; margin-bottom: 20px; outline: none; transition: border-color 0.2s; }}
            input:focus {{ border-color: #f59e0b; }}
            button {{ width: 100%; padding: 12px; background: #f59e0b; border: none; border-radius: 8px; color: #0b0f19; font-weight: 700; font-size: 15px; cursor: pointer; transition: background 0.2s; }}
            button:hover {{ background: #fbbf24; }}
            .error-msg {{ background: rgba(239,68,68,0.15); color: #ef4444; padding: 12px; border-radius: 8px; font-size: 13px; margin-bottom: 20px; text-align: center; border: 1px solid rgba(239,68,68,0.3); }}
            .credentials-hint {{ margin-top: 20px; font-size: 12px; color: #64748b; text-align: center; border-top: 1px solid #1e293b; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>GastroFlow</h1>
            <p>1. Bod zadania: Prihlásenie zamestnancov</p>
            {error_box}
            <form action="/login-action" method="post">
                <label>Používateľské meno</label>
                <input type="text" name="username" required placeholder="Napr. admin alebo casnik">
                <label>PIN kód / Heslo</label>
                <input type="password" name="pin" required placeholder="Zadajte PIN...">
                <button type="submit">Prihlásiť sa do systému</button>
            </form>
            <div class="credentials-hint">
                <b>Testovacie účty:</b><br>
                Manažér: <code>admin</code> / PIN: <code>1234</code><br>
                Čašník: <code>casnik</code> / PIN: <code>0000</code>
            </div>
        </div>
    </body>
    </html>
    """


@app.post("/login-action")
async def login_action(request: Request):
    form = await request.form()
    username = str(form.get("username", "")).strip()
    pin = str(form.get("pin", "")).strip()

    with closing(get_db()) as db:
        employee = db.execute("SELECT * FROM employees WHERE username = ? AND pin = ?", (username, pin)).fetchone()
        if not employee:
            return RedirectResponse("/login?error=Nesprávne prihlasovacie meno alebo PIN kód!", status_code=303)

    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(key="user", value=employee['full_name'])
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("user")
    return response


# =====================================================================
# HLAVNÝ ADMIN DASHBOARD (Zahŕňa body 2, 3, 4, 5)
# =====================================================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(user: str = Cookie(None)):
    if not user:
        return RedirectResponse("/login", status_code=303)

    with closing(get_db()) as db:
        menu_items = db.execute("SELECT * FROM menu_items ORDER BY category, name").fetchall()
        tables = db.execute("SELECT * FROM tables ORDER BY table_number").fetchall()
        orders = db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        
        # Výpočet celkových tržieb za deň (Bod 5)
        daily_revenue = db.execute("SELECT COALESCE(SUM(total_price), 0) FROM orders").fetchone()[0]
        total_orders_count = len(orders)

    # --- BOD 2: Grafický zoznam nápojov a jedál s cenou ---
    menu_cards_html = ""
    for item in menu_items:
        badge = '<span class="badge badge-success">Dostupné</span>' if item['available'] else '<span class="badge badge-danger">Vypredané</span>'
        img = item['image_url'] or "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500"
        menu_cards_html += f"""
        <div class="menu-card">
            <div class="menu-img" style="background-image: url('{img}')"></div>
            <div class="menu-body">
                <span class="category-tag">{item['category']}</span>
                <h3>{item['name']}</h3>
                <p>{item['description'] or ''}</p>
                <div class="menu-footer">
                    <span class="price-tag">{item['price']:.2f} €</span>
                    {badge}
                </div>
            </div>
        </div>
        """

    # --- BOD 3: Zoznam stolov v reštaurácii ---
    tables_html = ""
    for t in tables:
        status_style = "table-free" if t['status'] == 'voľný' else "table-busy"
        tables_html += f"""
        <div class="table-box {status_style}">
            <div class="t-top">
                <span class="t-num">Stôl #{t['table_number']}</span>
                <span class="badge {'badge-success' if t['status']=='voľný' else 'badge-danger'}">{t['status'].upper()}</span>
            </div>
            <div class="t-info">Kapacita: <b>{t['seats']} osoby</b></div>
            <form action="/toggle-table/{t['id']}" method="post" style="margin-top: 12px;">
                <button type="submit" class="btn-secondary-sm">Zmeniť stav stola</button>
            </form>
        </div>
        """

    # --- BOD 4: Jednoduchá kasa na vytváranie bločkov ---
    table_dropdown_options = "".join([f"<option value='{t['table_number']}'>Stôl #{t['table_number']} ({t['seats']} osôb)</option>" for t in tables])
    menu_dropdown_options = "".join([f"<option value='{item['id']}'>{item['name']} – {item['price']:.2f} €</option>" for item in menu_items if item['available']])

    # --- BOD 5: Sumár objednávok a bločkov za celý deň ---
    orders_table_rows = ""
    if not orders:
        orders_table_rows = '<tr><td colspan="7" class="empty-text">Zatiaľ neboli vystavené žiadne bločky za dnešný deň.</td></tr>'
    else:
        for o in orders:
            orders_table_rows += f"""
            <tr>
                <td><b>#{o['id']}</b></td>
                <td>Stôl #{o['table_number']}</td>
                <td>{o['customer_name']}</td>
                <td>{o['item_name']}</td>
                <td class="price-col">{o['total_price']:.2f} €</td>
                <td><span class="badge badge-info">{o['status']}</span></td>
                <td class="date-col">{o['created_at']}</td>
            </tr>
            """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="sk">
    <head>
        <meta charset="UTF-8">
        <title>GastroFlow - Hlavný Panel Reštaurácie</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-main: #0b0f19;
                --bg-card: #131d31;
                --border-color: #1e293b;
                --accent: #f59e0b;
                --accent-hover: #fbbf24;
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
                --danger: #ef4444;
                --success: #10b981;
                --info: #3b82f6;
            }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: 'Inter', sans-serif; background-color: var(--bg-main); color: var(--text-main); min-height: 100vh; line-height: 1.5; }}
            
            header {{ background: var(--bg-card); border-bottom: 1px solid var(--border-color); padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
            .brand h1 {{ color: var(--accent); font-size: 22px; font-weight: 700; }}
            .brand p {{ color: var(--text-muted); font-size: 13px; }}
            .user-box {{ display: flex; align-items: center; gap: 20px; font-size: 14px; }}
            .logout-btn {{ background: rgba(239,68,68,0.15); color: var(--danger); border: 1px solid rgba(239,68,68,0.3); padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: 600; transition: all 0.2s; }}
            .logout-btn:hover {{ background: var(--danger); color: white; }}

            main {{ max-width: 1400px; margin: 0 auto; padding: 35px 20px; display: flex; flex-direction: column; gap: 30px; }}

            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }}
            .stat-card {{ background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px; padding: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-left: 4px solid var(--accent); }}
            .stat-card h3 {{ color: var(--text-muted); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
            .stat-card .val {{ font-size: 32px; font-weight: 700; color: var(--text-main); margin-top: 8px; }}

            section {{ background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }}
            section h2 {{ font-size: 18px; font-weight: 600; color: var(--accent); margin-bottom: 20px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; }}

            .tables-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; }}
            .table-box {{ background: #0f172a; border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; transition: transform 0.2s; }}
            .table-free {{ border-left: 4px solid var(--success); }}
            .table-busy {{ border-left: 4px solid var(--danger); }}
            .t-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
            .t-num {{ font-weight: 700; font-size: 16px; }}
            .t-info {{ font-size: 13px; color: var(--text-muted); }}

            .kasa-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr auto; gap: 15px; align-items: center; }}
            input, select {{ width: 100%; background: #0b0f19; border: 1px solid var(--border-color); border-radius: 8px; padding: 12px 16px; color: white; font-size: 14px; outline: none; }}
            input:focus, select:focus {{ border-color: var(--accent); }}
            button.btn-primary {{ background: var(--accent); color: #0b0f19; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; white-space: nowrap; }}
            button.btn-primary:hover {{ background: var(--accent-hover); }}

            .menu-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
            .menu-card {{ background: #0f172a; border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; }}
            .menu-img {{ height: 140px; background-size: cover; background-position: center; }}
            .menu-body {{ padding: 18px; display: flex; flex-direction: column; flex-grow: 1; }}
            .category-tag {{ font-size: 11px; background: rgba(59,130,246,0.15); color: var(--info); padding: 3px 10px; border-radius: 20px; width: fit-content; font-weight: 600; margin-bottom: 10px; }}
            .menu-body h3 {{ font-size: 16px; margin-bottom: 6px; font-weight: 600; }}
            .menu-body p {{ font-size: 13px; color: var(--text-muted); flex-grow: 1; margin-bottom: 15px; }}
            .menu-footer {{ display: flex; justify-content: space-between; align-items: center; }}
            .price-tag {{ font-weight: 700; color: var(--accent); font-size: 18px; }}

            .table-responsive {{ overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
            th, td {{ padding: 14px 16px; border-bottom: 1px solid var(--border-color); }}
            th {{ color: var(--text-muted); font-weight: 600; background: rgba(255,255,255,0.01); }}
            tr:hover td {{ background: rgba(255,255,255,0.015); }}
            .price-col {{ font-weight: 700; color: var(--accent); }}
            .date-col {{ color: var(--text-muted); font-size: 13px; }}
            .empty-text {{ text-align: center; color: var(--text-muted); padding: 30px !important; font-style: italic; }}

            .badge {{ padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
            .badge-success {{ background: rgba(16,185,129,0.15); color: var(--success); }}
            .badge-danger {{ background: rgba(239,68,68,0.15); color: var(--danger); }}
            .badge-info {{ background: rgba(59,130,246,0.15); color: var(--info); }}

            .btn-secondary-sm {{ background: rgba(255,255,255,0.05); color: white; border: 1px solid var(--border-color); padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500; width: 100%; }}
            .btn-secondary-sm:hover {{ background: rgba(255,255,255,0.1); border-color: var(--text-muted); }}

            @media(max-width: 900px) {{
                .kasa-grid {{ grid-template-columns: 1fr; }}
                header {{ flex-direction: column; align-items: flex-start; gap: 15px; }}
            }}
        </style>
    </head>
    <body>
        <header>
            <div class="brand">
                <h1>GastroFlow – Reštauračný systém</h1>
                <p>Študijný odbor: Informačno-mediálne technológie | Obhajoba projektu</p>
            </div>
            <div class="user-box">
                <span>Prihlásený: <b>{user}</b></span>
                <a href="/logout" class="logout-btn">Odhlásiť sa</a>
            </div>
        </header>

        <main>
            <!-- 5. Bod: Štatistiky tržieb a prehľad dňa -->
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Celkové tržby za dnešný deň</h3>
                    <div class="val">{daily_revenue:.2f} €</div>
                </div>
                <div class="stat-card">
                    <h3>Počet vystavených bločkov</h3>
                    <div class="val">{total_orders_count}</div>
                </div>
                <div class="stat-card">
                    <h3>Položiek v ponuke menu</h3>
                    <div class="val">{len(menu_items)}</div>
                </div>
            </div>

            <!-- 3. Bod zadania: Zoznam stolov v reštaurácii -->
            <section>
                <h2>🪑 3. Bod zadania: Zoznam stolov v reštaurácii</h2>
                <div class="tables-grid">
                    {tables_html}
                </div>
            </section>

            <!-- 4. Bod zadania: Jednoduchá kasa na vytváranie bločkov -->
            <section>
                <h2>🧾 4. Bod zadania: Jednoduchá kasa (Vystavenie nového bločku)</h2>
                <form action="/create-bill" method="post" class="kasa-grid">
                    <select name="table_number" required>
                        <option value="">-- Vyberte stôl --</option>
                        {table_dropdown_options}
                    </select>
                    <input type="text" name="customer_name" placeholder="Meno zákazníka / hosta" required>
                    <select name="menu_item_id" required>
                        <option value="">-- Vyberte jedlo alebo nápoj --</option>
                        {menu_dropdown_options}
                    </select>
                    <button type="submit" class="btn-primary">Vystaviť bloček</button>
                </form>
            </section>

            <!-- 2. Bod zadania: Grafický zoznam nápojov a jedál s cenou -->
            <section>
                <h2>🍔 2. Bod zadania: Grafický zoznam nápojov a jedál s cenou</h2>
                <div class="menu-grid">
                    {menu_cards_html}
                </div>
            </section>

            <!-- 5. Bod zadania: Sumár objednávok a bločkov za celý deň -->
            <section>
                <h2>📊 5. Bod zadania: Sumár objednávok a bločkov za celý deň</h2>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>ID Bločku</th>
                                <th>Stôl</th>
                                <th>Zákazník</th>
                                <th>Položka</th>
                                <th>Celková suma</th>
                                <th>Stav</th>
                                <th>Čas vytvorenia</th>
                            </tr>
                        </thead>
                        <tbody>
                            {orders_table_rows}
                        </tbody>
                    </table>
                </div>
            </section>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(html_content)


# =====================================================================
# 3. SPRACOVANIE FORMULÁROV A AKCIÍ (BACKEND LOGIKA)
# =====================================================================

@app.post("/toggle-table/{table_id}")
def toggle_table_status(table_id: int):
    with closing(get_db()) as db:
        table = db.execute("SELECT status FROM tables WHERE id = ?", (table_id,)).fetchone()
        if table:
            new_status = 'obsadený' if table['status'] == 'voľný' else 'voľný'
            db.execute("UPDATE tables SET status = ? WHERE id = ?", (new_status, table_id))
            db.commit()
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/create-bill")
async def create_bill(request: Request):
    form = await request.form()
    try:
        table_number = int(form.get("table_number"))
        menu_item_id = int(form.get("menu_item_id"))
        customer_name = str(form.get("customer_name", "Host")).strip()
    except (TypeError, ValueError):
        raise HTTPException(400, "Neplatné vstupné údaje formulára")

    with closing(get_db()) as db:
        menu_item = db.execute("SELECT * FROM menu_items WHERE id = ?", (menu_item_id,)).fetchone()
        if not menu_item:
            raise HTTPException(404, "Položka v menu sa nenašla")

        item_name = menu_item['name']
        price = menu_item['price']

        db.execute("""
            INSERT INTO orders (table_number, customer_name, item_name, total_price, status)
            VALUES (?, ?, ?, ?, 'vystavený')
        """, (table_number, customer_name, item_name, price))

        db.execute("UPDATE tables SET status = 'obsadený' WHERE table_number = ?", (table_number,))
        db.commit()

    return RedirectResponse("/dashboard", status_code=303)