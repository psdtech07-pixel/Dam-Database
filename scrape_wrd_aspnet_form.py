import urllib.request
import urllib.parse
import ssl
import re
import os
import time

PDF_DIR = "dam_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

URL = "https://wrd.maharashtra.gov.in/Site/ViewPDFList?doctype=BTOLaLNhA0/q1GTf08fcNQN43JuJzENBtWSJwpAPMdgCPB0nLNI/L7AcnDUxfgYUyBtUXiLMcs6zX9kgTMjLefMEy4jeFOsSz4OAJEBdDWI="

def get_form_params():
    req = urllib.request.Request(URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            viewstate = re.search(r'id="__VIEWSTATE"\s+value="([^"]+)"', html)
            eventvalidation = re.search(r'id="__EVENTVALIDATION"\s+value="([^"]+)"', html)
            viewstategenerator = re.search(r'id="__VIEWSTATEGENERATOR"\s+value="([^"]+)"', html)
            
            return {
                '__VIEWSTATE': viewstate.group(1) if viewstate else '',
                '__EVENTVALIDATION': eventvalidation.group(1) if eventvalidation else '',
                '__VIEWSTATEGENERATOR': viewstategenerator.group(1) if viewstategenerator else ''
            }
    except Exception as e:
        print("Error getting ASP.NET form state:", e)
        return {}

def search_pdf_range(start_str, end_str):
    form_data = get_form_params()
    form_data.update({
        'ctl00$ContentPlaceHolder1$txtStartDate': start_str,
        'ctl00$ContentPlaceHolder1$txtEndDate': end_str,
        'ctl00$ContentPlaceHolder1$btnSearch': 'Search'
    })
    
    encoded_data = urllib.parse.urlencode(form_data).encode('utf-8')
    req = urllib.request.Request(URL, data=encoded_data, headers=HEADERS)
    
    try:
        with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            links = re.findall(r'href=[\"\']([^\"\']+\.pdf[^\"]*)[\"\']', html, re.I)
            print(f"Query {start_str} to {end_str}: Found {len(links)} PDF links.")
            return links
    except Exception as e:
        print(f"Error querying range {start_str} - {end_str}: {e}")
        return []

if __name__ == '__main__':
    print("🚀 Querying WRD ASP.NET Search Form for missing 2024 & 2025 dates...")
    links_2024 = search_pdf_range("01/01/2024", "31/03/2024")
    links_2025 = search_pdf_range("01/01/2025", "31/01/2025")
    
    all_links = set(links_2024 + links_2025)
    print("Discovered PDF links:", len(all_links))
    for l in list(all_links)[:10]:
        print("  •", l)
