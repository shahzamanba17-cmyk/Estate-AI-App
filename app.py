import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="My Real Estate AI", page_icon="🏠")
st.title("🏠 Bahria Town Estate AI Bot")
st.write("Aapki 10 Data Sheets se automatic details nikalne wala bot.")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"API Key ka masla: {e}")

SHEET_IDS = [
    "1mO238GbhkbEaGQ3zH5WxPWhiGFG-kp6rue6GRRPNmRE", 
    "1bcI0mKunqWKlMOf7mGPI7bYv1nWQ9mf7B86mem9bEYk", 
    "1iWqHyhlV--MJG3DsALwr08HG1OEWutU4V8Exv9Pf0uk", 
    "1A8nEQxtQYb6psr3YVcATHqKqF3YJaSN6LUbvQkxdeE8", 
    "1ICdBBGQnhV6SBdBqg00aIdvif27uYiVcZ39IJFjLYXc", 
    "1d7LqnZGRU5Rie5ceA1lM4ikgI3z9MOCGfxnJUvuuPiA", 
    "17ciRHIb20PiRy0g1Sw4RbrILBV7vE28KTKc3KNwi2i8", 
    "1P9PQfmEy_hByNgPwkKLOb1lImCRVMkHmZmTxQhE5CzE", 
    "1JioDEgPs1O9Px1twCqoU3ozhl-Vf1nfJIuvVGOainW4", 
    "1nNPySuzz8dInRWx9AZaC4Deumg4VM8XioP3BojuNj34"
]

# Naya Button: Cache clear karne ke liye
if st.button("🔄 Data Refresh Karein (Clear Cache)"):
    st.cache_data.clear()
    st.success("Cache clear ho gaya! Ab app naya data read karegi.")

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

with st.spinner("Data Load ho raha hai..."):
    df, sheets_count = load_all_data()

# Data load check
if df.empty:
    st.error("⚠️ Data load nahi hua! Ya toh sheets khali hain, ya unki 'Share' settings mein 'Anyone with the link' nahi kiya hua.")
else:
    st.success(f"✅ {sheets_count} sheets se Data kamyabi se load ho gaya hai (Total Rows: {len(df)}).")

user_query = st.text_input("Aapka sawal (Jaise: P1 mein rent ke liye kya hai?):")

if st.button("Dhoondo"):
    # Ab errors alag alag aayenge
    if not user_query:
        st.warning("⚠️ Bhai koi sawal to likho!")
    elif df.empty:
        st.warning("⚠️ Data access nahi ho raha, pehle upar Data Refresh karein.")
    else:
        with st.spinner("AI aapke messages parh raha hai..."):
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
                response = model.generate_content(prompt)
                
                st.success("Jawab Mil Gaya!")
                st.markdown(response.text)
