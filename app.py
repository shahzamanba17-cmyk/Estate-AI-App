import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Bahria Town Smart Search", page_icon="🏠", layout="centered")
st.title("🏠 Bahria Town Smart Search Bot")
st.write("Super-fast, AI-free Python search with clean organized output.")

# Aapki Data Sheets ki IDs
SHEET_IDS = [
    "139c3ogaD0-5YruC_t4lXZbM7_R4DAITsctnknOdKnaQ", 
    "1xQtra6SEx3_s_pytJtauVySGesOJ9OjVpNjV5Xlg04g"
]

# Cache clear karne ka button
if st.button("🔄 Data Refresh Karein (Clear Cache)"):
    st.cache_data.clear()
    st.success("Cache clear ho gaya! Naya data load ho raha hai.")

# Data load karne ka function
@st.cache_data(ttl=3600) 
def load_all_data():
    all_data = []
    for sheet_id in SHEET_IDS:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(url)
            if not df.empty:
                all_data.append(df)
        except Exception:
            continue
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # Date & Time ke mutabiq New to Old sort karna (Latest sab se upar)
        if 'Date & Time' in combined_df.columns:
            combined_df['Parsed_Date'] = pd.to_datetime(combined_df['Date & Time'], errors='coerce')
            combined_df = combined_df.sort_values(by='Parsed_Date', ascending=False)
        return combined_df
    return pd.DataFrame()

with st.spinner("Data load ho raha hai..."):
    df = load_all_data()

if df.empty:
    st.error("⚠️ Data load nahi hua! Sheets ki 'Share' settings check karein.")
else:
    st.success(f"✅ Total {len(df)} records load ho gaye hain (Naye se Purane ki tarah sorted).")

# User Input
user_query = st.text_input("Yahan apna keyword likhein (Jaise: sports city villa sale):")

if st.button("🔍 Search Karein"):
    if not user_query.strip():
        st.warning("⚠️ Pehle kuch likhein toh sahi!")
    elif df.empty:
        st.warning("⚠️ Data available nahi hai.")
    else:
        with st.spinner("Talaash aur formatting ki ja rahi hai..."):
            query_terms = [term.lower() for term in user_query.split()]
            
            matched_results = []
            
            for idx, row in df.iterrows():
                date_time = row.get('Date & Time', 'N/A')
                sender = row.get('Sender / Contact', row.get('Source/Sender', 'N/A'))
                details = str(row.get('Message Details', row.to_dict()))
                
                # Message ko lines mein torna
                lines = details.split('\n')
                
                for line in lines:
                    line_lower = line.lower()
                    # Check karein ke kya is line mein user ke diye gaye saare keywords hain
                    if all(term in line_lower for term in query_terms):
                        # Clean text formatting (Extracting phone numbers or prices if possible)
                        matched_results.append({
                            'date_time': date_time,
                            'sender': sender,
                            'matched_line': line.strip()
                        })
            
            if not matched_results:
                st.warning("❌ Aapke keywords wali koi exact line nahi mili.")
            else:
                st.success(f"🎉 Qamyabi! {len(matched_results)} organized records mil gaye hain:")
                st.markdown("---")
                
                for match_idx, item in enumerate(matched_results[:30], 1):
                    # Smart formatting of the matched line to look like an organized card
                    line_text = item['matched_line']
                    
                    with st.container():
                        st.markdown(f"### **Record #{match_idx}**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"🕒 **Waqt:** {item['date_time']}")
                        with col2:
                            st.markdown(f"👤 **Source:** {item['sender']}")
                        
                        # Displaying as a neat highlighted card
                        st.info(f"📌 **Detail:**\n\n{line_text}")
                        st.markdown("---")
