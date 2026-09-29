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
except:
    st.error("API Key missing! Streamlit secrets mein GEMINI_API_KEY daalein.")

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

@st.cache_data(ttl=3600) 
def load_all_data():
    all_data = []
    for sheet_id in SHEET_IDS:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            df = pd.read_csv(url)
            all_data.append(df)
        except Exception as e:
            continue
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

with st.spinner("Data Load ho raha hai..."):
    df = load_all_data()

user_query = st.text_input("Aapka sawal (Jaise: P1 mein rent ke liye kya hai?):")

if st.button("Dhoondo"):
    if user_query and not df.empty:
        with st.spinner("AI aapke 10,000 messages parh raha hai..."):
            keywords = user_query.lower().replace('mein', '').replace('ke', '').replace('liye', '').replace('kya', '').replace('hai', '').split()
            mask = df.astype(str).apply(lambda x: x.str.lower().str.contains('|'.join(keywords), na=False)).any(axis=1)
            filtered_df = df[mask].head(100) 
            
            if filtered_df.empty:
                st.warning("Aapke sawal ke mutabiq 10 files mein koi data nahi mila.")
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
    else:
        st.warning("Bhai koi sawal to likho!")
