import urllib.request
import urllib.parse
import ssl
import re
import os
import json
import time

PDF_DIR = "dam_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

BASE_URL = "https://wrd.maharashtra.gov.in"

def fetch_page_pdf_links(page_num=1):
    url = f"https://wrd.maharashtra.gov.in/Site/ViewPDFList?doctype=BTOLaLNhA0/q1GTf08fcNQN43JuJzENBtWSJwpAPMdgCPB0nLNI/L7AcnDUxfgYUyBtUXiLMcs6zX9kgTMjLefMEy4jeFOsSz4OAJEBdDWI=&page={page_num}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            links = re.findall(r'href=[\"\']([^\"\']+\.pdf[^\"]*)[\"\']', html, re.I)
            return links
    except Exception as e:
        print(f"Error fetching page {page_num}: {e}")
        return []

def main():
    print("🚀 Scraping WRD website PDF archive pages...")
    all_found_links = set()
    
    for p in range(1, 50):
        links = fetch_page_pdf_links(p)
        if not links:
            print(f"No links found on page {p}. Stopping pagination.")
            break
        
        pdf_storage_links = [l for l in links if 'Storage' in l or 'Report' in l or 'पाणीसाठा' in l]
        print(f"Page {p}: Found {len(links)} total PDF links ({len(pdf_storage_links)} storage reports).")
        all_found_links.update(pdf_storage_links)
        time.sleep(0.5)

    print(f"\n📊 Total Storage PDF links discovered across archive pages: {len(all_found_links)}")
    
    # Download missing PDFs from discovered links
    downloaded = 0
    for link in all_found_links:
        full_url = link if link.startswith('http') else urllib.parse.urljoin(BASE_URL, link)
        # Extract date from link name
        m = re.search(r'(\d{2}[-._]\d{2}[-._]\d{4})', link)
        if not m:
            continue
            
        dt_str = m.group(1).replace('.', '-').replace('_', '-')
        dest_path = os.path.join(PDF_DIR, f"report_{dt_str}.pdf")
        
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
            continue
            
        req = urllib.request.Request(full_url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=12) as resp:
                data = resp.read()
                if len(data) > 1000:
                    with open(dest_path, 'wb') as f:
                        f.write(data)
                    downloaded += 1
                    print(f"  ✅ Downloaded missing PDF: {dest_path}")
        except Exception as e:
            print(f"  ❌ Error downloading {dt_str}: {e}")

    print(f"\n🏁 Finished! Downloaded {downloaded} new missing PDFs.")

if __name__ == '__main__':
    main()
