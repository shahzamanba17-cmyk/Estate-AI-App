import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Bahria Town Smart Search", page_icon="🏠", layout="centered")
st.title("🏠 Bahria Town Smart Search Bot")
st.write("Clean, fast and exact-keyword search bot.")

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

# Clean WhatsApp Direct Number Extractor (Only valid mobile numbers)
def get_clean_whatsapp(text):
    # Pakistani phone numbers (jaise 03001234567 ya +923001234567)
    phone_pattern = r'(?:\+92|0)?(3[0-9]{9})'
    match = re.search(phone_pattern, text)
    if match:
        num = '92' + match.group(1)
        return f"https://wa.me/{num}"
    return None

# User Input
user_query = st.text_input("Yahan apna exact keyword likhein (Jaise: Ali block rent):")

if st.button("🔍 Search Karein"):
    if not user_query.strip():
        st.warning("⚠️ Pehle kuch likhein toh sahi!")
    elif df.empty:
        st.warning("⚠️ Data available nahi hai.")
    else:
        with st.spinner("Talaash ki ja rahi hai..."):
            # Bilkul exact keywords jo user ne likhe hon (No automatic wrong alterations)
            query_terms = [term.lower() for term in user_query.split()]
            
            matched_results = []
            
            for idx, row in df.iterrows():
                date_time = row.get('Date & Time', 'N/A')
                sender = row.get('Sender / Contact', row.get('Source/Sender', 'N/A'))
                details = str(row.get('Message Details', row.to_dict()))
                
                lines = details.split('\n')
                
                for line in lines:
                    line_lower = line.lower()
                    # Check karein ke user ke diye gaye saare keywords is line mein mojood hon
                    if all(term in line_lower for term in query_terms):
                        matched_results.append({
                            'date_time': date_time,
                            'sender': sender,
                            'matched_line': line.strip(),
                            'full_text': f"{sender} {details}"
                        })
            
            if not matched_results:
                st.warning("❌ Aapke keywords wali koi exact line nahi mili.")
            else:
                st.success(f"🎉 Qamyabi! {len(matched_results)} matching records mil gaye hain:")
                st.markdown("---")
                
                for match_idx, item in enumerate(matched_results[:50], 1):
                    line_text = item['matched_line']
                    wa_link = get_clean_whatsapp(item['full_text'])
                    
                    with st.container():
                        st.markdown(f"### **Record #{match_idx}**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"🕒 **Waqt:** {item['date_time']}")
                        with col2:
                            st.markdown(f"👤 **Source:** {item['sender']}")
                        
                        st.info(f"📌 **Detail:**\n\n{line_text}")
                        
                        # Agar saaf suthra phone number mila toh button do, warna nahi
                        if wa_link:
                            st.markdown(f"[📲 Is Number par WhatsApp Chat Kholein]({wa_link})", unsafe_allow_html=True)
                        
                        st.markdown("---")
