import streamlit as st
import pandas as pd
import re
import hashlib

st.set_page_config(page_title="Deal", page_icon="🏠", layout="wide") 

st.markdown("<h1 style='text-align: center;'>Deal</h1>", unsafe_allow_html=True)
st.markdown('<meta name="robots" content="noindex, nofollow">', unsafe_allow_html=True)

# Aapki Asli / Original Google Sheet ki ID
SHEET_ID = "1GmJcTrkHQwF6m33c4xbJI9pG7XyR7nn39ZOUeGcH86Y"

# ==========================================
# MEMORY SYSTEM (Bookmarks & Search State)
# ==========================================
if 'shahjhan_bm' not in st.session_state:
    st.session_state.shahjhan_bm = {}
if 'touqeer_bm' not in st.session_state:
    st.session_state.touqeer_bm = {}
if 'search_active1' not in st.session_state:
    st.session_state.search_active1 = False
if 'last_query1' not in st.session_state:
    st.session_state.last_query1 = ""
if 'search_active2' not in st.session_state:
    st.session_state.search_active2 = False
if 'last_query2' not in st.session_state:
    st.session_state.last_query2 = ""

@st.cache_data(ttl=3600) 
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        df = pd.read_csv(url)
        if not df.empty:
            if 'Date & Time' in df.columns:
                df['Parsed_Date'] = pd.to_datetime(df['Date & Time'], errors='coerce')
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
else:
    st.markdown(f"🟢 **Total Records: {len(df)}**")
    st.markdown("---")

# Precise & Smart Keyword Pattern Generator
def get_search_patterns(query):
    terms = query.lower().split()
    term_patterns = []
    for term in terms:
        if re.match(r'^p\d+$', term):
            num = term[1:]
            pattern = r'\b(p-?' + num + r'|precinct\s*' + num + r')\b'
            term_patterns.append(pattern)
        elif term in ['block', 'bloc', 'blk']:
            term_patterns.append(r'\b(block|bloc|blk)\b')
        elif term in ['rent', 'rental']:
            term_patterns.append(r'\b(rent|rental)\b')
        else:
            term_patterns.append(r'\b' + re.escape(term) + r'\b')
    return term_patterns

# Clean WhatsApp Direct Number Extractor
def get_clean_whatsapp(text):
    phone_pattern = r'(?:\+92|0)?(3[0-9]{9})'
    match = re.search(phone_pattern, text)
    if match:
        num = '92' + match.group(1)
        return f"https://wa.me/{num}"
    return None

# ==========================================
# REUSABLE UI & BOOKMARK LOGIC
# ==========================================
def render_bookmark_buttons(item_dict, unique_key_prefix):
    uid = item_dict['id']
    is_sj = uid in st.session_state.shahjhan_bm
    is_tq = uid in st.session_state.touqeer_bm
    
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("❌ Remove ShahJhan" if is_sj else "🔖 Save ShahJhan", key=f"sj_{unique_key_prefix}_{uid}"):
            if is_sj: del st.session_state.shahjhan_bm[uid]
            else: st.session_state.shahjhan_bm[uid] = item_dict
            st.rerun()
    with c2:
        if st.button("❌ Remove Touqeer" if is_tq else "🔖 Save Touqeer", key=f"tq_{unique_key_prefix}_{uid}"):
            if is_tq: del st.session_state.touqeer_bm[uid]
            else: st.session_state.touqeer_bm[uid] = item_dict
            st.rerun()

def render_deal_ui(item, key_prefix, record_num=None):
    if item['source_tab'] == 'tab1':
        title_text = f"Record #{record_num}" if record_num is not None else "Saved Record"
        st.markdown(
            f"<h3 style='text-align: center;'><span style='background-color: #d4edda; color: #155724; padding: 4px 12px; border-radius: 6px; border: 1px solid #c3e6cb;'>{title_text}</span></h3>", 
            unsafe_allow_html=True
        )
        
        c1, c2 = st.columns(2)
        with c1: st.markdown(f"🕒 **Waqt:** {item['date_time']}")
        with c2: st.markdown(f"👤 **Source:** {item['sender']}")
        st.markdown(f"📌 **Relevant Deals:**<br>{item['deal_text']}", unsafe_allow_html=True)
        if item['wa_link']: st.markdown(f"[📲 Is Number par WhatsApp Chat Kholein]({item['wa_link']})", unsafe_allow_html=True)
        with st.expander("👀 Poora Original Message Dekhein (Show Full List)"):
            st.markdown(item['original_details'], unsafe_allow_html=True)
            
    elif item['source_tab'] == 'tab2_avail':
        st.markdown(f"""
        <div style='background-color: #f0fff4; padding: 15px; border-radius: 10px; border-left: 5px solid #48bb78; margin-bottom: 10px;'>
            <small>🕒 {item['date_time']} | 👤 {item['sender']}</small><br><br>
            {item['deal_text']}
        </div>
        """, unsafe_allow_html=True)
        if item['wa_link']: st.markdown(f"[📲 WhatsApp Karein]({item['wa_link']})", unsafe_allow_html=True)
        with st.expander("👀 Poora Original Message Dekhein"):
            st.markdown(item['original_details'], unsafe_allow_html=True)
            
    elif item['source_tab'] == 'tab2_req':
        st.markdown(f"""
        <div style='background-color: #fff5f5; padding: 15px; border-radius: 10px; border-left: 5px solid #f56565; margin-bottom: 10px;'>
            <small>🕒 {item['date_time']} | 👤 {item['sender']}</small><br><br>
            {item['deal_text']}
        </div>
        """, unsafe_allow_html=True)
        if item['wa_link']: st.markdown(f"[📲 WhatsApp Karein]({item['wa_link']})", unsafe_allow_html=True)
        with st.expander("👀 Poora Original Message Dekhein"):
            st.markdown(item['original_details'], unsafe_allow_html=True)

    render_bookmark_buttons(item, key_prefix)
    st.markdown("<hr>", unsafe_allow_html=True)

