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

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌍 Global Lead Engine")

def get_contacts(url):
    contacts = {'email': 'N/A', 'phone': 'N/A'}
    try:
        # We use a very standard browser header
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(url, timeout=5, headers=headers, verify=False)
        if resp.status_code == 200:
            text = resp.text
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            phone_match = re.search(r'\+?\d[\d -]{8,}\d', text)
            if email_match: contacts['email'] = email_match.group(0)
            if phone_match: contacts['phone'] = phone_match.group(0)
    except:
        pass
    return contacts

# --- UI ---
with st.form("search"):
    niche = st.text_input("Niche", "AI Automation")
    loc = st.text_input("Location", "Dubai")
    submit = st.form_submit_button("Find Leads")

if submit:
    st.info(f"Searching for {niche} in {loc}...")
    
    # NEW STRATEGY: Use a 'Site-Specific' Search to bypass standard bot detection
    # This targets LinkedIn, Instagram, and direct business sites
    search_query = f'"{niche}" "{loc}" email @gmail.com'
    url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&num=20"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # DEBUG: Let's see if Google is blocking us
        if response.status_code == 429:
            st.error("Google is temporarily blocking this request. Wait 5 minutes.")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        leads = []
        # Google search results are usually inside 'div.g' or 'div.yuRUbf'
        for g in soup.find_all('div', class_='g'):
            link = g.find('a', href=True)['href']
            title = g.find('h3').text if g.find('h3') else "Business"
            
            if "google.com" not in link:
                st.write(f"✅ Found: {title}")
                # Get deeper info
                contacts = get_contacts(link)
                leads.append({
                    "Name": title,
                    "Website": link,
                    "Email": contacts['email'],
                    "Phone": contacts['phone']
                })
        
        if leads:
            df = pd.DataFrame(leads)
            st.dataframe(df)
            
            # Export
            output = io.BytesIO()
            df.to_excel(output, index=False)
            st.download_button("📥 Download Excel", output.getvalue(), "leads.xlsx")
        else:
            st.warning("No leads found. Google might be blocking the 'Bot' fingerprint. Try a more specific search like 'Founder of [Niche] in [City]'")
            
    except Exception as e:
        st.error(f"Error: {e}")
