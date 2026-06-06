"""
UAE Cheque Printer Pro — Free Desktop Application
Supports all major UAE banks | PDC Management | PDF Print
By ChequerPrinterUAE.com
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import sys
import json
import subprocess
import platform
from datetime import datetime

# ─── Amount to Words ──────────────────────────────────────────────────────────

ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
        'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen',
        'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty',
        'Sixty', 'Seventy', 'Eighty', 'Ninety']

def _say(n):
    n = int(n)
    if n == 0: return ''
    if n < 20: return ONES[n]
    if n < 100:
        return TENS[n // 10] + (' ' + ONES[n % 10] if n % 10 else '')
    if n < 1000:
        r = _say(n % 100)
        return ONES[n // 100] + ' Hundred' + (' and ' + r if r else '')
    if n < 1000000:
        r = _say(n % 1000)
        return _say(n // 1000) + ' Thousand' + (' ' + r if r else '')
    r = _say(n % 1000000)
    return _say(n // 1000000) + ' Million' + (' ' + r if r else '')

def amount_to_words(amount):
    try:
        amount = float(str(amount).replace(',', ''))
    except Exception:
        return ''
    dirhams = int(amount)
    fils = round((amount - dirhams) * 100)
    result = ('UAE Dirhams ' + _say(dirhams)) if dirhams else 'UAE Dirhams Zero'
    if fils:
        result += ' and ' + _say(fils) + ' Fils'
    return result + ' Only'

# ─── UAE Banks ────────────────────────────────────────────────────────────────

UAE_BANKS = [
    {'id': 'enbd',    'name': 'Emirates NBD',                       'short': 'ENBD',    'color': '#1a1a2e', 'fg': 'white'},
    {'id': 'adcb',    'name': 'Abu Dhabi Commercial Bank (ADCB)',    'short': 'ADCB',    'color': '#c0392b', 'fg': 'white'},
    {'id': 'fab',     'name': 'First Abu Dhabi Bank (FAB)',          'short': 'FAB',     'color': '#006400', 'fg': 'white'},
    {'id': 'mashreq', 'name': 'Mashreq Bank',                       'short': 'Mashreq', 'color': '#8b0000', 'fg': 'white'},
    {'id': 'dib',     'name': 'Dubai Islamic Bank',                  'short': 'DIB',     'color': '#2e7d32', 'fg': 'white'},
    {'id': 'rakbank', 'name': 'RAK Bank',                            'short': 'RAK',     'color': '#1b3a6b', 'fg': 'white'},
    {'id': 'cbd',     'name': 'Commercial Bank of Dubai (CBD)',      'short': 'CBD',     'color': '#003087', 'fg': 'white'},
    {'id': 'hsbc',    'name': 'HSBC UAE',                            'short': 'HSBC',    'color': '#db0011', 'fg': 'white'},
    {'id': 'sc',      'name': 'Standard Chartered UAE',              'short': 'SCB',     'color': '#0070ac', 'fg': 'white'},
    {'id': 'adib',    'name': 'Abu Dhabi Islamic Bank (ADIB)',       'short': 'ADIB',    'color': '#1a6635', 'fg': 'white'},
    {'id': 'cbi',     'name': 'Commercial Bank International (CBI)', 'short': 'CBI',     'color': '#0047ab', 'fg': 'white'},
    {'id': 'uab',     'name': 'United Arab Bank (UAB)',              'short': 'UAB',     'color': '#b22222', 'fg': 'white'},
    {'id': 'nbd',     'name': 'National Bank of Dubai',              'short': 'NBD',     'color': '#0d47a1', 'fg': 'white'},
    {'id': 'other',   'name': 'Other Bank',                          'short': 'BANK',    'color': '#455a64', 'fg': 'white'},
]

def bank_by_id(bid):
    for b in UAE_BANKS:
        if b['id'] == bid:
            return b
    return UAE_BANKS[-1]

BANK_NAMES = [b['name'] for b in UAE_BANKS]

# ─── Database ─────────────────────────────────────────────────────────────────

def get_db_path():
    if platform.system() == 'Windows':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    else:
        base = os.path.expanduser('~')
    folder = os.path.join(base, 'UAEChequePrinter')
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, 'cheques.db')

def init_db():
    db = sqlite3.connect(get_db_path())
    db.execute('''CREATE TABLE IF NOT EXISTS cheques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bank_id TEXT, cheque_number TEXT,
        account_name TEXT, account_number TEXT,
        date TEXT, payee TEXT,
        amount REAL, amount_words TEXT,
        memo TEXT, status TEXT DEFAULT "pending",
        is_pdc INTEGER DEFAULT 0,
        pdc_present_date TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    db.commit()
    db.close()

def save_cheque(data):
    db = sqlite3.connect(get_db_path())
    cur = db.execute('''INSERT INTO cheques
        (bank_id, cheque_number, account_name, account_number, date, payee,
         amount, amount_words, memo, status, is_pdc, pdc_present_date, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (data['bank_id'], data['cheque_number'], data['account_name'],
         data['account_number'], data['date'], data['payee'],
         data['amount'], data['amount_words'], data['memo'],
         data['status'], data['is_pdc'], data['pdc_present_date'], data['notes']))
    db.commit()
    cid = cur.lastrowid
    db.close()
    return cid

def get_all_cheques(status_filter=None):
    db = sqlite3.connect(get_db_path())
    db.row_factory = sqlite3.Row
    if status_filter and status_filter != 'All':
        rows = db.execute("SELECT * FROM cheques WHERE status=? ORDER BY date DESC", (status_filter.lower(),)).fetchall()
    else:
        rows = db.execute("SELECT * FROM cheques ORDER BY date DESC").fetchall()
    db.close()
    return [dict(r) for r in rows]

def update_status(cid, status):
    db = sqlite3.connect(get_db_path())
    db.execute("UPDATE cheques SET status=? WHERE id=?", (status, cid))
    db.commit()
    db.close()

def delete_cheque_by_id(cid):
    db = sqlite3.connect(get_db_path())
    db.execute("DELETE FROM cheques WHERE id=?", (cid,))
    db.commit()
    db.close()

def get_stats():
    db = sqlite3.connect(get_db_path())
    row = db.execute('''SELECT
        COUNT(*) total,
        SUM(CASE WHEN status="pending" THEN 1 ELSE 0 END) pending,
        SUM(CASE WHEN status="cleared" THEN 1 ELSE 0 END) cleared,
        SUM(CASE WHEN status="bounced" THEN 1 ELSE 0 END) bounced,
        SUM(CASE WHEN is_pdc=1 AND status="pending" THEN 1 ELSE 0 END) pdc_pending,
        SUM(CASE WHEN status="pending" THEN amount ELSE 0 END) pending_amount
        FROM cheques''').fetchone()
    db.close()
    return dict(zip(['total','pending','cleared','bounced','pdc_pending','pending_amount'], row))

# ─── PDF Generator ────────────────────────────────────────────────────────────

def generate_cheque_pdf(data, output_path):
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white, black, lightgrey
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    bank = bank_by_id(data.get('bank_id', 'other'))

    # UAE standard cheque: 210mm wide x 85mm tall
    W, H = 210 * mm, 85 * mm

    c = rl_canvas.Canvas(output_path, pagesize=(W, H))

    # Bank header stripe
    bank_color = HexColor(bank['color'])
    c.setFillColor(bank_color)
    c.rect(0, H - 18*mm, W, 18*mm, fill=1, stroke=0)

    # Bank name
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(6*mm, H - 12*mm, bank['name'].upper())
    c.setFont('Helvetica', 7)
    c.drawRightString(W - 6*mm, H - 12*mm, 'UNITED ARAB EMIRATES')

    # Cheque body background
    c.setFillColor(HexColor('#FEFCE8'))
    c.rect(0, 0, W, H - 18*mm, fill=1, stroke=0)

    # Border
    c.setStrokeColor(HexColor('#D6D3C4'))
    c.setLineWidth(0.5)
    c.rect(0, 0, W, H, fill=0, stroke=1)

    # Helper: label + underline field
    def field(label, value, x, y, width, font_size=9):
        c.setFillColor(HexColor('#888888'))
        c.setFont('Helvetica', 6)
        c.drawString(x, y + 3*mm, label)
        c.setFillColor(black)
        c.setFont('Courier', font_size)
        c.drawString(x, y, value or '')
        c.setStrokeColor(HexColor('#999999'))
        c.setLineWidth(0.4)
        c.line(x, y - 0.5*mm, x + width, y - 0.5*mm)

    # Date (top right)
    date_str = data.get('date', '')
    if date_str and '-' in date_str:
        parts = date_str.split('-')
        date_disp = f"{parts[2]}/{parts[1]}/{parts[0]}"
    else:
        date_disp = date_str
    field('Date', date_disp, W - 50*mm, H - 26*mm, 44*mm)

    # Account holder (top left)
    if data.get('account_name'):
        field('A/C Name', data['account_name'], 6*mm, H - 26*mm, 90*mm)

    # Pay to
    field('Pay to the Order of', data.get('payee', ''), 6*mm, H - 38*mm, 145*mm, font_size=10)

    # Amount box (right)
    c.setStrokeColor(HexColor('#666666'))
    c.setLineWidth(1)
    c.rect(W - 50*mm, H - 53*mm, 44*mm, 14*mm, fill=0, stroke=1)
    c.setFillColor(HexColor('#888888'))
    c.setFont('Helvetica', 6)
    c.drawCentredString(W - 28*mm, H - 42*mm, 'AED')
    c.setFillColor(black)
    c.setFont('Courier-Bold', 11)
    amount_str = f"{float(data.get('amount', 0)):,.2f}"
    c.drawCentredString(W - 28*mm, H - 50*mm, amount_str)

    # Amount in words (multi-line)
    c.setFillColor(HexColor('#888888'))
    c.setFont('Helvetica', 6)
    c.drawString(6*mm, H - 42*mm, 'Amount in Words')
    words = data.get('amount_words', '')
    c.setFillColor(black)
    c.setFont('Courier', 7.5)
    # Wrap at ~100 chars
    if len(words) > 70:
        mid = words[:70].rfind(' ')
        line1, line2 = words[:mid], words[mid+1:]
        c.drawString(6*mm, H - 47*mm, line1)
        c.setStrokeColor(HexColor('#999999'))
        c.setLineWidth(0.4)
        c.line(6*mm, H - 47.5*mm, W - 55*mm, H - 47.5*mm)
        c.drawString(6*mm, H - 52*mm, line2)
        c.line(6*mm, H - 52.5*mm, W - 55*mm, H - 52.5*mm)
    else:
        c.drawString(6*mm, H - 48*mm, words)
        c.setStrokeColor(HexColor('#999999'))
        c.setLineWidth(0.4)
        c.line(6*mm, H - 48.5*mm, W - 55*mm, H - 48.5*mm)

    # Memo
    field('For / Memo', data.get('memo', ''), 6*mm, H - 63*mm, 80*mm, font_size=8)

    # Account number
    if data.get('account_number'):
        field('A/C No.', data['account_number'], 6*mm, H - 73*mm, 60*mm)

    # Signature line
    c.setStrokeColor(HexColor('#888888'))
    c.setLineWidth(0.5)
    c.line(W - 55*mm, H - 70*mm, W - 6*mm, H - 70*mm)
    c.setFillColor(HexColor('#888888'))
    c.setFont('Helvetica', 6)
    c.drawCentredString(W - 30*mm, H - 73*mm, 'Authorised Signature')

    # MICR line
    cheque_num = data.get('cheque_number', '000000').ljust(6, '0')[:6]
    ac_num = (data.get('account_number', '') or '0000000000').ljust(10, '0')[:10]
    micr = f"⑆ {cheque_num} ⑆ {ac_num} ⑆"
    c.setFillColor(HexColor('#AAAAAA'))
    c.setFont('Courier', 8)
    c.drawCentredString(W / 2, 4*mm, micr)

    c.save()

# ─── Main Application ─────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("UAE Cheque Printer Pro  |  Free by ChequerPrinterUAE.com")
        self.geometry("1100x680")
        self.minsize(900, 600)
        init_db()
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──────────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_propagate(False)

        logo = ctk.CTkLabel(self.sidebar, text="🖨️ UAE Cheque\nPrinter Pro",
                            font=ctk.CTkFont(size=14, weight='bold'))
        logo.pack(pady=(24, 4), padx=16)
        ctk.CTkLabel(self.sidebar, text="Free by ChequerPrinterUAE.com",
                     font=ctk.CTkFont(size=9), text_color='gray').pack(pady=(0, 20), padx=16)

        self.nav_buttons = {}
        nav_items = [
            ('🖨️  Print Cheque', 'print'),
            ('📋  PDC Manager', 'pdc'),
            ('⚙️  Settings', 'settings'),
        ]
        for label, key in nav_items:
            btn = ctk.CTkButton(self.sidebar, text=label, anchor='w',
                                command=lambda k=key: self.show_tab(k),
                                fg_color='transparent', hover_color='#2a3a4a',
                                font=ctk.CTkFont(size=13))
            btn.pack(fill='x', padx=8, pady=2)
            self.nav_buttons[key] = btn

        # Stats at bottom of sidebar
        self.sidebar_stats = ctk.CTkLabel(self.sidebar, text='', font=ctk.CTkFont(size=10),
                                          text_color='gray', justify='left')
        self.sidebar_stats.pack(side='bottom', pady=16, padx=16)
        self._refresh_sidebar_stats()

        # ── Content area ─────────────────────────────────────────────────────
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color='transparent')
        self.content.grid(row=0, column=1, sticky='nsew', padx=0)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.tabs = {}
        self.tabs['print'] = PrintTab(self.content, self)
        self.tabs['pdc'] = PDCTab(self.content, self)
        self.tabs['settings'] = SettingsTab(self.content, self)

        self.show_tab('print')

    def show_tab(self, key):
        for k, frame in self.tabs.items():
            frame.grid_remove()
        self.tabs[key].grid(row=0, column=0, sticky='nsew')
        if key == 'pdc':
            self.tabs['pdc'].refresh()
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color='#1a6baf' if k == key else 'transparent')

    def _refresh_sidebar_stats(self):
        try:
            s = get_stats()
            txt = (f"Total:    {s['total'] or 0}\n"
                   f"Pending:  {s['pending'] or 0}\n"
                   f"Cleared:  {s['cleared'] or 0}\n"
                   f"Bounced:  {s['bounced'] or 0}\n"
                   f"PDC due:  {s['pdc_pending'] or 0}\n"
                   f"AED out:  {(s['pending_amount'] or 0):,.0f}")
            self.sidebar_stats.configure(text=txt)
        except Exception:
            pass

# ─── Print Tab ────────────────────────────────────────────────────────────────

class PrintTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color='transparent')
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color='transparent')
        hdr.grid(row=0, column=0, columnspan=2, sticky='ew', padx=20, pady=(20, 0))
        ctk.CTkLabel(hdr, text='Print Cheque', font=ctk.CTkFont(size=22, weight='bold')).pack(side='left')
        ctk.CTkLabel(hdr, text='Fill details and generate PDF', text_color='gray',
                     font=ctk.CTkFont(size=12)).pack(side='left', padx=(12, 0))

        # Left: form
        form_scroll = ctk.CTkScrollableFrame(self, label_text='')
        form_scroll.grid(row=1, column=0, sticky='nsew', padx=(20, 10), pady=16)
        form_scroll.grid_columnconfigure(0, weight=1)
        self._build_form(form_scroll)

        # Right: preview
        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=1, column=1, sticky='nsew', padx=(10, 20), pady=16)
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(1, weight=1)
        self._build_preview(preview_frame)

    def _build_form(self, parent):
        self.vars = {}

        def row(label, key, widget_type='entry', **kwargs):
            ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11),
                         anchor='w').pack(fill='x', padx=4, pady=(8, 1))
            if widget_type == 'entry':
                v = ctk.StringVar()
                e = ctk.CTkEntry(parent, textvariable=v, **kwargs)
                e.pack(fill='x', padx=4)
                self.vars[key] = v
                return e
            elif widget_type == 'combo':
                v = ctk.StringVar()
                e = ctk.CTkComboBox(parent, variable=v, **kwargs)
                e.pack(fill='x', padx=4)
                self.vars[key] = v
                return e
            elif widget_type == 'check':
                v = ctk.BooleanVar()
                e = ctk.CTkCheckBox(parent, text=label, variable=v, **kwargs)
                e.pack(fill='x', padx=4)
                self.vars[key] = v
                return e
            elif widget_type == 'text':
                v = ctk.StringVar()
                e = ctk.CTkTextbox(parent, height=55, **kwargs)
                e.pack(fill='x', padx=4)
                self.vars[key] = e
                return e

        # Bank
        row('Bank *', 'bank_id', 'combo',
            values=BANK_NAMES, command=self._on_change)
        self.vars['bank_id'].set(BANK_NAMES[0])

        # Cheque number + date (side by side)
        r2 = ctk.CTkFrame(parent, fg_color='transparent')
        r2.pack(fill='x', padx=4, pady=(8, 0))
        r2.grid_columnconfigure(0, weight=1)
        r2.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(r2, text='Cheque Number', font=ctk.CTkFont(size=11), anchor='w').grid(row=0, column=0, sticky='ew', padx=(0, 4))
        ctk.CTkLabel(r2, text='Date *', font=ctk.CTkFont(size=11), anchor='w').grid(row=0, column=1, sticky='ew', padx=(4, 0))
        v1 = ctk.StringVar()
        ctk.CTkEntry(r2, textvariable=v1).grid(row=1, column=0, sticky='ew', padx=(0, 4))
        self.vars['cheque_number'] = v1
        v2 = ctk.StringVar(value=datetime.now().strftime('%d/%m/%Y'))
        e2 = ctk.CTkEntry(r2, textvariable=v2)
        e2.grid(row=1, column=1, sticky='ew', padx=(4, 0))
        self.vars['date'] = v2

        # Account name + number
        r3 = ctk.CTkFrame(parent, fg_color='transparent')
        r3.pack(fill='x', padx=4, pady=(8, 0))
        r3.grid_columnconfigure(0, weight=1)
        r3.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(r3, text='Account Holder Name', font=ctk.CTkFont(size=11), anchor='w').grid(row=0, column=0, sticky='ew', padx=(0,4))
        ctk.CTkLabel(r3, text='Account Number', font=ctk.CTkFont(size=11), anchor='w').grid(row=0, column=1, sticky='ew', padx=(4,0))
        van = ctk.StringVar()
        ctk.CTkEntry(r3, textvariable=van).grid(row=1, column=0, sticky='ew', padx=(0,4))
        self.vars['account_name'] = van
        vac = ctk.StringVar()
        ctk.CTkEntry(r3, textvariable=vac).grid(row=1, column=1, sticky='ew', padx=(4,0))
        self.vars['account_number'] = vac

        # Payee
        row('Pay to the Order of *', 'payee', 'entry')
        self.vars['payee'].trace_add('write', lambda *a: self._on_change())

        # Amount
        ctk.CTkLabel(parent, text='Amount (AED) *', font=ctk.CTkFont(size=11), anchor='w').pack(fill='x', padx=4, pady=(8, 1))
        self.amt_var = ctk.StringVar()
        self.amt_var.trace_add('write', lambda *a: self._on_amount_change())
        ctk.CTkEntry(parent, textvariable=self.amt_var, font=ctk.CTkFont(family='Courier New', size=13)).pack(fill='x', padx=4)
        self.vars['amount'] = self.amt_var

        # Amount in words (auto)
        ctk.CTkLabel(parent, text='Amount in Words (auto)', font=ctk.CTkFont(size=11), anchor='w').pack(fill='x', padx=4, pady=(8, 1))
        self.words_box = ctk.CTkTextbox(parent, height=45, font=ctk.CTkFont(size=10))
        self.words_box.pack(fill='x', padx=4)
        self.words_box.configure(state='disabled')

        # Memo + status
        r4 = ctk.CTkFrame(parent, fg_color='transparent')
        r4.pack(fill='x', padx=4, pady=(8, 0))
        r4.grid_columnconfigure(0, weight=1)
        r4.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(r4, text='Memo / Purpose', font=ctk.CTkFont(size=11), anchor='w').grid(row=0, column=0, sticky='ew', padx=(0,4))
        ctk.CTkLabel(r4, text='Status', font=ctk.CTkFont(size=11), anchor='w').grid(row=0, column=1, sticky='ew', padx=(4,0))
        vm = ctk.StringVar()
        ctk.CTkEntry(r4, textvariable=vm).grid(row=1, column=0, sticky='ew', padx=(0,4))
        self.vars['memo'] = vm
        vs = ctk.StringVar(value='Pending')
        ctk.CTkComboBox(r4, variable=vs, values=['Pending', 'Cleared', 'Bounced', 'Cancelled']).grid(row=1, column=1, sticky='ew', padx=(4,0))
        self.vars['status'] = vs

        # PDC
        ctk.CTkLabel(parent, text='', font=ctk.CTkFont(size=8)).pack()
        self.pdc_var = ctk.BooleanVar()
        ctk.CTkCheckBox(parent, text='Post-Dated Cheque (PDC)',
                        variable=self.pdc_var,
                        command=self._on_pdc_toggle).pack(fill='x', padx=4)

        self.pdc_frame = ctk.CTkFrame(parent, fg_color='transparent')
        ctk.CTkLabel(self.pdc_frame, text='Presentation Date', font=ctk.CTkFont(size=11), anchor='w').pack(fill='x', padx=4, pady=(4, 1))
        self.pdc_date_var = ctk.StringVar()
        ctk.CTkEntry(self.pdc_frame, textvariable=self.pdc_date_var,
                     placeholder_text='DD/MM/YYYY').pack(fill='x', padx=4)
        self.vars['pdc_present_date'] = self.pdc_date_var

        # Notes
        ctk.CTkLabel(parent, text='Notes (internal)', font=ctk.CTkFont(size=11), anchor='w').pack(fill='x', padx=4, pady=(8, 1))
        self.notes_box = ctk.CTkTextbox(parent, height=50)
        self.notes_box.pack(fill='x', padx=4)

        # Buttons
        ctk.CTkLabel(parent, text='', font=ctk.CTkFont(size=8)).pack()
        btn_row = ctk.CTkFrame(parent, fg_color='transparent')
        btn_row.pack(fill='x', padx=4)
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(btn_row, text='💾  Save Cheque',
                      command=self.save_cheque, height=38).grid(row=0, column=0, sticky='ew', padx=(0, 4))
        ctk.CTkButton(btn_row, text='🖨️  Save & Print PDF',
                      command=self.save_and_print, height=38,
                      fg_color='#1a6baf', hover_color='#1557a0').grid(row=0, column=1, sticky='ew', padx=(4, 0))

    def _build_preview(self, parent):
        ctk.CTkLabel(parent, text='Cheque Preview',
                     font=ctk.CTkFont(size=13, weight='bold')).pack(pady=(16, 8), padx=16, anchor='w')

        # Canvas for cheque preview
        canvas_frame = ctk.CTkFrame(parent, fg_color='#1a1a2e')
        canvas_frame.pack(fill='x', padx=16)
        self.preview_canvas = tk.Canvas(canvas_frame, height=170, bg='#1a1a2e',
                                        highlightthickness=0)
        self.preview_canvas.pack(fill='x', padx=8, pady=8)
        self._draw_cheque_preview()

        # Tips
        tips = ctk.CTkFrame(parent, fg_color='#2a3a1a')
        tips.pack(fill='x', padx=16, pady=(12, 0))
        ctk.CTkLabel(tips, text='💡 Printing Tips', font=ctk.CTkFont(size=11, weight='bold'),
                     text_color='#90ee90').pack(anchor='w', padx=12, pady=(8, 2))
        tip_text = ("1. Click 'Save & Print PDF' to generate a print-ready PDF\n"
                    "2. Open the PDF and press Ctrl+P (or Cmd+P)\n"
                    "3. Set paper size to match your cheque dimensions\n"
                    "4. Disable headers/footers in print settings\n"
                    "5. Use 'Fit to Page' or '100%' scale")
        ctk.CTkLabel(tips, text=tip_text, font=ctk.CTkFont(size=10),
                     text_color='#a0c8a0', justify='left').pack(anchor='w', padx=12, pady=(0, 10))

    def _on_pdc_toggle(self):
        if self.pdc_var.get():
            self.pdc_frame.pack(fill='x', padx=4, pady=(4, 0))
        else:
            self.pdc_frame.pack_forget()

    def _on_amount_change(self):
        try:
            val = self.amt_var.get().strip()
            if val:
                words = amount_to_words(val)
                self.words_box.configure(state='normal')
                self.words_box.delete('1.0', 'end')
                self.words_box.insert('1.0', words)
                self.words_box.configure(state='disabled')
        except Exception:
            pass
        self._draw_cheque_preview()

    def _on_change(self, *args):
        self._draw_cheque_preview()

    def _draw_cheque_preview(self):
        c = self.preview_canvas
        c.delete('all')
        w = c.winfo_width() or 600
        h = 165

        # Get current bank color
        bank_name = self.vars.get('bank_id', ctk.StringVar()).get()
        bank = next((b for b in UAE_BANKS if b['name'] == bank_name), UAE_BANKS[0])
        color = bank['color']

        # Background
        c.create_rectangle(0, 0, w, h, fill='#FEFCE8', outline='#D6D3C4', width=1)

        # Bank stripe
        c.create_rectangle(0, 0, w, 28, fill=color, outline='')
        c.create_text(10, 14, text=bank['name'].upper(), fill='white',
                      font=('Courier New', 9, 'bold'), anchor='w')

        # Payee
        payee = self.vars.get('payee', ctk.StringVar()).get() or '___________________________________'
        c.create_text(10, 42, text='Pay to the Order of', fill='#888', font=('Arial', 7), anchor='w')
        c.create_line(10, 58, w - 110, 58, fill='#aaa')
        c.create_text(10, 55, text=payee[:45], fill='#111',
                      font=('Courier New', 10, 'bold'), anchor='w')

        # Date
        date_val = self.vars.get('date', ctk.StringVar()).get() or '__/__/____'
        c.create_text(w - 108, 42, text='Date', fill='#888', font=('Arial', 7), anchor='w')
        c.create_text(w - 108, 55, text=date_val, fill='#333', font=('Courier New', 9), anchor='w')
        c.create_line(w - 108, 58, w - 8, 58, fill='#aaa')

        # Amount box
        c.create_rectangle(w - 108, 63, w - 8, 90, outline='#666', fill='white')
        c.create_text(w - 58, 67, text='AED', fill='#888', font=('Arial', 7), anchor='center')
        amt_disp = self.amt_var.get() or '0.00'
        c.create_text(w - 58, 82, text=amt_disp, fill='#111',
                      font=('Courier New', 10, 'bold'), anchor='center')

        # Words
        words_val = self.words_box.get('1.0', 'end').strip() if self.words_box.winfo_exists() else ''
        c.create_text(10, 70, text='Amount in Words', fill='#888', font=('Arial', 7), anchor='w')
        short_words = words_val[:60] + ('...' if len(words_val) > 60 else '')
        c.create_text(10, 83, text=short_words, fill='#333', font=('Courier New', 8), anchor='w')
        c.create_line(10, 90, w - 115, 90, fill='#aaa')

        # Signature line
        c.create_line(w - 108, 125, w - 8, 125, fill='#888')
        c.create_text(w - 58, 132, text='Authorised Signature', fill='#888', font=('Arial', 7), anchor='center')

        # MICR
        c.create_text(w // 2, 155, text='⑆ 000000 ⑆ 0000000000 ⑆', fill='#bbb',
                      font=('Courier New', 8), anchor='center')

    def _get_form_data(self):
        bank_name = self.vars['bank_id'].get()
        bank = next((b for b in UAE_BANKS if b['name'] == bank_name), UAE_BANKS[-1])
        # Parse date
        date_raw = self.vars['date'].get().strip()
        if '/' in date_raw:
            parts = date_raw.split('/')
            if len(parts) == 3:
                date_iso = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            else:
                date_iso = date_raw
        else:
            date_iso = date_raw

        amount_raw = self.vars['amount'].get().replace(',', '').strip()
        try:
            amount = float(amount_raw)
        except Exception:
            amount = 0.0

        return {
            'bank_id': bank['id'],
            'cheque_number': self.vars['cheque_number'].get().strip(),
            'account_name': self.vars['account_name'].get().strip(),
            'account_number': self.vars['account_number'].get().strip(),
            'date': date_iso,
            'payee': self.vars['payee'].get().strip(),
            'amount': amount,
            'amount_words': amount_to_words(amount),
            'memo': self.vars['memo'].get().strip(),
            'status': self.vars['status'].get().lower(),
            'is_pdc': 1 if self.pdc_var.get() else 0,
            'pdc_present_date': self.vars['pdc_present_date'].get().strip() if self.pdc_var.get() else '',
            'notes': self.notes_box.get('1.0', 'end').strip(),
        }

    def _validate(self, data):
        if not data['payee']:
            messagebox.showerror('Missing Field', 'Please enter "Pay to the Order of"')
            return False
        if data['amount'] <= 0:
            messagebox.showerror('Missing Field', 'Please enter a valid Amount')
            return False
        if not data['date']:
            messagebox.showerror('Missing Field', 'Please enter the Cheque Date')
            return False
        return True

    def save_cheque(self):
        data = self._get_form_data()
        if not self._validate(data):
            return
        save_cheque(data)
        self.app._refresh_sidebar_stats()
        messagebox.showinfo('Saved', f'Cheque for {data["payee"]} saved successfully.')

    def save_and_print(self):
        data = self._get_form_data()
        if not self._validate(data):
            return

        # Ask for save location
        default_name = f"cheque_{data['payee'].replace(' ', '_')}_{data['date']}.pdf"
        path = filedialog.asksaveasfilename(
            defaultextension='.pdf',
            filetypes=[('PDF files', '*.pdf')],
            initialfile=default_name,
            title='Save Cheque PDF'
        )
        if not path:
            return

        try:
            generate_cheque_pdf(data, path)
            save_cheque(data)
            self.app._refresh_sidebar_stats()
            # Open the PDF
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
            messagebox.showinfo('PDF Ready', f'Cheque PDF saved to:\n{path}\n\nThe file will open for printing.')
        except Exception as ex:
            messagebox.showerror('Error', f'Could not generate PDF:\n{str(ex)}')

# ─── PDC Manager Tab ──────────────────────────────────────────────────────────

class PDCTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color='transparent')
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color='transparent')
        hdr.grid(row=0, column=0, sticky='ew', padx=20, pady=(20, 8))
        ctk.CTkLabel(hdr, text='PDC Manager', font=ctk.CTkFont(size=22, weight='bold')).pack(side='left')
        self.filter_var = ctk.StringVar(value='All')
        f = ctk.CTkComboBox(hdr, variable=self.filter_var, width=140,
                            values=['All', 'Pending', 'Cleared', 'Bounced', 'Cancelled'],
                            command=lambda v: self.refresh())
        f.pack(side='right', padx=(0, 0))
        ctk.CTkLabel(hdr, text='Filter:', font=ctk.CTkFont(size=12)).pack(side='right', padx=8)

        # Treeview (table)
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0, 8))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', background='#2b2b2b', foreground='white',
                        fieldbackground='#2b2b2b', rowheight=28, font=('Arial', 10))
        style.configure('Treeview.Heading', background='#1a2840', foreground='white',
                        font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1a6baf')])

        cols = ('ID', 'Bank', 'Cheque #', 'Payee', 'Date', 'Amount (AED)', 'Type', 'Status')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column('ID', width=40, anchor='center')
        self.tree.column('Bank', width=80, anchor='center')
        self.tree.column('Cheque #', width=80, anchor='center')
        self.tree.column('Payee', width=200)
        self.tree.column('Date', width=90, anchor='center')
        self.tree.column('Amount (AED)', width=110, anchor='e')
        self.tree.column('Type', width=70, anchor='center')
        self.tree.column('Status', width=80, anchor='center')

        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')

        # Action buttons
        btn_row = ctk.CTkFrame(self, fg_color='transparent')
        btn_row.grid(row=2, column=0, sticky='ew', padx=20, pady=(0, 16))
        ctk.CTkButton(btn_row, text='✅  Mark Cleared', width=130,
                      fg_color='#1a7a40', hover_color='#155e30',
                      command=lambda: self._set_status('cleared')).pack(side='left', padx=(0, 8))
        ctk.CTkButton(btn_row, text='❌  Mark Bounced', width=130,
                      fg_color='#8b0000', hover_color='#6e0000',
                      command=lambda: self._set_status('bounced')).pack(side='left', padx=(0, 8))
        ctk.CTkButton(btn_row, text='🖨️  Print Selected', width=130,
                      command=self._print_selected).pack(side='left', padx=(0, 8))
        ctk.CTkButton(btn_row, text='🗑️  Delete', width=100,
                      fg_color='#555', hover_color='#444',
                      command=self._delete_selected).pack(side='left')
        ctk.CTkButton(btn_row, text='↻  Refresh', width=90,
                      command=self.refresh).pack(side='right')

        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        cheques = get_all_cheques(self.filter_var.get())
        for c in cheques:
            bank = bank_by_id(c['bank_id'])
            pdc_label = 'PDC' if c['is_pdc'] else 'Normal'
            tag = c['status']
            self.tree.insert('', 'end', iid=str(c['id']), values=(
                c['id'], bank['short'], c['cheque_number'] or '—',
                c['payee'], c['date'],
                f"{c['amount']:,.2f}", pdc_label, c['status'].capitalize()
            ), tags=(tag,))
        self.tree.tag_configure('pending', foreground='#f59e0b')
        self.tree.tag_configure('cleared', foreground='#22c55e')
        self.tree.tag_configure('bounced', foreground='#ef4444')
        self.tree.tag_configure('cancelled', foreground='#9ca3af')
        self.app._refresh_sidebar_stats()

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Select Cheque', 'Please select a cheque first.')
            return None
        return int(sel[0])

    def _set_status(self, status):
        cid = self._selected_id()
        if cid:
            update_status(cid, status)
            self.refresh()

    def _delete_selected(self):
        cid = self._selected_id()
        if cid:
            if messagebox.askyesno('Delete', 'Delete this cheque record?'):
                delete_cheque_by_id(cid)
                self.refresh()

    def _print_selected(self):
        cid = self._selected_id()
        if not cid:
            return
        db = sqlite3.connect(get_db_path())
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM cheques WHERE id=?", (cid,)).fetchone()
        db.close()
        if not row:
            return
        data = dict(row)
        path = filedialog.asksaveasfilename(
            defaultextension='.pdf',
            filetypes=[('PDF files', '*.pdf')],
            initialfile=f"cheque_{data['payee'].replace(' ', '_')}.pdf",
            title='Save Cheque PDF'
        )
        if not path:
            return
        try:
            generate_cheque_pdf(data, path)
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
        except Exception as ex:
            messagebox.showerror('Error', str(ex))

# ─── Settings Tab ─────────────────────────────────────────────────────────────

class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color='transparent')
        self.app = app
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text='Settings', font=ctk.CTkFont(size=22, weight='bold')).pack(
            anchor='w', padx=20, pady=(20, 4))

        card = ctk.CTkFrame(self)
        card.pack(fill='x', padx=20, pady=8)

        ctk.CTkLabel(card, text='Database Location',
                     font=ctk.CTkFont(size=12, weight='bold')).pack(anchor='w', padx=16, pady=(12, 2))
        ctk.CTkLabel(card, text=get_db_path(),
                     font=ctk.CTkFont(size=10), text_color='gray').pack(anchor='w', padx=16, pady=(0, 12))

        ctk.CTkButton(card, text='📂  Open Database Folder',
                      command=self._open_db_folder, width=200).pack(anchor='w', padx=16, pady=(0, 12))

        # About
        about = ctk.CTkFrame(self)
        about.pack(fill='x', padx=20, pady=8)
        ctk.CTkLabel(about, text='About', font=ctk.CTkFont(size=12, weight='bold')).pack(
            anchor='w', padx=16, pady=(12, 2))
        about_text = ("UAE Cheque Printer Pro v1.0 — Free Software\n"
                      "Supports 14 UAE banks | PDC Management | PDF Print\n\n"
                      "Website: chequeprinteruae.com\n"
                      "Free to download, use, and share.")
        ctk.CTkLabel(about, text=about_text, font=ctk.CTkFont(size=11),
                     text_color='gray', justify='left').pack(anchor='w', padx=16, pady=(0, 12))

    def _open_db_folder(self):
        folder = os.path.dirname(get_db_path())
        if platform.system() == 'Windows':
            os.startfile(folder)
        elif platform.system() == 'Darwin':
            subprocess.run(['open', folder])
        else:
            subprocess.run(['xdg-open', folder])

# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app = App()
    app.mainloop()
