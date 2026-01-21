import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import time
import random
import io

# --- PAGE SETUP ---
st.set_page_config(page_title="Universal AI Lead Gen", layout="centered")

# Custom CSS for Mobile Styling
# FIX: Changed unsafe_allow_name_with_status to unsafe_allow_html
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #007bff; color: white; }
    .stDownloadButton>button { width: 100%; border-radius: 20px; background-color: #28a745; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌍 Global Lead Engine")
st.subheader("B2B & B2C AI Lead Generation")

# --- CORE LOGIC ---
def get_contacts(url):
    """Reliable non-blocking contact extraction."""
    contacts = {'email': 'N/A', 'phone': 'N/A', 'socials': []}
    try:
        # Using a more robust header to prevent blocks
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        resp = requests.get(url, timeout=7, headers=headers, verify=False)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            raw_text = soup.get_text()
            
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', raw_text)
            phones = re.findall(r'\+?\d[\d\-\(\) ]{9,}\d', raw_text)
            
            contacts['email'] = emails[0] if emails else "N/A"
            contacts['phone'] = phones[0] if phones else "N/A"
            
            platforms = ['instagram.com', 'linkedin.com', 'facebook.com', 'twitter.com', 'youtube.com']
            for a in soup.find_all('a', href=True):
                href = a['href'].lower()
                if any(p in href for p in platforms):
                    contacts['socials'].append(href)
    except:
        pass
    return contacts

def generate_pitch(niche, lead_type):
    if lead_type == "B2B":
        return f"Hi, we build AI agents for {niche} startups. Let's automate your workflow."
    return f"Hi, we help {niche} influencers build personal apps. Let's own your audience."

# --- UI INPUTS ---
tab1, tab2 = st.tabs(["Single Search", "Bulk Hierarchy (Tehsils)"])

with tab1:
    with st.form("single"):
        niche = st.text_input("Industry/Niche", "AI Tech Startups")
        loc = st.text_input("Specific Location", "Hauz Khas, Delhi")
        depth = st.number_input("Leads per search", 5, 50, 10)
        btn1 = st.form_submit_button("Start Search")

with tab2:
    st.info("Upload a CSV/Excel with a column named 'Location' to map entire regions.")
    uploaded_file = st.file_uploader("Upload District/Tehsil List", type=['csv', 'xlsx'])
    niche_bulk = st.text_input("Industry for Bulk Search", "Fashion Influencers")
    btn2 = st.button("Start Bulk Mapping")

# --- EXECUTION ENGINE ---
def run_process(loc_list, niche_target):
    leads_found = []
    progress = st.progress(0)
    total = len(loc_list)
    
    for idx, area in enumerate(loc_list):
        st.write(f"🔍 Mapping: {niche_target} in {area}...")
        # Search query focused on finding websites/founders
        search_query = f"{niche_target} {area} owner website"
        search_url = f"https://www.google.com/search?q={search_query.replace(' ','+')}"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
            res = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Clean Google redirect links
                if "/url?q=" in href and not "google.com" in href:
                    clean_link = href.split("/url?q=")[1].split("&")[0]
                    links.append(clean_link)
            
            # Limit links per sub-location to prevent getting blocked
            for link in list(dict.fromkeys(links))[:5]: 
                data = get_contacts(link)
                l_type = "B2C" if any(x in niche_target.lower() for x in ['fashion', 'fitness', 'influencer', 'coach']) else "B2B"
                leads_found.append({
                    "Location": area,
                    "Business Name": link.split('//')[-1].split('/')[0],
                    "Website": link,
                    "Email": data['email'],
                    "Phone": data['phone'],
                    "Socials": ", ".join(list(set(data['socials']))),
                    "Type": l_type,
                    "AI Pitch": generate_pitch(niche_target, l_type)
                })
        except Exception as e:
            st.warning(f"Skipped {area} due to connection limits.")
            
        progress.progress((idx + 1) / total)
        time.sleep(random.uniform(2, 5)) 

    if leads_found:
        df = pd.DataFrame(leads_found)
        st.success(f"Harvested {len(df)} leads!")
        st.dataframe(df)
        
        # Excel Export using BytesIO for Streamlit
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Leads_Database')
        
        st.download_button(
            label="📥 Download Excel Results",
            data=output.getvalue(),
            file_name=f"leads_{niche_target}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("No leads found. Try a different niche or location.")

# --- TRIGGER LOGIC ---
if btn1:
    run_process([loc], niche)

if btn2 and uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            loc_df = pd.read_csv(uploaded_file)
        else:
            loc_df = pd.read_excel(uploaded_file)
        
        if 'Location' in loc_df.columns:
            run_process(loc_df['Location'].tolist(), niche_bulk)
        else:
            st.error("File must have a column exactly named 'Location'")
    except Exception as e:
        st.error(f"Error reading file: {e}")
