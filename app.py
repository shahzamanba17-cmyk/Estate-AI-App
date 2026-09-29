import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bahria Town Smart Search", page_icon="🏠", layout="centered")
st.title("🏠 Bahria Town Smart Search Bot")
st.write("Aapke messages se exact matching details nikalne wala smart bot.")

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
user_query = st.text_input("Yahan apna keyword likhein (Jaise: Ali block rent corner):")

if st.button("🔍 Search Karein"):
    if not user_query.strip():
        st.warning("⚠️ Pehle kuch likhein toh sahi!")
    elif df.empty:
        st.warning("⚠️ Data available nahi hai.")
    else:
        with st.spinner("Exact matching lines talaash kiye ja rahe hain..."):
            query_terms = [term.lower() for term in user_query.split()]
            
            # Hum aik nayi list banayenge jo sirf exact matching lines ko store karegi
            matched_results = []
            
            for idx, row in df.iterrows():
                date_time = row.get('Date & Time', 'N/A')
                sender = row.get('Sender / Contact', row.get('Source/Sender', 'N/A'))
                details = str(row.get('Message Details', row.to_dict()))
                
                # Message ko alag alag lines ya paragraphs mein torna
                lines = details.split('\n')
                
                for line in lines:
                    line_lower = line.lower()
                    # Check karein ke kya is aik hi line mein USER ke diye gaye SAARE keywords mojood hain
                    if all(term in line_lower for term in query_terms):
                        matched_results.append({
                            'date_time': date_time,
                            'sender': sender,
                            'matched_line': line.strip()
                        })
            
            if not matched_results:
                st.warning("❌ Aapke saare keywords wali koi exact line ya post nahi mili.")
            else:
                st.success(f"🎉 Qamyabi! {len(matched_results)} exact matching details mil gayi hain:")
                st.markdown("---")
                
                for match_idx, item in enumerate(matched_results[:30], 1):
                    with st.container():
                        st.markdown(f"### **Record #{match_idx}**")
                        st.markdown(f"**Date & Time:** {item['date_time']}")
                        st.markdown(f"**Source/Sender:** {item['sender']}")
                        st.markdown(f"**Matching Detail:**\n> **{item['matched_line']}**")
                        st.markdown("---")
