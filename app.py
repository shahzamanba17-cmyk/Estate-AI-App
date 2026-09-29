import streamlit as st
import pandas as pd
from google import genai

st.set_page_config(page_title="My Real Estate AI", page_icon="🏠")
st.title("🏠 Bahria Town Estate AI Bot")
st.write("Aapki Data Sheets se automatic details nikalne wala bot.")

# API Key aur Client Setup
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"API Key ka masla: {e}")

# Aapki Data Sheets ki IDs
SHEET_IDS = [
    "139c3ogaD0-5YruC_t4lXZbM7_R4DAITsctnknOdKnaQ", 
    "1xQtra6SEx3_s_pytJtauVySGesOJ9OjVpNjV5Xlg04g"
]

# Cache clear karne ka button
if st.button("🔄 Data Refresh Karein (Clear Cache)"):
    st.cache_data.clear()
    st.success("Cache clear ho gaya! Ab app naya data read karegi.")

# Data load karne ka function
@st.cache_data(ttl=3600) 
def load_all_data():
    all_data = []
    loaded_sheets = 0
    for sheet_id in SHEET_IDS:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(url)
            if not df.empty:
                all_data.append(df)
                loaded_sheets += 1
        except Exception as e:
            continue
    
    if all_data:
        return pd.concat(all_data, ignore_index=True), loaded_sheets
    return pd.DataFrame(), 0

# Data Loading status
with st.spinner("Data Load ho raha hai..."):
    df, sheets_count = load_all_data()

if df.empty:
    st.error("⚠️ Data load nahi hua! Ya toh sheets khali hain, ya unki 'Share' settings mein 'Anyone with the link' nahi kiya hua.")
else:
    st.success(f"✅ {sheets_count} sheets se Data kamyabi se load ho gaya hai (Total Rows: {len(df)}).")

# Search Section
user_query = st.text_input("Aapka sawal (Jaise: P1 mein rent ke liye kya hai?):")

if st.button("Dhoondo"):
    if not user_query:
        st.warning("⚠️ Bhai koi sawal to likho!")
    elif df.empty:
        st.warning("⚠️ Data access nahi ho raha, pehle upar 'Data Refresh' button dabayen.")
    else:
        with st.spinner("AI aapke messages parh raha hai..."):
            # Filtering Data
            keywords = user_query.lower().replace('mein', '').replace('ke', '').replace('liye', '').replace('kya', '').replace('hai', '').split()
            mask = df.astype(str).apply(lambda x: x.str.lower().str.contains('|'.join(keywords), na=False)).any(axis=1)
            filtered_df = df[mask].head(100) 
            
            if filtered_df.empty:
                st.warning("Aapke sawal ke mutabiq sheets mein koi record nahi mila.")
            else:
                data_text = filtered_df.to_csv(index=False)
                prompt = f"""
                Tum ek expert Real Estate assistant ho. 
                User ka sawal: '{user_query}'
                
                Niche user ki excel sheets ka filter kiya hua data hai:
                {data_text}
                
                Is data ko parh kar bilkul NotebookLM ki tarah ek mukammal, point-to-point Roman Urdu/Hindi mein summary do. 
                Rent, location, demand, aur contact number zaroor shamil karna. 
                Agar data mein jawab nahi hai toh bata dena.
                """
                
                # Correct model name: gemini-1.5-flash
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                )
                
                st.success("Jawab Mil Gaya!")
                st.markdown(response.text)
