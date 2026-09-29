import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Deal", page_icon="🏠", layout="centered")

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
    if st.button("🔄"):
        st.cache_data.clear()
        st.rerun()

if df.empty:
    st.error("⚠️ Data load nahi hua! Google Sheet ki 'Share' settings check karein.")
else:
    st.markdown(f"🟢 **{len(df)}**")

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

user_query = st.text_input("Search:", placeholder="Ali block rent ya p3")

if st.button("🔍 Search Karein"):
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
                
                # 1. Message ko Chunks (Deals) mein todna
                paragraphs = re.split(r'\n\s*\n', details)
                if not paragraphs:
                    continue
                
                # 2. Header Inheritance: Top Heading ko yaad rakhna
                header_chunk = paragraphs[0]
                header_lower = header_chunk.lower()
                
                matched_chunks = []
                formatted_full_message_paragraphs = []
                
                # 3. Har paragraph (deal) ko alag check karna
                for i, para in enumerate(paragraphs):
                    para_lower = para.lower()
                    
                    chunk_match = True
                    for pattern in search_patterns:
                        if not (re.search(pattern, para_lower) or re.search(pattern, header_lower)):
                            chunk_match = False
                            break
                    
                    # Agar yeh makhsoos deal match ho gayi
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
                            
                        # Matching deal ko highlight ke sath full message list mein daalna
                        formatted_full_message_paragraphs.append(formatted_para)
                    else:
                        # Jo deal match nahi hui usay BINA highlight kiye full message list mein daalna
                        formatted_full_message_paragraphs.append(para.replace('\n', '<br>'))

                # Agar kisi bhi chunk (deal) mein match mil gaya toh record save karein
                if matched_chunks:
                    matched_html = "<br><br>".join(matched_chunks)
                    
                    if not any("[Top Heading" in chunk for chunk in matched_chunks):
                        header_html = f"<div style='color: gray; font-size: 0.9em;'><i>Context (Shuru Ki Line):<br>{header_chunk.replace(chr(10), '<br>')}</i></div><br>"
                        matched_html = header_html + matched_html

                    # Poora original message sirf matched deals ke highlights ke sath
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
                st.markdown("---")
                
                for match_idx, item in enumerate(matched_results[:50], 1):
                    wa_link = get_clean_whatsapp(item['full_text'])
                    
                    with st.container():
                        st.markdown(
                            f"<h3 style='text-align: center;'><span style='background-color: #d4edda; color: #155724; padding: 4px 12px; border-radius: 6px; border: 1px solid #c3e6cb;'>Record #{match_idx}</span></h3>", 
                            unsafe_allow_html=True
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"🕒 **Waqt:** {item['date_time']}")
                        with col2:
                            st.markdown(f"👤 **Source:** {item['sender']}")
                        
                        st.markdown(f"📌 **Relevant Deals:**<br>{item['matched_html']}", unsafe_allow_html=True)
                        
                        if wa_link:
                            st.markdown(f"[📲 Is Number par WhatsApp Chat Kholein]({wa_link})", unsafe_allow_html=True)
                        
                        with st.expander("👀 Poora Original Message Dekhein (Show Full List)"):
                            st.markdown(item['original_details'], unsafe_allow_html=True)
                        
                        st.markdown("---")
