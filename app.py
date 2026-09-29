import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Bahria Town Smart Search", page_icon="🏠", layout="centered")
st.title("🏠 Bahria Town Smart Search Bot")
st.write("Smart Python Search with Auto-Synonym & WhatsApp Direct Links.")

# Aapki Asli / Original Google Sheet ki ID
SHEET_ID = "1GmJcTrkHQwF6m33c4xbJI9pG7XyR7nn39ZOUeGcH86Y"

# Cache clear karne ka button
if st.button("🔄 Data Refresh Karein (Clear Cache)"):
    st.cache_data.clear()
    st.success("Cache clear ho gaya! Naya data load ho raha hai.")

# Data load karne ka function
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

if df.empty:
    st.error("⚠️ Data load nahi hua! Google Sheet ki 'Share' settings 'Anyone with the link can view' par check karein.")
else:
    st.success(f"✅ Total {len(df)} records load ho gaye hain (Naye se Purane ki tarah sorted).")

# Smart Synonym Extractor
def expand_query_terms(query):
    terms = query.lower().split()
    expanded = set(terms)
    
    for term in terms:
        if term in ['block', 'bloc', 'blk']:
            expanded.update(['block', 'bloc', 'blk'])
        elif term in ['precinct', 'p', 'prec']:
            expanded.update(['precinct', 'p', 'prec', 'p-'])
        elif term in ['rent', 'rental']:
            expanded.update(['rent', 'rental'])
        elif term in ['sale', 'selling']:
            expanded.update(['sale', 'selling', 'for sale'])
        elif term in ['corner', 'c/nr']:
            expanded.update(['corner', 'c/nr'])
            
    return list(expanded)

# Helper function to get clean WhatsApp Direct Chat or Group Link
def get_whatsapp_info(text):
    # Pehle check karein agar text mein koi direct WhatsApp group link (`chat.whatsapp.com`) mojood hai
    group_link_match = re.search(r'https?://chat\.whatsapp\.com/[A-Za-z0-9]+', text)
    if group_link_match:
        return group_link_match.group(0), "Group Link"
    
    # Agar group link na ho, toh personal phone number dhoond kar direct chat link banayein
    phone_pattern = r'(?:\+92|0)?3[0-9]{9}'
    match = re.search(phone_pattern, text)
    if match:
        num = match.group(0)
        if num.startswith('0'):
            num = '92' + num[1:]
        elif not num.startswith('92'):
            num = '92' + num
        return f"https://wa.me/{num}", "Direct Number"
        
    return None, None

# User Input
user_query = st.text_input("Yahan apna keyword likhein (Jaise: Ali block rent, P12 corner):")

if st.button("🔍 Search Karein"):
    if not user_query.strip():
        st.warning("⚠️ Pehle kuch likhein toh sahi!")
    elif df.empty:
        st.warning("⚠️ Data available nahi hai.")
    else:
        with st.spinner("Smart spelling aur variations ke sath talaash jari hai..."):
            query_terms = expand_query_terms(user_query)
            
            matched_results = []
            
            for idx, row in df.iterrows():
                date_time = row.get('Date & Time', 'N/A')
                sender = row.get('Sender / Contact', row.get('Source/Sender', 'N/A'))
                details = str(row.get('Message Details', row.to_dict()))
                
                lines = details.split('\n')
                
                for line in lines:
                    line_lower = line.lower()
                    if any(term in line_lower for term in query_terms):
                        matched_results.append({
                            'date_time': date_time,
                            'sender': sender,
                            'matched_line': line.strip(),
                            'full_row_text': f"{sender} {details}"
                        })
            
            if not matched_results:
                st.warning("❌ Aapke keywords wali koi exact line nahi mili.")
            else:
                st.success(f"🎉 Qamyabi! {len(matched_results)} matching records mil gaye hain (Showing up to 50):")
                st.markdown("---")
                
                for match_idx, item in enumerate(matched_results[:50], 1):
                    line_text = item['matched_line']
                    full_text = item['full_row_text']
                    
                    wa_url, wa_type = get_whatsapp_info(full_text)
                    
                    with st.container():
                        st.markdown(f"### **Record #{match_idx}**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"🕒 **Waqt:** {item['date_time']}")
                        with col2:
                            st.markdown(f"👤 **Source:** {item['sender']}")
                        
                        st.info(f"📌 **Detail:**\n\n{line_text}")
                        
                        # Link type ke hisab se button dikhana
                        if wa_url:
                            if wa_type == "Group Link":
                                st.markdown(f"[🔗 WhatsApp Group Link Kholein]({wa_url})", unsafe_allow_html=True)
                            else:
                                st.markdown(f"[📲 Is Number par WhatsApp Chat Kholein]({wa_url})", unsafe_allow_html=True)
                        
                        st.markdown("---")
