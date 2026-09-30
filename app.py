import streamlit as st
import pandas as pd
import re
import hashlib
import datetime

st.set_page_config(page_title="Deal", page_icon="🏠", layout="wide") 

# ==========================================
# CUSTOM CSS FOR MOBILE SCROLLBAR
# ==========================================
st.markdown("""
<style>
/* Mobile par scrollbar ko mota aur pakarne mein asan banane ke liye */
::-webkit-scrollbar {
    width: 16px !important; 
    height: 16px !important;
}
::-webkit-scrollbar-track {
    background: #f1f1f1 !important; 
}
::-webkit-scrollbar-thumb {
    background: #888 !important; 
    border-radius: 8px !important;
    border: 3px solid #f1f1f1 !important;
}
::-webkit-scrollbar-thumb:hover {
    background: #555 !important; 
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Deal</h1>", unsafe_allow_html=True)
st.markdown('<meta name="robots" content="noindex, nofollow">', unsafe_allow_html=True)

# Aapki Asli / Original Google Sheet ki ID
SHEET_ID = "1GmJcTrkHQwF6m33c4xbJI9pG7XyR7nn39ZOUeGcH86Y"

# ==========================================
# MEMORY SYSTEM (Search State)
# ==========================================
if 'search_active1' not in st.session_state:
    st.session_state.search_active1 = False
if 'last_query1' not in st.session_state:
    st.session_state.last_query1 = ""
if 'search_active2' not in st.session_state:
    st.session_state.search_active2 = False
if 'last_query2' not in st.session_state:
    st.session_state.last_query2 = ""

if 'show_all_expanders' not in st.session_state:
    st.session_state.show_all_expanders = False

def toggle_expanders():
    st.session_state.show_all_expanders = not st.session_state.show_all_expanders

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
    
    # ==========================================
    # DATE RANGE FILTER WITH QUICK TABS
    # ==========================================
    st.markdown("### 📅 Date Filter")
    
    quick_days = st.radio(
        "Quick Select:", 
        ["1D", "2D", "3D", "4D", "5D", "6D", "7D", "2W", "3W", "1M", "All Time", "Custom Range"], 
        horizontal=True
    )
    
    today = datetime.date.today()
    
    if quick_days == "1D":
        start_date, end_date = today, today
    elif quick_days == "2D":
        start_date, end_date = today - datetime.timedelta(days=1), today
    elif quick_days == "3D":
        start_date, end_date = today - datetime.timedelta(days=2), today
    elif quick_days == "4D":
        start_date, end_date = today - datetime.timedelta(days=3), today
    elif quick_days == "5D":
        start_date, end_date = today - datetime.timedelta(days=4), today
    elif quick_days == "6D":
        start_date, end_date = today - datetime.timedelta(days=5), today
    elif quick_days == "7D":
        start_date, end_date = today - datetime.timedelta(days=6), today
    elif quick_days == "2W":
        start_date, end_date = today - datetime.timedelta(days=14), today
    elif quick_days == "3W":
        start_date, end_date = today - datetime.timedelta(days=21), today
    elif quick_days == "1M":
        start_date, end_date = today - datetime.timedelta(days=30), today
    elif quick_days == "All Time":
        start_date = df['Parsed_Date'].min().date() if pd.notnull(df['Parsed_Date'].min()) else today
        end_date = today
    else: # Custom Range
        col_d1, col_d2 = st.columns(2)
        min_d = df['Parsed_Date'].min().date() if pd.notnull(df['Parsed_Date'].min()) else today - datetime.timedelta(days=30)
        with col_d1:
            start_date = st.date_input("Start Date", min_d)
        with col_d2:
            end_date = st.date_input("End Date", today)
            
    # Filter DataFrame based on dates
    mask = (df['Parsed_Date'].dt.date >= start_date) & (df['Parsed_Date'].dt.date <= end_date)
    df = df.loc[mask]
    
    st.markdown(f"**🎯 Filtered Records ({quick_days}): {len(df)}**")
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
# REUSABLE UI LOGIC (Bookmarks Removed)
# ==========================================
def render_deal_ui(item, record_num=None):
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
        
        with st.expander("👀 Poora Original Message Dekhein (Show Full List)", expanded=st.session_state.show_all_expanders):
            st.markdown(item['original_details'], unsafe_allow_html=True)
            
    elif item['source_tab'] == 'tab2_avail':
        st.markdown(f"""
        <div style='background-color: #f0fff4; padding: 15px; border-radius: 10px; border-left: 5px solid #48bb78; margin-bottom: 10px;'>
            <small>🕒 {item['date_time']} | 👤 {item['sender']}</small><br><br>
            {item['deal_text']}
        </div>
        """, unsafe_allow_html=True)
        if item['wa_link']: st.markdown(f"[📲 WhatsApp Karein]({item['wa_link']})", unsafe_allow_html=True)
        
        with st.expander("👀 Poora Original Message Dekhein", expanded=st.session_state.show_all_expanders):
            st.markdown(item['original_details'], unsafe_allow_html=True)
            
    elif item['source_tab'] == 'tab2_req':
        st.markdown(f"""
        <div style='background-color: #fff5f5; padding: 15px; border-radius: 10px; border-left: 5px solid #f56565; margin-bottom: 10px;'>
            <small>🕒 {item['date_time']} | 👤 {item['sender']}</small><br><br>
            {item['deal_text']}
        </div>
        """, unsafe_allow_html=True)
        if item['wa_link']: st.markdown(f"[📲 WhatsApp Karein]({item['wa_link']})", unsafe_allow_html=True)
        
        with st.expander("👀 Poora Original Message Dekhein", expanded=st.session_state.show_all_expanders):
            st.markdown(item['original_details'], unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

def generate_id(date_time, sender, text):
    unique_string = f"{date_time}_{sender}_{text}"
    return hashlib.md5(unique_string.encode()).hexdigest()

# ==========================================
# TABS BANANA (3 TABS: Search, Matcher, Analytics)
# ==========================================
tab1, tab2, tab3 = st.tabs(["🔍 Smart Search", "🤝 Deal Matcher", "📊 Analytics Dashboard"])

# ------------------------------------------
# TAB 1: SMART SEARCH
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
            seen_signatures = set()
            
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
                    
                    clean_text_sig = re.sub(r'<[^>]*?>', '', matched_html).strip().lower()
                    signature = f"{sender}_{clean_text_sig}"
                    
                    if signature in seen_signatures:
                        continue 
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
                
                btn_text = "🔼 Sab Messages Band Karein (Collapse All)" if st.session_state.show_all_expanders else "🔽 Sab Messages Kholein (Expand All)"
                st.button(btn_text, on_click=toggle_expanders, key="btn_exp_t1")
                
                for match_idx, item in enumerate(matched_results[:150], 1):
                    render_deal_ui(item, match_idx)

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
            seen_signatures_tab2 = set() 
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
                            continue 
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

            if available_deals or required_deals:
                btn_text2 = "🔼 Sab Messages Band Karein (Collapse All)" if st.session_state.show_all_expanders else "🔽 Sab Messages Kholein (Expand All)"
                st.button(btn_text2, on_click=toggle_expanders, key="btn_exp_t2")

            col_avail, col_req = st.columns(2)
            
            with col_avail:
                st.markdown("### 🟢 Available (Supply)")
                if not available_deals: st.info("Koi 'Available' deal nahi mili.")
                else:
                    for i, item in enumerate(available_deals[:25]):
                        render_deal_ui(item)

            with col_req:
                st.markdown("### 🔴 Required (Demand)")
                if not required_deals: st.info("Koi 'Required' (Demand) deal nahi mili.")
                else:
                    for i, item in enumerate(required_deals[:25]):
                        render_deal_ui(item)

# ------------------------------------------
# TAB 3: ANALYTICS DASHBOARD (New Deep Analytics)
# ------------------------------------------
with tab3:
    st.markdown("### 📊 Market Analytics Dashboard")
    
    if not df.empty:
        st.markdown("#### 📈 Daily Market Activity")
        daily_counts = df.groupby(df['Parsed_Date'].dt.date).size()
        st.line_chart(daily_counts)
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            # 1. Top Precincts
            st.markdown("#### 🏙️ Top 15 Active Precincts")
            precinct_pattern = r'(?i)\b(?:p-?|precinct\s*)(\d+)\b'
            extracted_p = df['Message Details'].astype(str).str.extractall(precinct_pattern)[0]
            if not extracted_p.empty:
                p_counts = extracted_p.value_counts().reset_index()
                p_counts.columns = ['Precinct', 'Mentions']
                p_counts['Precinct'] = 'P-' + p_counts['Precinct'].astype(str)
                st.bar_chart(p_counts.head(15).set_index('Precinct'))
            
            # 2. Property Type Analysis
            st.markdown("#### 🏠 Property Type Analysis")
            def get_prop_type(text):
                t = str(text).lower()
                types = []
                if re.search(r'\b(plot|files?)\b', t): types.append('Plot')
                if re.search(r'\b(villa|home|house)\b', t): types.append('Villa')
                if re.search(r'\b(apartment|flat|tower)\b', t): types.append('Apartment')
                if re.search(r'\b(commercial|shop|office)\b', t): types.append('Commercial')
                return types if types else ['Other']
            
            all_types = df['Message Details'].apply(get_prop_type).explode()
            st.bar_chart(all_types.value_counts())
            
            # 3. Demand vs Supply
            st.markdown("#### ⚖️ Demand vs Supply")
            req_keywords = r'\b(need|require|required|chahiye|chahye|looking|buyer|client)\b'
            def get_demand_supply(text):
                if re.search(req_keywords, str(text).lower()): 
                    return 'Required (Demand)'
                return 'Available (Supply)'
            
            ds_counts = df['Message Details'].apply(get_demand_supply).value_counts()
            st.bar_chart(ds_counts)

        with col_c2:
            # 4. Top Property Sizes
            st.markdown("#### 📐 Top Property Sizes")
            size_pattern = r'(?i)(\d{2,4})\s*(?:gaz|sq\s*yard|sqyd|sq\s*yds|yards|yard|sqft|sq\s*ft)'
            extracted_sizes = df['Message Details'].astype(str).str.extractall(size_pattern)[0]
            if not extracted_sizes.empty:
                s_counts = extracted_sizes.value_counts().reset_index()
                s_counts.columns = ['Size', 'Count']
                s_counts['Size'] = s_counts['Size'].astype(str) + ' Gaz/SqYd'
                st.bar_chart(s_counts.head(10).set_index('Size'))
            else:
                st.info("Size data available nahi hai.")
                
            # 5. Top Prime Features
            st.markdown("#### ⭐ Top Prime Features")
            def get_features(text):
                t = str(text).lower()
                feats = []
                if re.search(r'\b(west\s*open)\b', t): feats.append('West Open')
                if re.search(r'\b(park\s*face|park\s*facing)\b', t): feats.append('Park Face')
                if re.search(r'\b(corner|semi\s*corner)\b', t): feats.append('Corner')
                if re.search(r'\b(jinnah\s*face|jinnah\s*facing|jinnah\s*back)\b', t): feats.append('Jinnah Facing')
                if re.search(r'\b(main\s*boulevard|main\s*road)\b', t): feats.append('Main Road')
                return feats
            
            all_feats = df['Message Details'].apply(get_features).explode().dropna()
            if not all_feats.empty:
                st.bar_chart(all_feats.value_counts())
            else:
                st.info("No prime features found.")
                
            # 6. Construction Status
            st.markdown("#### 🏗️ Construction Status")
            def get_status(text):
                t = str(text).lower()
                status = []
                if re.search(r'\b(brand\s*new)\b', t): status.append('Brand New')
                if re.search(r'\b(grey\s*structure|gray\s*structure)\b', t): status.append('Grey Structure')
                if re.search(r'\b(furnished|fully\s*furnished)\b', t): status.append('Furnished')
                return status
            
            all_status = df['Message Details'].apply(get_status).explode().dropna()
            if not all_status.empty:
                st.bar_chart(all_status.value_counts())
            else:
                st.info("No status keywords found.")
                
    else:
        st.warning("Data available nahi hai.")
