import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Deal", page_icon="🏠", layout="wide") # Layout wide kar diya taake 2 columns achay lagin

st.title("Deal")
st.markdown('<meta name="robots" content="noindex, nofollow">', unsafe_allow_html=True)

# Aapki Asli / Original Google Sheet ki ID
SHEET_ID = "1GmJcTrkHQwF6m33c4xbJI9pG7XyR7nn39ZOUeGcH86Y"

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
    if st.button("🔄 Refresh"):
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
# TABS BANANA (Search aur Matcher ke liye)
# ==========================================
tab1, tab2 = st.tabs(["🔍 Smart Search", "🤝 Deal Matcher (Demand & Supply)"])

# ------------------------------------------
# TAB 1: PEHLE WALA NORMAL SMART SEARCH
# ------------------------------------------
with tab1:
    st.markdown("### 🔍 General Search")
    user_query = st.text_input("Search:", placeholder="Ali block rent ya p3", key="search_tab1")

    if st.button("🔍 Search Karein", key="btn_tab1"):
        if not user_query.strip():
            st.warning("⚠️ Pehle kuch likhein toh sahi!")
        elif df.empty:
            st.warning("⚠️ Data available nahi hai.")
        else:
            with st.spinner("Talaash ki ja rahi hai..."):
                search_patterns = get_search_patterns(user_query)
                matched_results = []
                
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

                        matched_results.append({
                            'date_time': date_time,
                            'sender': sender,
                            'matched_html': matched_html,
                            'full_text': f"{sender} {details}",
                            'original_details': highlighted_original_details 
                        })
                
                if not matched_results:
                    st.warning("❌ Aapke keywords wala koi record nahi mila.")
                else:
                    st.success(f"🎉 Qamyabi! {len(matched_results)} matching records mil gaye hain:")
                    for match_idx, item in enumerate(matched_results[:50], 1):
                        wa_link = get_clean_whatsapp(item['full_text'])
                        with st.container():
                            st.markdown(f"### <span style='background-color: #d4edda; color: #155724; padding: 4px 12px; border-radius: 6px;'>Record #{match_idx}</span>", unsafe_allow_html=True)
                            col1, col2 = st.columns(2)
                            with col1: st.markdown(f"🕒 **Waqt:** {item['date_time']}")
                            with col2: st.markdown(f"👤 **Source:** {item['sender']}")
                            
                            st.markdown(f"📌 **Relevant Deals:**<br>{item['matched_html']}", unsafe_allow_html=True)
                            
                            if wa_link:
                                st.markdown(f"[📲 Is Number par WhatsApp Chat Kholein]({wa_link})", unsafe_allow_html=True)
                            
                            with st.expander("👀 Poora Original Message Dekhein (Show Full List)"):
                                st.markdown(item['original_details'], unsafe_allow_html=True)
                            st.markdown("---")

# ------------------------------------------
# TAB 2: DEAL MATCHER (Required vs Available)
# ------------------------------------------
with tab2:
    st.markdown("### 🤝 Aamne-Samne Matcher (Demand vs Supply)")
    st.info("Yahan sirf property ka naam likhein (e.g., 'Ali block villa'). Bot khud 'Required' aur 'Available' ko alag alag columns mein dikhayega!")
    
    match_query = st.text_input("Property to Match:", placeholder="e.g., Ali block villa", key="search_tab2")

    if st.button("🤝 Match Deals", key="btn_tab2"):
        if not match_query.strip():
            st.warning("⚠️ Pehle kuch likhein toh sahi!")
        elif df.empty:
            st.warning("⚠️ Data available nahi hai.")
        else:
            with st.spinner("Deals match ki ja rahi hain..."):
                search_patterns = get_search_patterns(match_query)
                
                # Do alag lists banayenge (Required aur Available ke liye)
                required_deals = []
                available_deals = []
                
                # Required words list (agar in mein se koi word aaye toh wo demand/required mani jayegi)
                required_keywords = r'\b(need|require|required|chahiye|chahye|looking|buyer|client)\b'
                
                for idx, row in df.iterrows():
                    date_time = row.get('Date & Time', 'N/A')
                    sender = row.get('Sender / Contact', row.get('Source/Sender', 'N/A'))
                    details = str(row.get('Message Details', row.to_dict())).strip()
                    
                    paragraphs = re.split(r'\n\s*\n', details)
                    if not paragraphs: continue
                    
                    header_chunk = paragraphs[0]
                    header_lower = header_chunk.lower()
                    
                    for i, para in enumerate(paragraphs):
                        para_lower = para.lower()
                        chunk_match = True
                        
                        for pattern in search_patterns:
                            if not (re.search(pattern, para_lower) or re.search(pattern, header_lower)):
                                chunk_match = False
                                break
                        
                        if chunk_match and search_patterns:
                            # Highlight the keywords
                            lines = para.split('\n')
                            hl_lines = []
                            for line in lines:
                                if any(re.search(p, line.lower()) for p in search_patterns):
                                    hl_lines.append(f"<mark style='background-color: #fff3cd; color: #000; padding: 2px 4px; border-radius: 3px;'>{line.strip()}</mark>")
                                else:
                                    hl_lines.append(line.strip())
                            
                            formatted_para = "<br>".join(hl_lines)
                            
                            deal_data = {
                                'date_time': date_time,
                                'sender': sender,
                                'deal_text': formatted_para,
                                'wa_link': get_clean_whatsapp(f"{sender} {details}")
                            }
                            
                            # Decide karna ke deal Required hai ya Available
                            is_required = bool(re.search(required_keywords, para_lower) or re.search(required_keywords, header_lower))
                            
                            if is_required:
                                required_deals.append(deal_data)
                            else:
                                available_deals.append(deal_data)

                # Screen ko 2 hisson (Columns) mein todna
                col_avail, col_req = st.columns(2)
                
                # COLUMN 1: AVAILABLE
                with col_avail:
                    st.markdown("### 🟢 Available (Supply)")
                    if not available_deals:
                        st.info("Koi 'Available' deal nahi mili.")
                    else:
                        for item in available_deals[:25]:
                            st.markdown(f"""
                            <div style='background-color: #f0fff4; padding: 15px; border-radius: 10px; border-left: 5px solid #48bb78; margin-bottom: 10px;'>
                                <small>🕒 {item['date_time']} | 👤 {item['sender']}</small><br><br>
                                {item['deal_text']}
                            </div>
                            """, unsafe_allow_html=True)
                            if item['wa_link']:
                                st.markdown(f"[📲 WhatsApp Karein]({item['wa_link']})", unsafe_allow_html=True)
                            st.markdown("<hr>", unsafe_allow_html=True)

                # COLUMN 2: REQUIRED
                with col_req:
                    st.markdown("### 🔴 Required (Demand)")
                    if not required_deals:
                        st.info("Koi 'Required' (Demand) deal nahi mili.")
                    else:
                        for item in required_deals[:25]:
                            st.markdown(f"""
                            <div style='background-color: #fff5f5; padding: 15px; border-radius: 10px; border-left: 5px solid #f56565; margin-bottom: 10px;'>
                                <small>🕒 {item['date_time']} | 👤 {item['sender']}</small><br><br>
                                {item['deal_text']}
                            </div>
                            """, unsafe_allow_html=True)
                            if item['wa_link']:
                                st.markdown(f"[📲 WhatsApp Karein]({item['wa_link']})", unsafe_allow_html=True)
                            st.markdown("<hr>", unsafe_allow_html=True)