def generate_id(date_time, sender, text):
    unique_string = f"{date_time}_{sender}_{text}"
    return hashlib.md5(unique_string.encode()).hexdigest()

# ==========================================
# TABS BANANA
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Smart Search", "🤝 Deal Matcher", "📘 ShahJhan's Bookmarks", "📗 Touqeer's Bookmarks"])

# ------------------------------------------
# TAB 1: PEHLE WALA NORMAL SMART SEARCH
# ------------------------------------------
with tab1:
    st.markdown("### 🔍 General Search")
    user_query = st.text_input("Search:", placeholder="Ali block rent ya p3", key="search_input_tab1")

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
            seen_signatures = set() # Duplicates hatane ke liye memory set
            
            for idx, row in df.iterrows():
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
                        
                        if i == 0:
                            matched_chunks.append(f"<b>[Top Heading / Context]</b><br>{formatted_para}")
                        else:
                            matched_chunks.append(f"<b>[Matched Deal]</b><br>{formatted_para}")
                            
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
                    
                    # Deduplication Signature (Sender + Exact Deal Text)
                    # Agar same sender ne wahi text dobara bheja hai toh signature same hoga
                    clean_text_sig = re.sub(r'<[^>]*?>', '', matched_html).strip().lower()
                    signature = f"{sender}_{clean_text_sig}"
                    
                    if signature in seen_signatures:
                        continue # Agar pehle se maujood hai toh skip kar do (Duplicate hta do)
                    seen_signatures.add(signature)
                    
                    item_id = generate_id(date_time, sender, matched_html)
                    
                    matched_results.append({
                        'id': item_id,
                        'date_time': date_time,
                        'sender': sender,
                        'deal_text': matched_html,
                        'wa_link': wa_link,
                        'original_details': highlighted_original_details,
                        'source_tab': 'tab1'
                    })
            
            if not matched_results:
                st.warning("❌ Aapke keywords wala koi record nahi mila.")
            else:
                st.success(f"🎉 Qamyabi! {len(matched_results)} unique matching records mil gaye hain:")
                for match_idx, item in enumerate(matched_results[:100], 1):
                    render_deal_ui(item, f"t1_{match_idx}", match_idx)

# ------------------------------------------
# TAB 2: DEAL MATCHER (Required vs Available)
# ------------------------------------------
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
            seen_signatures_tab2 = set() # Matcher ke liye duplicate filter
            required_keywords = r'\b(need|require|required|chahiye|chahye|looking|buyer|client)\b'
            
            for idx, row in df.iterrows():
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
                        
                        matched_chunks_data.append({
                            'deal_text': formatted_para,
                            'is_required': is_required
                        })
                    else:
                        formatted_full_message_paragraphs.append(para.replace('\n', '<br>'))
                        
                if matched_chunks_data:
                    highlighted_original_details = "<br><br>".join(formatted_full_message_paragraphs)
                    wa_link = get_clean_whatsapp(f"{sender} {details}")
                    
                    for m_data in matched_chunks_data:
                        clean_text_sig = re.sub(r'<[^>]*?>', '', m_data['deal_text']).strip().lower()
                        signature = f"{sender}_{clean_text_sig}"
                        
                        if signature in seen_signatures_tab2:
                            continue # Duplicate skip
                        seen_signatures_tab2.add(signature)
                        
                        item_id = generate_id(date_time, sender, m_data['deal_text'])
                        deal_dict = {
                            'id': item_id,
                            'date_time': date_time,
                            'sender': sender,
                            'deal_text': m_data['deal_text'],
                            'wa_link': wa_link,
                            'original_details': highlighted_original_details,
                            'source_tab': 'tab2_req' if m_data['is_required'] else 'tab2_avail'
                        }
                        if m_data['is_required']: required_deals.append(deal_dict)
                        else: available_deals.append(deal_dict)

            col_avail, col_req = st.columns(2)
            
            with col_avail:
                st.markdown("### 🟢 Available (Supply)")
                if not available_deals: st.info("Koi 'Available' deal nahi mili.")
                else:
                    for i, item in enumerate(available_deals[:25]):
                        render_deal_ui(item, f"t2a_{i}")

            with col_req:
                st.markdown("### 🔴 Required (Demand)")
                if not required_deals: st.info("Koi 'Required' (Demand) deal nahi mili.")
                else:
                    for i, item in enumerate(required_deals[:25]):
                        render_deal_ui(item, f"t2r_{i}")

# ------------------------------------------
# TAB 3: SHAHJHAN'S BOOKMARKS
# ------------------------------------------
with tab3:
    st.markdown("### 📘 ShahJhan's Bookmarks")
    if not st.session_state.shahjhan_bm:
        st.info("Abhi tak aapne koi deal bookmark nahi ki.")
    else:
        for i, item in enumerate(reversed(list(st.session_state.shahjhan_bm.values()))):
            render_deal_ui(item, f"bm_sj_{i}", i + 1)

# ------------------------------------------
# TAB 4: TOUQEER'S BOOKMARKS
# ------------------------------------------
with tab4:
    st.markdown("### 📗 Touqeer's Bookmarks")
    if not st.session_state.touqeer_bm:
        st.info("Abhi tak aapne koi deal bookmark nahi ki.")
    else:
        for i, item in enumerate(reversed(list(st.session_state.touqeer_bm.values()))):
            render_deal_ui(item, f"bm_tq_{i}", i + 1)
