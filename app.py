import streamlit as st
import pandas as pd
import re
import hashlib
import datetime
from zoneinfo import ZoneInfo
import html
import streamlit.components.v1 as components

st.set_page_config(page_title="Deal Tracker", page_icon="🏠", layout="wide")

# ============================================================
# BASIC UI
# ============================================================
st.markdown("""
<style>
::-webkit-scrollbar { width: 16px !important; height: 16px !important; }
::-webkit-scrollbar-track { background: #f1f1f1 !important; }
::-webkit-scrollbar-thumb { background: #888 !important; border-radius: 8px !important; border: 3px solid #f1f1f1 !important; }
::-webkit-scrollbar-thumb:hover { background: #555 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنْ فَضْلِكَ</h1>", unsafe_allow_html=True)
st.markdown('<meta name="robots" content="noindex, nofollow">', unsafe_allow_html=True)

SHEET_ID = "1GmJcTrkHQwF6m33c4xbJI9pG7XyR7nn39ZOUeGcH86Y"

# ============================================================
# SESSION STATE
# ============================================================
DEFAULTS = {
    "search_active1": False,
    "last_query1": "",
    "search_active2": False,
    "last_query2": "",
    "show_all_expanders": False,
    "selected_ids": set(),
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, set) else value

def toggle_expanders():
    st.session_state.show_all_expanders = not st.session_state.show_all_expanders

# ============================================================
# LOAD MAIN DATA (SHEET 1)
# ============================================================
@st.cache_data(ttl=3600)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        df = pd.read_csv(url)
        if not df.empty and 'Date & Time' in df.columns:
            df['Parsed_Date'] = pd.to_datetime(
            df['Date & Time'],
            errors='coerce',
            dayfirst=True
        )
            df = df.sort_values(by='Parsed_Date', ascending=False)
        return df
    except Exception as e:
        st.error(f"Error loading sheet: {e}")
        return pd.DataFrame()

with st.spinner("Original Sheet se data load ho raha hai..."):
    df = load_data()

col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

if df.empty:
    st.error("⚠️ Data load nahi hua! Google Sheet ki 'Share' settings check karein.")
    st.stop()
else:
    st.markdown(f"🟢 **{len(df)}**")
    st.markdown("---")

# ============================================================
# KEYWORD INTELLIGENCE (Original Unchanged)
# ============================================================
KEYWORD_GROUPS = {
    "apartment": [
        "apartment", "apartments", "appartment", "appartments", "aprtment",
        "apprtment", "apprtments", "appatment", "apparment", "appartmint",
        "appartmet", "flat", "flats"
    ],
    "villa": ["villa", "villas", "vila", "vilaa", "villah", "vill", "cilla"],
    "house": ["house", "houses", "home", "homes", "bungalow", "bungalows"],
    "plot": ["plot", "plots"],
    "shop": ["shop", "shops"],
    "office": ["office", "offices"],
    "commercial": ["commercial", "commercials", "comercial", "commercil", "commercail"],
    "portion": ["portion", "portions"],
    "tower": ["tower", "towers", "towr"],
    "precinct": ["precinct", "precincts", "precint", "preinct", "precient", "precent", "pricenct", "preint"],
    "block": ["block", "blocks", "bloc", "blk"],
    "road": ["road", "roads", "rd"],
    "boulevard": ["boulevard", "boulevards", "bullevard", "blvd"],
    "rent": ["rent", "rental", "rentals", "renting", "rnt"],
    "sale": ["sale", "sales", "sell", "selling", "seller", "sele", "sal", "sare", "saleh"],
    "purchase": ["purchase", "purchases", "buy", "buying", "buyer", "buyers"],
    "available": [
        "available", "avaible", "avaliable", "avaialble", "avalable", "availabe",
        "availablle", "availabll", "avialable", "avalible", "ailable"
    ],
    "required": [
        "required", "require", "requires", "requird", "requierd", "reqird", "rrquired",
        "sequire", "need", "needs", "looking", "wanted", "want", "buyer", "client",
        "chahiye", "chahye", "darkar", "darkaar", "talab"
    ],
    "demand": ["demand", "demands", "damand", "demamd", "dmand", "demmand", "deamand", "dsmand", "demans", "demond", "decmand", "demad"],
    "allotment": ["allotment", "allotments", "alotment", "alltment", "allotement", "allottment", "allotmnet", "alltmnt"],
    "corner": ["corner", "corners", "conner", "cornr", "carner", "coner"],
    "jinnah": ["jinnah", "jinah", "jinnal", "jinh", "jinnha"],
    "facing": ["facing", "fecing", "fasing"],
    "park": ["park", "parks"],
    "west": ["west", "western"],
    "main": ["main"],
    "grey": ["grey", "gray"],
    "structure": ["structure", "structures", "stucture"],
    "furnished": ["furnished", "furnish", "furnshed", "furnishes", "furnisher", "fuenshed", "furnsihed"],
    "unfurnished": ["unfurnished"],
    "brand": ["brand"],
    "new": ["new"],
    "yard": ["yard", "yards", "gaz", "gazz", "sqyd", "sqyds", "sqyard", "sqyards"],
    "marla": ["marla", "marlas"],
    "kanal": ["kanal", "kanals"],
    "bedroom": ["bedroom", "bedrooms", "badroom"],
    "storey": ["storey", "storeys", "story", "stories"],
    "basement": ["basement", "basements"],
}

ALIAS_TO_GROUP = {}
for canonical, aliases in KEYWORD_GROUPS.items():
    for alias in aliases:
        ALIAS_TO_GROUP[alias.lower()] = canonical

def regex_for_aliases(aliases):
    escaped = sorted({re.escape(a.lower()) for a in aliases}, key=len, reverse=True)
    return r"\b(?:" + "|".join(escaped) + r")\b"

def get_search_patterns(query):
    raw_terms = query.lower().split()
    patterns = []
    used_groups = set()

    for term in raw_terms:
        p_match = re.fullmatch(r"p[-_]?([0-9]+[a-z]?)", term)
        if p_match:
            number = p_match.group(1)
            patterns.append(
                rf"\b(?:p[-_]?{re.escape(number)}|precinct[-_\s]*{re.escape(number)})\b"
            )
            continue
        canonical = ALIAS_TO_GROUP.get(term)
        if canonical and canonical not in used_groups:
            patterns.append(regex_for_aliases(KEYWORD_GROUPS[canonical]))
            used_groups.add(canonical)
        elif canonical:
            continue
        else:
            patterns.append(r"\b" + re.escape(term) + r"\b")

    return patterns

# ============================================================
# WHATSAPP NUMBER
# ============================================================
def get_clean_whatsapp(text):
    phone_pattern = r'(?:\+92|0)?(3[0-9]{9})'
    match = re.search(phone_pattern, str(text))
    if match:
        num = '92' + match.group(1)
        return f"https://wa.me/{num}"
    return None

def generate_id(date_time, sender, text):
    unique_string = f"{date_time}_{sender}_{text}"
    return hashlib.md5(unique_string.encode()).hexdigest()

# ============================================================
# DATE FILTER
# ============================================================
st.markdown("### 📅 Date Filter")
quick_days = st.radio(
    "Quick Select:",
    ["1D", "2D", "3D", "4D", "5D", "6D", "7D", "2W", "3W", "1M", "All Time", "Custom Range"],
    horizontal=True,
)

pakistan_tz = ZoneInfo("Asia/Karachi")
today = datetime.datetime.now(pakistan_tz).date()

if quick_days == "1D": start_date, end_date = today, today
elif quick_days == "2D": start_date, end_date = today - datetime.timedelta(days=1), today
elif quick_days == "3D": start_date, end_date = today - datetime.timedelta(days=2), today
elif quick_days == "4D": start_date, end_date = today - datetime.timedelta(days=3), today
elif quick_days == "5D": start_date, end_date = today - datetime.timedelta(days=4), today
elif quick_days == "6D": start_date, end_date = today - datetime.timedelta(days=5), today
elif quick_days == "7D": start_date, end_date = today - datetime.timedelta(days=6), today
elif quick_days == "2W": start_date, end_date = today - datetime.timedelta(days=13), today
elif quick_days == "3W": start_date, end_date = today - datetime.timedelta(days=20), today
elif quick_days == "1M": start_date, end_date = today - datetime.timedelta(days=29), today
elif quick_days == "All Time":
    valid_dates = df['Parsed_Date'].dropna()
    start_date = valid_dates.min().date() if not valid_dates.empty else today
    end_date = today
else:
    col_d1, col_d2 = st.columns(2)
    valid_dates = df['Parsed_Date'].dropna()
    min_d = valid_dates.min().date() if not valid_dates.empty else today - datetime.timedelta(days=30)
    with col_d1: start_date = st.date_input("Start Date", min_d)
    with col_d2: end_date = st.date_input("End Date", today)

parsed_dates_only = df['Parsed_Date'].dt.date
mask = (parsed_dates_only >= start_date) & (parsed_dates_only <= end_date)
df = df.loc[mask].copy()
st.markdown(f"**🎯 Filtered Records ({quick_days}): {len(df)}**")
st.markdown("---")

# ============================================================
# COPY ALL RESULTS
# ============================================================
def clean_html_text(value):
    value = str(value)
    value = re.sub(r'<br\s*/?>', '\n', value, flags=re.I)
    value = re.sub(r'<[^>]+>', '', value)
    return html.unescape(value).strip()

def make_copy_text(items):
    blocks = []
    for number, item in enumerate(items, 1):
        deal_text = clean_html_text(item.get('deal_text', ''))
        original = clean_html_text(item.get('original_details', ''))
        block = (
            f"Record #{number}\n"
            f"Waqt: {item.get('date_time', 'N/A')}\n"
            f"Source: {item.get('sender', 'N/A')}\n"
            f"Relevant Deal: {deal_text}"
        )
        if original and original != deal_text:
            block += f"\nOriginal Message: {original}"
        blocks.append(block)
    return "\n\n" + "\n\n------------------------------\n\n".join(blocks)

def copy_all_results(items, prefix):
    if not items: return
    copy_text = make_copy_text(items)
    safe_text = html.escape(copy_text)
    height = min(500, max(160, 110 + len(items) * 45))
    components.html(
        f"""
        <div style="font-family:Arial,sans-serif;">
          <button id="copyBtn" style="background:#198754;color:white;border:none;border-radius:6px;padding:10px 18px;font-size:16px;cursor:pointer;">📋 Copy All Records</button>
          <span id="status" style="margin-left:10px;font-weight:600;"></span>
          <textarea id="allText" style="width:100%;height:{height}px;margin-top:10px;padding:10px;border:1px solid #ccc;border-radius:6px;font-size:14px;box-sizing:border-box;" readonly>{safe_text}</textarea>
        </div>
        <script>
        const btn = document.getElementById('copyBtn');
        const box = document.getElementById('allText');
        const status = document.getElementById('status');
        btn.addEventListener('click', async () => {{
          try {{
            await navigator.clipboard.writeText(box.value);
            status.textContent = '✅ Copied!';
          }} catch (e) {{
            box.focus(); box.select(); document.execCommand('copy'); status.textContent = '✅ Copied!';
          }}
          setTimeout(() => status.textContent = '', 2500);
        }});
        </script>
        """, height=height + 80, scrolling=True,
    )

# ============================================================
# UI RENDERER
# ============================================================
def render_deal_ui(item, record_num=None):
    if item['source_tab'] == 'tab1':
        title_text = f"Record #{record_num}" if record_num is not None else "Saved Record"
        st.markdown(f"<h3 style='text-align: center;'><span style='background-color: #d4edda; color: #155724; padding: 4px 12px; border-radius: 6px; border: 1px solid #c3e6cb;'>{title_text}</span></h3>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: st.markdown(f"🕒 **Waqt:** {item['date_time']}")
        with c2: st.markdown(f"👤 **Source:** {item['sender']}")
        st.markdown(f"📌 **Relevant Deals:**<br>{item['deal_text']}", unsafe_allow_html=True)
        if item['wa_link']: st.markdown(f"[📲 Is Number par WhatsApp Chat Kholein]({item['wa_link']})", unsafe_allow_html=True)
        with st.expander("👀 Poora Original Message Dekhein (Show Full List)", expanded=st.session_state.show_all_expanders):
            st.markdown(item['original_details'], unsafe_allow_html=True)
    elif item['source_tab'] == 'tab2_avail':
        st.markdown(f"<div style='background-color: #f0fff4; padding: 15px; border-radius: 10px; border-left: 5px solid #48bb78; margin-bottom: 10px;'><small>🕒 {item['date_time']} | 👤 {item['sender']}</small><br><br>{item['deal_text']}</div>", unsafe_allow_html=True)
        if item['wa_link']: st.markdown(f"[📲 WhatsApp Karein]({item['wa_link']})", unsafe_allow_html=True)
        with st.expander("👀 Poora Original Message Dekhein", expanded=st.session_state.show_all_expanders):
            st.markdown(item['original_details'], unsafe_allow_html=True)
    elif item['source_tab'] == 'tab2_req':
        st.markdown(f"<div style='background-color: #fff5f5; padding: 15px; border-radius: 10px; border-left: 5px solid #f56565; margin-bottom: 10px;'><small>🕒 {item['date_time']} | 👤 {item['sender']}</small><br><br>{item['deal_text']}</div>", unsafe_allow_html=True)
        if item['wa_link']: st.markdown(f"[📲 WhatsApp Karein]({item['wa_link']})", unsafe_allow_html=True)
        with st.expander("👀 Poora Original Message Dekhein", expanded=st.session_state.show_all_expanders):
            st.markdown(item['original_details'], unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

# ============================================================
# TABS (Original 3 + New 4th Tab)
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Smart Search", "🤝 Deal Matcher", "📊 Analytics Dashboard", "📋 Client Tracker"])

# ============================================================
# TAB 1: SMART SEARCH (Original, no changes)
# ============================================================
with tab1:
    st.markdown("### 🔍 General Search")
    user_query = st.text_input("Search:", placeholder="Ali block apartment ya p3", key="search_input_tab1")

    if st.button("🔍 Search Karein", key="btn_tab1"):
        st.session_state.search_active1 = True
        st.session_state.last_query1 = user_query
    elif user_query != st.session_state.last_query1:
        st.session_state.search_active1 = False
        st.session_state.last_query1 = user_query

    if st.session_state.search_active1 and user_query.strip() and not df.empty:
        with st.spinner("Talaash ki ja rahi hai..."):
            search_patterns = get_search_patterns(user_query)
            matched_results = []
            seen_signatures = set()

            for _, row in df.iterrows():
                date_time = row.get('Date & Time', 'N/A')
                sender = row.get('Sender / Contact', row.get('Source/Sender', 'N/A'))
                details = str(row.get('Message Details', row.to_dict())).strip()
                paragraphs = re.split(r'\n\s*\n', details)
                if not paragraphs: continue

                header_chunk = paragraphs[0]
                header_lower = header_chunk.lower()
                matched_chunks = []
                formatted_full_message_paragraphs = []

                for i, para in enumerate(paragraphs):
                    para_lower = para.lower()
                    chunk_match = True
                    for pattern in search_patterns:
                        if not (re.search(pattern, para_lower) or re.search(pattern, header_lower)):
                            chunk_match = False
                            break

                    if chunk_match and search_patterns:
                        lines = para.split('\n')
                        hl_lines = []
                        for line in lines:
                            if any(re.search(p, line.lower()) for p in search_patterns):
                                hl_lines.append(f"<mark style='background-color: #fff3cd; color: #000; padding: 2px 4px; border-radius: 3px;'>{line.strip()}</mark>")
                            else:
                                hl_lines.append(line.strip())
                        formatted_para = "<br>".join(hl_lines)
                        if i == 0: matched_chunks.append(f"<b>[Top Heading / Context]</b><br>{formatted_para}")
                        else: matched_chunks.append(f"<b>[Matched Deal]</b><br>{formatted_para}")
                        formatted_full_message_paragraphs.append(formatted_para)
                    else:
                        formatted_full_message_paragraphs.append(para.replace('\n', '<br>'))

                if matched_chunks:
                    matched_html = "<br><br>".join(matched_chunks)
                    if not any("[Top Heading" in chunk for chunk in matched_chunks):
                        header_html = f"<div style='color: gray; font-size: 0.9em;'><i>Context (Shuru Ki Line):<br>{header_chunk.replace(chr(10), '<br>')}</i></div><br>"
                        matched_html = header_html + matched_html

                    highlighted_original_details = "<br><br>".join(formatted_full_message_paragraphs)
                    wa_link = get_clean_whatsapp(f"{sender} {details}")
                    clean_text_sig = re.sub(r'<[^>]*?>', '', matched_html).strip().lower()
                    signature = f"{sender}_{clean_text_sig}"
                    if signature in seen_signatures: continue
                    seen_signatures.add(signature)

                    item_id = generate_id(date_time, sender, matched_html)
                    matched_results.append({
                        'id': item_id,
                        'date_time': date_time,
                        'sender': sender,
                        'deal_text': matched_html,
                        'wa_link': wa_link,
                        'original_details': highlighted_original_details,
                        'source_tab': 'tab1',
                    })

        if not matched_results: st.warning("❌ Aapke keywords wala koi record nahi mila.")
        else:
            st.success(f"🎉 Qamyabi! {len(matched_results)} unique matching records mil gaye hain:")
            copy_all_results(matched_results[:150], "tab1")
            btn_text = "🔼 Sab Messages Band Karein (Collapse All)" if st.session_state.show_all_expanders else "🔽 Sab Messages Kholein (Expand All)"
            st.button(btn_text, on_click=toggle_expanders, key="btn_exp_t1")
            for match_idx, item in enumerate(matched_results[:150], 1):
                render_deal_ui(item, match_idx)

# ============================================================
# TAB 2: DEAL MATCHER (Original, no changes)
# ============================================================
with tab2:
    st.markdown("### 🤝 Aamne-Samne Matcher (Demand vs Supply)")
    match_query = st.text_input("Property to Match:", placeholder="e.g., Ali block villa", key="search_input_tab2")

    if st.button("🤝 Match Deals", key="btn_tab2"):
        st.session_state.search_active2 = True
        st.session_state.last_query2 = match_query
    elif match_query != st.session_state.last_query2:
        st.session_state.search_active2 = False
        st.session_state.last_query2 = match_query

    if st.session_state.search_active2 and match_query.strip() and not df.empty:
        with st.spinner("Deals match ki ja rahi hain..."):
            search_patterns = get_search_patterns(match_query)
            required_deals = []
            available_deals = []
            seen_signatures_tab2 = set()
            required_keywords = r'\b(need|needs|require|required|requires|chahiye|chahye|looking|buyer|buyers|client|wanted|want|darkar|darkaar|talab)\b'

            for _, row in df.iterrows():
                date_time = row.get('Date & Time', 'N/A')
                sender = row.get('Sender / Contact', row.get('Source/Sender', 'N/A'))
                details = str(row.get('Message Details', row.to_dict())).strip()
                paragraphs = re.split(r'\n\s*\n', details)
                if not paragraphs: continue

                header_chunk = paragraphs[0]
                header_lower = header_chunk.lower()
                matched_chunks_data = []
                formatted_full_message_paragraphs = []

                for i, para in enumerate(paragraphs):
                    para_lower = para.lower()
                    chunk_match = True
                    for pattern in search_patterns:
                        if not (re.search(pattern, para_lower) or re.search(pattern, header_lower)):
                            chunk_match = False
                            break
                    if chunk_match and search_patterns:
                        lines = para.split('\n')
                        hl_lines = []
                        for line in lines:
                            if any(re.search(p, line.lower()) for p in search_patterns):
                                hl_lines.append(f"<mark style='background-color: #fff3cd; color: #000; padding: 2px 4px; border-radius: 3px;'>{line.strip()}</mark>")
                            else:
                                hl_lines.append(line.strip())
                        formatted_para = "<br>".join(hl_lines)
                        formatted_full_message_paragraphs.append(formatted_para)
                        is_required = bool(re.search(required_keywords, para_lower) or re.search(required_keywords, header_lower))
                        matched_chunks_data.append({'deal_text': formatted_para, 'is_required': is_required})
                    else:
                        formatted_full_message_paragraphs.append(para.replace('\n', '<br>'))

                if matched_chunks_data:
                    highlighted_original_details = "<br><br>".join(formatted_full_message_paragraphs)
                    wa_link = get_clean_whatsapp(f"{sender} {details}")

                    for m_data in matched_chunks_data:
                        clean_text_sig = re.sub(r'<[^>]*?>', '', m_data['deal_text']).strip().lower()
                        signature = f"{sender}_{clean_text_sig}"
                        if signature in seen_signatures_tab2: continue
                        seen_signatures_tab2.add(signature)

                        item_id = generate_id(date_time, sender, m_data['deal_text'])
                        deal_dict = {
                            'id': item_id,
                            'date_time': date_time,
                            'sender': sender,
                            'deal_text': m_data['deal_text'],
                            'wa_link': wa_link,
                            'original_details': highlighted_original_details,
                            'source_tab': 'tab2_req' if m_data['is_required'] else 'tab2_avail',
                        }
                        if m_data['is_required']: required_deals.append(deal_dict)
                        else: available_deals.append(deal_dict)

        all_matcher_items = available_deals + required_deals
        if available_deals or required_deals:
            copy_all_results(all_matcher_items[:50], "tab2")
            btn_text2 = "🔼 Sab Messages Band Karein (Collapse All)" if st.session_state.show_all_expanders else "🔽 Sab Messages Kholein (Expand All)"
            st.button(btn_text2, on_click=toggle_expanders, key="btn_exp_t2")

        col_avail, col_req = st.columns(2)
        with col_avail:
            st.markdown("### 🟢 Available (Supply)")
            if not available_deals: st.info("Koi 'Available' deal nahi mili.")
            else:
                for item in available_deals[:25]: render_deal_ui(item)
        with col_req:
            st.markdown("### 🔴 Required (Demand)")
            if not required_deals: st.info("Koi 'Required' (Demand) deal nahi mili.")
            else:
                for item in required_deals[:25]: render_deal_ui(item)

# ============================================================
# TAB 3: ANALYTICS (Original, fixed KeyError)
# ============================================================
with tab3:
    st.markdown("### 📊 Market Analytics Dashboard")
    if not df.empty:
        st.markdown("#### 📈 Daily Market Activity")
        daily_counts = df.groupby(df['Parsed_Date'].dt.date).size()
        st.line_chart(daily_counts)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### 🏙️ Top 15 Active Precincts")
            precinct_pattern = r'(?i)\b(?:p[-_]?|precinct\s*)([0-9]+[a-z]?)\b'
            extracted_p = df['Message Details'].astype(str).str.extractall(precinct_pattern)[0]
            if not extracted_p.empty:
                p_counts = extracted_p.value_counts().reset_index()
                p_counts.columns = ['Precinct', 'Mentions']
                p_counts['Precinct'] = 'P-' + p_counts['Precinct'].astype(str)
                st.bar_chart(p_counts.head(15).set_index('Precinct'))

            st.markdown("#### 🏠 Property Type Analysis")
            def get_prop_type(text):
                t = str(text).lower()
                types = []
                if re.search(regex_for_aliases(KEYWORD_GROUPS['plot']), t): types.append('Plot')
                if re.search(regex_for_aliases(KEYWORD_GROUPS['villa']), t) or re.search(regex_for_aliases(KEYWORD_GROUPS['house']), t): types.append('Villa / House')
                if re.search(regex_for_aliases(KEYWORD_GROUPS['apartment']), t): types.append('Apartment / Flat')
                if re.search(regex_for_aliases(KEYWORD_GROUPS['commercial']), t) or re.search(regex_for_aliases(KEYWORD_GROUPS['shop']), t) or re.search(regex_for_aliases(KEYWORD_GROUPS['office']), t): types.append('Commercial')
                return types if types else ['Other']

            all_types = df['Message Details'].apply(get_prop_type).explode()
            st.bar_chart(all_types.value_counts())

            st.markdown("#### ⚖️ Demand vs Supply")
            req_keywords = r'\b(need|needs|require|required|requires|chahiye|chahye|looking|buyer|buyers|client|wanted|want|darkar|darkaar|talab)\b'
            def get_demand_supply(text):
                if re.search(req_keywords, str(text).lower()): return 'Required (Demand)'
                return 'Available (Supply)'
            ds_counts = df['Message Details'].apply(get_demand_supply).value_counts()
            st.bar_chart(ds_counts)

        with col_c2:
            st.markdown("#### 📐 Top Property Sizes")
            size_pattern = r'(?i)(\d{2,4})\s*(?:gaz|sq\s*yard|sqyd|sq\s*yds|yards|yard|sqft|sq\s*ft)'
            extracted_sizes = df['Message Details'].astype(str).str.extractall(size_pattern)[0]
            if not extracted_sizes.empty:
                s_counts = extracted_sizes.value_counts().reset_index()
                s_counts.columns = ['Size', 'Count']
                s_counts['Size'] = s_counts['Size'].astype(str) + ' Gaz/SqYd'
                st.bar_chart(s_counts.head(10).set_index('Size'))
            else: st.info("Size data available nahi hai.")

            st.markdown("#### ⭐ Top Prime Features")
            def get_features(text):
                t = str(text).lower()
                feats = []
                if re.search(r'\bwest\s*open\b', t): feats.append('West Open')
                if re.search(r'\bpark\s*(face|facing)\b', t): feats.append('Park Face')
                if re.search(regex_for_aliases(KEYWORD_GROUPS['corner']), t): feats.append('Corner')
                if re.search(r'\bjinnah\s*(face|facing|back)\b', t): feats.append('Jinnah Facing')
                if re.search(r'\bmain\s*(boulevard|road)\b', t): feats.append('Main Road')
                return feats
            all_feats = df['Message Details'].apply(get_features).explode().dropna()
            if not all_feats.empty: st.bar_chart(all_feats.value_counts())
            else: st.info("No prime features found.")

            st.markdown("#### 🏗️ Construction Status")
            def get_status(text):
                t = str(text).lower()
                status = []
                if re.search(r'\bbrand\s*new\b', t): status.append('Brand New')
                if re.search(r'\b(?:grey|gray)\s*structure\b', t): status.append('Grey Structure')
                if re.search(regex_for_aliases(KEYWORD_GROUPS['furnished']), t): status.append('Furnished')
                if re.search(regex_for_aliases(KEYWORD_GROUPS['unfurnished']), t): status.append('Unfurnished')
                return status
            all_status = df['Message Details'].apply(get_status).explode().dropna()
            if not all_status.empty: st.bar_chart(all_status.value_counts())
            else: st.info("No status keywords found.")
    else:
        st.warning("Data available nahi hai.")


# ============================================================
# TAB 4: CLIENT TRACKER (New Section for Google Sheet data)
# ============================================================
with tab4:
    st.markdown("### 📋 Apne Clients ki List Dekhein")
    st.markdown("Apni Google Sheet (`Client Requirements`) ka data direct yahan filter aur manage karein. Yeh data har 30 minute mein auto-refresh hota hai.")
    
    # TTL set to 1800 seconds (30 mins) for auto-refresh
    @st.cache_data(ttl=1800)
    def load_client_requirements():
        req_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Client+Requirements"
        try:
            return pd.read_csv(req_url)
        except Exception:
            return pd.DataFrame()

    clients_df = load_client_requirements()

    # --- FILTERS ROW 1 (PROPERTY TYPE) ---
    st.markdown("#### 🏷️ 1. Filter By Property")
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1: c_plots = st.checkbox("Plots", value=True, key="c_plot")
    with col_t2: c_villas = st.checkbox("Villas / Houses", value=True, key="c_villa")
    with col_t3: c_apts = st.checkbox("Apartments", value=True, key="c_apt")
    with col_t4: c_comm = st.checkbox("Shops / Commercial", value=True, key="c_comm")

    # --- FILTERS ROW 2 (ACTION) ---
    st.markdown("#### 🔄 2. Filter By Action")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1: c_buy = st.checkbox("Buy", value=True, key="c_buy")
    with col_a2: c_sell = st.checkbox("Sell", value=True, key="c_sell")
    with col_a3: c_rent = st.checkbox("Rent", value=True, key="c_rent")

    st.markdown("---")

    if clients_df.empty:
        st.info("⚠️ Client Requirements sheet khali hai ya fetch nahi ho saki. Pehle Google Sheet mein entries daalein.")
    else:
        # Filtering Logic
        filtered_clients = []
        for _, row in clients_df.iterrows():
            c_name = str(row.get('Client Name', '')).strip()
            if not c_name or c_name == 'nan':
                continue
                
            c_type = str(row.get('Property Type', '')).lower()
            c_action = str(row.get('Action', '')).lower()
            
            # 1. Type Match Check
            type_match = False
            if (c_plots and "plot" in c_type) or \
               (c_villas and ("villa" in c_type or "house" in c_type)) or \
               (c_apts and ("apartment" in c_type or "flat" in c_type)) or \
               (c_comm and ("shop" in c_type or "commercial" in c_type)):
                type_match = True
                
            if not c_type or c_type == 'nan': 
                if c_plots and c_villas and c_apts and c_comm: type_match = True

            # 2. Action Match Check
            action_match = False
            if (c_buy and "buy" in c_action) or \
               (c_sell and "sell" in c_action) or \
               (c_rent and "rent" in c_action):
                action_match = True
                
            if not c_action or c_action == 'nan':
                if c_buy and c_sell and c_rent: action_match = True

            # Agar dono filter pass hon to show karein
            if type_match and action_match:
                filtered_clients.append(row)

        # Output Results
        if not filtered_clients:
            st.warning("❌ Aapke set kiye gaye filters ke mutabiq koi client nahi mila.")
        else:
            st.success(f"✅ {len(filtered_clients)} Clients Found!")
            
            # Khoobsurat Table/Card Format
            for row in filtered_clients:
                name = str(row.get('Client Name', 'Unknown')).strip()
                phone = str(row.get('Phone Number', '')).strip()
                action = str(row.get('Action', '')).strip()
                ptype = str(row.get('Property Type', '')).strip()
                loc = str(row.get('Location / Keywords', '')).strip()
                budget = str(row.get('Budget in Lacs', '')).strip()
                urgency = str(row.get('Urgency', '')).strip()
                
                if budget == 'nan' or not budget: budget = "N/A"
                if urgency == 'nan' or not urgency: urgency = "N/A"
                if loc == 'nan' or not loc: loc = "N/A"
                
                # WhatsApp Link Generation (Same format as Tab 1)
                wa_link = get_clean_whatsapp(phone) if phone and phone != 'nan' else ""
                wa_btn = f"<a href='{wa_link}' target='_blank' style='background-color:#25D366; color:white; padding:6px 12px; border-radius:5px; text-decoration:none; font-size: 13px; font-weight:bold;'>📲 WhatsApp Chat</a>" if wa_link else "<span style='color:#dc3545;font-size:12px;'>No valid number</span>"
                
                st.markdown(f"""
                <div style='background-color: #ffffff; padding: 15px; border-radius: 8px; margin-bottom: 12px; border-left: 5px solid #6f42c1; box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.08); border: 1px solid #e9ecef;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h4 style='margin:0; color: #333;'>👤 {name}</h4>
                        <div>{wa_btn}</div>
                    </div>
                    <hr style='margin: 10px 0; border-color: #f1f1f1;'>
                    <table style='width: 100%; font-size: 14.5px; text-align: left; border-collapse: collapse;'>
                        <tr>
                            <td style='padding: 5px; color: #495057;'><b>Action:</b> <span style='color:#007bff; font-weight:bold;'>{action}</span></td>
                            <td style='padding: 5px; color: #495057;'><b>Property:</b> {ptype}</td>
                            <td style='padding: 5px; color: #495057;'><b>Urgency:</b> {urgency}</td>
                        </tr>
                        <tr>
                            <td colspan='2' style='padding: 5px; color: #495057;'><b>📍 Location / Demand:</b> {loc}</td>
                            <td style='padding: 5px; color: #495057;'><b>💰 Budget:</b> {budget}</td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)
