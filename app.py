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
    return pd.DataFrame(), 0

with st.spinner("Data load ho raha hai..."):
    df = load_all_data()

if df.empty:
    st.error("⚠️ Data load nahi hua! Sheets ki 'Share' settings check karein.")
else:
    st.success(f"✅ Total {len(df)} records load ho gaye hain (Naye se Purane ki tarah sorted).")

# User Input
user_query = st.text_input("Yahan apna keyword likhein (Jaise: Ali block rent, corner villa, P8):")

if st.button("🔍 Search Karein"):
    if not user_query.strip():
        st.warning("⚠️ Pehle kuch likhein toh sahi!")
    elif df.empty:
        st.warning("⚠️ Data available nahi hai.")
    else:
        with st.spinner("Exact matching tukre talaash kiye ja rahe hain..."):
            query_terms = user_query.lower().split()
            
            # Filter rows containing all keywords
            mask = pd.Series([True] * len(df))
            for term in query_terms:
                term_mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(term, na=False)).any(axis=1)
                mask = mask & term_mask
            
            filtered_df = df[mask].head(30) # Top 30 relevant results
            
            if filtered_df.empty:
                st.warning("❌ Aapke search ke mutabiq koi record nahi mila.")
            else:
                st.success(f"🎉 Qamyabi! {len(filtered_df)} matching posts mil gayi hain:")
                st.markdown("---")
                
                match_count = 0
                for idx, row in filtered_df.iterrows():
                    # Poori row ke text ko lines mein tornay ke liye
                    row_text = str(row.to_dict())
                    lines = [line.strip() for line in row_text.split('\n') if line.strip()]
                    
                    # Sirf woh line ya hissa nikalna jo keyword se match karta ho
                    matching_snippets = []
                    for line in lines:
                        if any(term in line.lower() for term in query_terms):
                            matching_snippets.append(line)
                    
                    # Agar specific lines na milen toh poori details dikha dein, warna sirf matching hissa
                    display_text = "\n".join(matching_snippets) if matching_snippets else row_text
                    
                    match_count += 1
                    with st.container():
                        st.markdown(f"**Result #{match_count}**")
                        if 'Date & Time' in row and pd.notna(row['Date & Time']):
                            st.markdown(f"🕒 **Waqt (Time):** {row['Date & Time']}")
                        if 'Source/Sender' in row and pd.notna(row['Source/Sender']):
                            st.markdown(f"👤 **Sender:** {row['Source/Sender']}")
                        
                        st.markdown(f"📋 **Mutaliqa Details:**\n{display_text}")
                        st.markdown("---")
