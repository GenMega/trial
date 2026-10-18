import time
import requests

# Track start time to enforce the 5.5-hour limit
start_time = time.time()
MAX_RUN_TIME = 5.5 * 3600  # 5.5 hours in seconds

session = requests.Session()
base_url = "https://fliphits.com/api/app"
headers = {
    "Host": "fliphits.com",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}

# Authentication
auth_data = {
    "application_key": "54fcfd42fc2949d6ac3126d13734dfde7775eab80ecb0f05d1d4508747f916b7",
    "app_id": "5767d69deef14e9799109527ee62b396"
}

print("[+] Authenticating...")
auth_response = session.post(f"{base_url}/auth", headers=headers, data=auth_data)
auth_json = auth_response.json()

if not auth_json.get("status"):
    print("[!] Authentication failed. Exiting.")
    exit()

print(f"[+] Logged in as: {auth_json.get('username')}")

# Initial payload template
payload = {
    "viewer_mode": "gui",
    "os_system": "win",
    "gpu_status": "enabled",
    "visitor_profile_inventory_complete": "1",
    "visitor_profile_inventory": "[]",
    "available_ram_mb": "2421",
    "client_resource_issue": "0",
    "cpu_cores": "8",
    "free_cpu_percent": "800",
    "recent_render_crash_count": "0",
    "system_cpu_percent": "0",
    "total_ram_mb": "8005",
    "app_id": "5767d69deef14e9799109527ee62b396",
    "application_key": "54fcfd42fc2949d6ac3126d13734dfde7775eab80ecb0f05d1d4508747f916b7"
}

print("[+] Requesting initial site...")
response = session.post(f"{base_url}/next-site", headers=headers, data=payload)
res_json = response.json()

current_site_id = str(res_json.get("Id"))
current_token = str(res_json.get("visit_token"))
previous_token = current_token 
duration = int(res_json.get("site", {}).get("duration", 30))

payload["hit_completed"] = "1"

print("[+] Starting auto-surf loop...")
try:
    while True:
        # Check if 5.5 hours have elapsed
        if time.time() - start_time >= MAX_RUN_TIME:
            print("[+] 5.5-hour limit reached. Exiting cleanly for cron handover.")
            break

        payload["completed_site"] = current_site_id
        payload["visit_token"] = current_token
        payload["pending_visit_token"] = previous_token
        payload["duration"] = str(duration)

        print(f"--- Sending hit for site: {current_site_id} ---")
        response = session.post(f"{base_url}/next-site", headers=headers, data=payload)
        
        try:
            res_json = response.json()
            earned = res_json.get("earnpoint", 0)
            print(f"[+] Points earned: {earned}")
            
            previous_token = current_token
            current_token = str(res_json.get("visit_token"))
            current_site_id = str(res_json.get("Id"))
            
            duration = int(res_json.get("site", {}).get("duration", res_json.get("active_visit_remaining_seconds", 30)))
            
        except Exception as err:
            print(f"[!] Error parsing response: {err}")
            duration = 30

        # Countdown loop
        print(f"[*] Waiting {duration} seconds...")
        for remaining in range(duration, 0, -1):
            # Also check time limit inside countdown to exit faster if needed
            if time.time() - start_time >= MAX_RUN_TIME:
                break
            print(f"\rTime remaining: {remaining:3d}s ", end="", flush=True)
            time.sleep(1)
        print("\r[+] Moving to next site...\n")

except Exception as e:
    print(f"[!] Script error: {e}")
