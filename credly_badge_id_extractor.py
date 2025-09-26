import pdfplumber
import re
import requests
import os
import time

# =================================================================
# 1. CORE UTILITY FUNCTIONS
# =================================================================

def extract_credly_id_from_url(credly_url):
    """
    Extracts the unique alphanumeric badge ID (GUID) from a long Credly 'badges/...' URL.
    """
    guid_pattern = r"/badges/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/print"
    match = re.search(guid_pattern, credly_url, re.IGNORECASE) 
    if match:
        return match.group(1)
    return None

def resolve_credly_short_url(short_url, max_retries=3):
    """
    Follows a short Credly URL redirect with retries for network robustness.
    """
    if "credly.com" not in short_url.lower():
        return None
    
    # Print using the original URL's case
    print(f"\nAttempting to resolve short URL: {short_url}...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                short_url, # <-- The actual request uses the case-sensitive URL
                timeout=15, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            response.raise_for_status() 
            return response.url
            
        except requests.exceptions.Timeout:
            print(f"⚠️ Attempt {attempt + 1}: Request timed out.")
        except requests.exceptions.RequestException as e:
            print(f"🛑 Attempt {attempt + 1}: Request failed ({e.__class__.__name__}). Check network/firewall.")
        
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            time.sleep(wait_time)

    return None

# =================================================================
# 2. MAIN PDF PROCESSING FUNCTION
# =================================================================
# (This logic correctly finds the case-sensitive URL and passes it to the resolver)

def process_certificate_pdf_complete(pdf_path):
    # ... (omitted for brevity, as the logic is correct)
    if not os.path.exists(pdf_path):
        return {"pdf_text": "Error: File Not Found", "credly_id": None, "final_long_url": None, "found_url_in_pdf": None}

    full_text_list = [] 
    found_url = None
    
    short_url_pattern = r'https?://(?:www\.)?credly\.com/go/[a-zA-Z0-9]{4,12}\b'
    long_url_pattern = r'https?://(?:www\.)?credly\.com/badges/[a-zA-Z0-9-]+/print'
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                
                # --- Line-by-Line Text Extraction (Correctly preserves case) ---
                words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False, extra_attrs=['top'])
                words.sort(key=lambda w: (w['top'], w['x0']))

                current_line = ""
                last_top = None
                
                for word in words:
                    if last_top is None or abs(word['top'] - last_top) > 5:
                        if current_line: full_text_list.append(current_line.strip())
                        current_line = word['text']
                        last_top = word['top']
                    else:
                        current_line += " " + word['text']
                
                if current_line: full_text_list.append(current_line.strip())

                full_text = "\n".join(full_text_list)
                search_text = full_text.lower()
                
                # --- URL Search (This sets found_url to the correct case) ---
                for annotation in page.annots:
                    if annotation.get('Subtype') == '/Link' and 'A' in annotation:
                        link_uri = annotation['A'].get('URI')
                        if link_uri and "credly.com" in link_uri.lower():
                            found_url = link_uri
                            break
                if found_url: break 

            long_credly_url = None
            
            if not found_url:
                match = re.search(short_url_pattern, full_text, re.IGNORECASE) or \
                        re.search(long_url_pattern, full_text, re.IGNORECASE)
                if match:
                    # found_url is set to the case-sensitive text found in the PDF
                    found_url = match.group(0) 

            if found_url:
                if "/go/" in found_url.lower():
                    # Resolves the short URL (uses the correct case)
                    long_credly_url = resolve_credly_short_url(found_url)
                elif "/badges/" in found_url.lower():
                    long_credly_url = found_url

            credly_id = extract_credly_id_from_url(long_credly_url) if long_credly_url else None
            
            return {
                "pdf_text": full_text,
                "credly_id": credly_id,
                "final_long_url": long_credly_url,
                "found_url_in_pdf": found_url 
            }

    except Exception as e:
        return {"pdf_text": f"Error during processing: {e}", "credly_id": None, "final_long_url": None, "found_url_in_pdf": None}


# =================================================================
# 3. FINAL EXECUTION AND FORMATTING BLOCK
# =================================================================

if __name__ == "__main__":
    # 1. Define the path to your certificate PDF file
    pdf_file_path = 'AWS_Academy_Graduate___AWS_Academy_Cloud_Foundations_Badge20250121-25-u7aks6.pdf' 

    print("\n" + "="*70)
    print(f"Starting analysis for: {pdf_file_path}")
    print("="*70)
    
    # 2. Run the main function
    results = process_certificate_pdf_complete(pdf_file_path)

    # 3. Print the final results in the EXACT requested format
    
    print("\n" + "="*70)
    print(" FINAL CERTIFICATE ANALYSIS RESULTS (VERY VERY PAKKA)")
    print("="*70)
    
    # --- DIAGNOSTICS & STATUS ---
    if results["credly_id"]:
        print(f"** ✅ CREDLY BADGE ID (EXTRACTED CLEANLY): **")
    else:
        print(f"** ❌ CREDLY BADGE ID NOT EXTRACTED (Check Redirect Status): **")
    print("-" * 70)

    print("\n** EXTRACTED PDF TEXT (LINE-BY-LINE, PRESERVING CASE): **")
    print(results["pdf_text"])
    
    print("\nRedirected Link")
    if results["final_long_url"]:
        print(results["final_long_url"])
    elif results["found_url_in_pdf"]:
        # Print the original link for manual checking
        print(f"Resolution Failed for: {results['found_url_in_pdf']} (Check network/firewall)")
    else:
        print("No Credly URL was found in the PDF text.")
    
    print("\nID SHANE NEED :")
    print(results["credly_id"] or "ID not found.")
    print("="*70)