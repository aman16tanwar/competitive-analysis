import requests
import streamlit as st
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# SpyFu and SerpApi credentials
SPYFU_API_KEY = ""  # Replace with your SpyFu Secret Key
SERPAPI_KEY = ""  # Replace with your SerpApi key
FB_ACCESS_TOKEN = ""  # Replace with your Facebook access token




# Mapping for month numbers to names
MONTH_MAP = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}

def clean_domain(domain):
    """Clean the domain to remove protocol and www."""
    domain = domain.replace("https://", "").replace("http://", "")
    domain = domain.replace("www.", "")
    return domain

# Function to fetch PPC competitors from SpyFu
def fetch_ppc_competitors(domain, country_code):
    cleaned_domain = clean_domain(domain)
    endpoint = "https://www.spyfu.com/apis/competitors_api/v2/ppc/getTopCompetitors"
    params = {
        "domain": cleaned_domain,
        "startingRow": 1,
        "pageSize": 5,
        "countryCode": country_code,
        "api_key": SPYFU_API_KEY
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching PPC competitors: {str(e)}")
        return []

# Function to fetch domain stats for the last 3 months
def fetch_domain_stats_last_3_months(domain, country_code):
    url = f"https://www.spyfu.com/apis/domain_stats_api/v2/getAllDomainStats"
    params = {
        "domain": domain,
        "countryCode": country_code,
        "api_key": SPYFU_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if len(results) > 3:
            results = results[-3:]
        
        for entry in results:
            entry["searchMonth"] = MONTH_MAP.get(entry["searchMonth"], entry["searchMonth"])
        
        return results
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching domain stats: {e}")
        return []

# Function to fetch ad creatives from Google Ads Transparency
def fetch_google_ad_creatives(domain):
    endpoint = "https://serpapi.com/search"
    params = {
        "engine": "google_ads_transparency_center",
        "text": domain,
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('ad_creatives', [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching Google ad creatives: {str(e)}")
        return []

# Function to fetch ad creatives from Facebook Ads Library
def fetch_facebook_ad_creatives(domain, country_code):
    endpoint = f"https://graph.facebook.com/v21.0/ads_archive"
    params = {
        "ad_reached_countries": country_code,
        "search_terms": domain,
        "access_token": FB_ACCESS_TOKEN
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching Facebook ad creatives: {str(e)}")
        return []

# Display competitor data in a table format
def display_competitor_data(competitors):
    st.markdown('<div class="section-header">🏆 Competitor Analysis</div>', unsafe_allow_html=True)
    
    # Display the competitor stats in a table format
    if competitors:
        st.markdown('**🔗 Top PPC Competitors with Domain Stats**')
        competitor_table = "| Domain | Search Month | Search Year | Average Ad Rank | Strength | Monthly Budget | Total Ads Purchased |\n"
        competitor_table += "|--------|--------------|-------------|-----------------|----------|----------------|----------------------|\n"
        
        for entry in competitors:
            competitor_table += f"| {entry['domain']} | {entry['searchMonth']} | {entry['searchYear']} | {entry['averageAdRank']} | {entry['strength']} | ${entry['monthlyBudget']:,.2f} | {entry['totalAdsPurchased']} |\n"
        
        st.markdown(competitor_table, unsafe_allow_html=True)

# Main Streamlit app function
def main():
    st.title("🔍 Kedet Competitive Analysis")
    
    with st.sidebar:
        st.header("🛠️ Search Configuration")
        domain = st.text_input("🌐 Enter Domain (e.g., skibig3.com)")
        country_codes = ["US", "CA", "UK", "IN"]
        country_code = st.selectbox("Select Country Code", country_codes)

        if st.button("Fetch Competitors"):
            if domain and country_code:
                with st.spinner("Fetching competitors..."):
                    competitors = fetch_ppc_competitors(domain, country_code)
                    if competitors:
                        st.session_state['competitors'] = competitors
                        st.session_state['country_code'] = country_code
                        
                        stats_data = []
                        for comp in competitors:
                            comp_data = fetch_domain_stats_last_3_months(comp['domain'], country_code)
                            for month_data in comp_data:
                                month_data['domain'] = comp['domain']
                            stats_data.extend(comp_data)
                        
                        st.session_state['stats_data'] = stats_data
            else:
                st.warning("Please enter a domain and select a country.")

    if 'stats_data' in st.session_state:
        display_competitor_data(st.session_state['stats_data'])

    if 'competitors' in st.session_state:
        competitor_options = [entry['domain'] for entry in st.session_state['competitors']]
        selected_competitor = st.selectbox("Select Competitor", competitor_options)
        
        ad_source = st.radio("Choose Ad Source", ("Google Ads", "Facebook Ads"))

        if st.button("Fetch Ad Creatives"):
            if selected_competitor:
                if ad_source == "Google Ads":
                    ad_creatives = fetch_google_ad_creatives(selected_competitor)
                    st.session_state['ad_creatives'] = ad_creatives
                    st.session_state['ad_source'] = "Google Ads"
                else:
                    ad_creatives = fetch_facebook_ad_creatives(selected_competitor, st.session_state['country_code'])
                    st.session_state['ad_creatives'] = ad_creatives
                    st.session_state['ad_source'] = "Facebook Ads"

    if 'ad_creatives' in st.session_state:
        st.markdown(f"### {st.session_state['ad_source']} Ad Creatives")
        if st.session_state['ad_source'] == "Google Ads":
            for ad in st.session_state['ad_creatives']:
                st.markdown(f"**Ad Format**: {ad.get('format', 'N/A')}")
                if ad.get('image'):
                    st.image(ad['image'], caption="Google Ad Creative", use_column_width=True)
                st.markdown("---")
        elif st.session_state['ad_source'] == "Facebook Ads":
            for ad in st.session_state['ad_creatives']:
                st.markdown(f"**Page ID**: {ad.get('page_id')}")
                st.markdown(f"**Ad Start Time**: {ad.get('ad_delivery_start_time')}")
                st.markdown(f"**Ad Stop Time**: {ad.get('ad_delivery_stop_time')}")
                st.markdown(f"[View Ad on Facebook]({ad['ad_snapshot_url']})")
                st.markdown("---")

if __name__ == "__main__":
    main()
