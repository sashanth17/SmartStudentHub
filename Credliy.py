import requests
from datetime import datetime, timezone

class CredlyBadgeVerification:
    def verify(badge_id):
        """
        Verifies a Credly digital badge using its public API endpoint.

        This function performs technical validity checks. If verification fails at
        any step, it prints a descriptive log of the failure and returns None.

        Args:
            badge_id (str): The unique ID of the badge to verify.

        Returns:
            dict: The JSON data object for the badge if it is fully verified.
            None: If the verification fails for any reason.
        """
        if not badge_id:
            print("Verification Log: Badge ID cannot be empty.")
            return None

        url = f"https://www.credly.com/api/v1/public_badges/{badge_id}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 404:
                print(f'Verification Log: Badge ID "{badge_id}" not found (404).')
                return None
            response.raise_for_status()
            badge_data = response.json().get('data', {})
        except requests.exceptions.RequestException as e:
            print(f"Verification Log: API request failed: {e}")
            return None
        except ValueError:
            print("Verification Log: Failed to parse JSON response from the API.")
            return None

        state = badge_data.get('state')
        if state != 'accepted':
            print(f'Verification Log: Badge state is "{state}", not "accepted".')
            return None

        expires_at_str = badge_data.get('expires_at')
        if expires_at_str:
            try:
                expiration_date = datetime.fromisoformat(expires_at_str)
                now_utc = datetime.now(timezone.utc)
                if expiration_date < now_utc:
                    print(f'Verification Log: Badge expired on {expiration_date.date()}.')
                    return None
            except (ValueError, TypeError):
                print(f'Verification Log: Could not parse expiration date: "{expires_at_str}"')
                return None

        print(f'Verification Log: Badge "{badge_id}" is technically valid. Extracting details...')
        return badge_data


# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    badge_id_to_check = "f5deaadd-8abb-45d9-abfa-99d600ce9245" # Cisco Network Tech
    
    print(f"--- Attempting Full Verification for ID: {badge_id_to_check} ---")
    
    verified_content = CredlyBadgeVerification.verify(badge_id_to_check)
    
    if verified_content:
        print("\n" + "="*15 + " VERIFICATION SUCCEEDED " + "="*15)
        
        # --- Extracting Core Details ---
        earner = verified_content.get('issued_to', 'N/A')
        badge_template = verified_content.get('badge_template', {})
        badge_name = badge_template.get('name', 'N/A')
        issuer = verified_content.get('issuer', {}).get('summary', 'N/A')
        issued_date = verified_content.get('issued_at_date', 'N/A')
        expires_date = verified_content.get('expires_at_date', 'Does not expire')
        level = badge_template.get('level', 'N/A')
        
        print(f"\n[+] Earner:         {earner}")
        print(f"[+] Credential:     {badge_name}")
        print(f"[+] Issuer:         {issuer}")
        print(f"[+] Issued On:      {issued_date}")
        print(f"[+] Expires On:     {expires_date}")
        print(f"[+] Level:          {level}")

        # --- Extracting Description ---
        description = badge_template.get('description', 'No description provided.')
        print("\n[+] Description:")
        print(f"    {description}")

        # --- Extracting Earning Criteria (The "Grade") ---
        criteria = badge_template.get('badge_template_activities', [])
        print("\n[+] Earning Criteria:")
        if criteria:
            for item in criteria:
                print(f"    - {item.get('title', 'N/A')}")
        else:
            print("    - No specific criteria listed.")
            
        # --- Extracting Validated Skills (The "Credits") ---
        skills = badge_template.get('skills', [])
        print("\n[+] Validated Skills:")
        if skills:
            skill_names = [skill.get('name', 'N/A') for skill in skills]
            print(f"    {', '.join(skill_names)}")
        else:
            print("    - No skills listed.")
            
        print("\n" + "="*48)

    else:
        print("\n" + "!"*15 + " VERIFICATION FAILED " + "!"*15)
        print("See verification log above for the reason.")
