import requests
import time
import random
import re
import string
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

init(autoreset=True)

# Fungsi untuk memuat daftar proxy dari file
def load_proxies():
    try:
        with open("Proxy.txt", "r") as file:
            proxies = [line.strip() for line in file if line.strip()]
        return proxies
    except FileNotFoundError:
        print(Fore.RED + "proxy.txt not found.")
        return []

# Fungsi untuk mendapatkan sesi dengan proxy yang dipilih secara acak
def get_proxy_session(proxies):
    if not proxies:
        print(Fore.YELLOW + "Tidak ada proxy tersedia. Menggunakan sesi default.")
        return requests.Session()
    
    random.shuffle(proxies)  # Acak daftar proxy sebelum digunakan
    
    for proxy in proxies:
        session = requests.Session()
        session.proxies = {"http": proxy, "https": proxy}
        
        try:
            # Ambil IP publik dari proxy
            response = session.get("https://api.ipify.org?format=json", timeout=5)
            if response.status_code == 200:
                ip = response.json().get("ip")
                print(Fore.GREEN + f"Menggunakan Proxy Dengan IP: {ip}")
                return session
        except requests.RequestException:
            print(Fore.RED + f"Proxy gagal: {proxy}")
    
    print(Fore.YELLOW + "Semua proxy gagal. Menggunakan sesi default.")
    return requests.Session()

def generate_random_email(session):
    username = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 8)))
    username += str(random.randint(100, 999))
    domain = session.get("https://api.mail.tm/domains").json()["hydra:member"][0]["domain"]
    return f"{username}@{domain}"

def get_random_country():
    countries = [
        "🇺🇸 United States", "🇨🇦 Canada", "🇦🇼 Aruba", "🇦🇫 Afghanistan", "🇦🇴 Angola",
        "🇦🇮 Anguilla", "🇦🇸 Åland Islands", "🇦🇱 Albania", "🇦🇩 Andorra", "🇦🇪 United Arab Emirates",
        "🇦🇷 Argentina", "🇦🇲 Armenia", "🇦🇸 American Samoa", "🇦🇶 Antarctica", "🇹🇰 French Southern and Antarctic Lands",
        "🇦🇬 Antigua and Barbuda", "🇦🇺 Australia", "🇦🇹 Austria", "🇦🇿 Azerbaijan"
    ]
    return random.choice(countries)

def get_random_name():
    first_names = [
        "John", "Michael", "Emily", "Emma", "David", "Daniel", "Sophia", "Olivia",
        "James", "William", "Ethan", "Benjamin", "Nathan", "Aiden", "Samuel",
        "Alexander", "Henry", "Liam", "Lucas", "Noah", "Mason", "Logan", "Jacob"
    ]
    
    last_names = [
        "Smith", "Johnson", "Brown", "Williams", "Jones", "Garcia", "Davis", "Miller",
        "Wilson", "Anderson", "Moore", "Taylor", "Jackson", "Harris", "Martin",
        "Clark", "Lewis", "Walker", "Allen", "Young", "King", "Wright", "Scott"
    ]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    return first_name, last_name

def get_referred_by():
    try:
        with open("Reff.txt", "r") as file:
            return file.readline().strip()
    except FileNotFoundError:
        return ""

def create_account(session):
    email = generate_random_email(session)
    password = "Password123!"
    
    payload = {"address": email, "password": password}
    response = session.post("https://api.mail.tm/accounts", json=payload)

    if response.status_code == 201:
        print(Fore.CYAN + f"Akun dibuat: {email}")
        return email, password
    else:
        print(Fore.RED + f"Gagal membuat akun (Status {response.status_code}): {response.text}")
        return None, None

def post_to_waitlist(session, email):
    country = get_random_country()
    referred_by = get_referred_by()
    first_name, last_name = get_random_name()
    
    payload = {
        "country": country,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "referred_by": referred_by
    }
    
    response = session.post("https://api.legend.xyz/waitlist", json=payload)
    if response.status_code == 201:
        print(Fore.GREEN + f"Berhasil daftar ke waitlist: {first_name} {last_name} dari {country}")
    else:
        print(Fore.RED + "Gagal daftar ke waitlist:", response.json())

def get_token(session, email, password):
    response = session.post("https://api.mail.tm/token", json={"address": email, "password": password})
    if response.status_code == 200:
        return response.json()["token"]
    else:
        print(Fore.RED + "Gagal mendapatkan token:", response.json())
        return None

def get_email_content(session, token, message_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = session.get(f"https://api.mail.tm/messages/{message_id}", headers=headers)
    if response.status_code == 200:
        return response.json().get("text") or response.json().get("html") or ""
    return ""

def get_inbox_messages(session, token):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(15):
        response = session.get("https://api.mail.tm/messages", headers=headers)
        if response.status_code == 200:
            messages = response.json()["hydra:member"]
            if messages:
                latest_message = messages[0]
                print(Fore.YELLOW + f"Email dari: {latest_message['from']['address']}, Subjek: {latest_message['subject']}")
                return latest_message["id"], get_email_content(session, token, latest_message["id"])
        time.sleep(1)
    print(Fore.YELLOW + "Tidak ada email masuk setelah 15 detik.")
    return None, None

def extract_verification_token(email_text):
    if email_text:
        match = re.search(r'https://legend\.xyz/waitlist_confirmation\?confirmation_token=([\w\-._]+)', email_text)
        if match:
            return match.group(1)
    return None

def verify_email(session, token):
    if token:
        url = "https://api.legend.xyz/waitlist/confirm"
        response = session.post(url, json={"token": token})

        if response.status_code == 200:
            print(Fore.GREEN + "Email berhasil diverifikasi.")
            return True
        else:
            print(Fore.RED + "Gagal verifikasi email:", response.text)
            return False
    return False

def check_latest_email(session, email, password):
    token = get_token(session, email, password)
    if token:
        message_id, email_text = get_inbox_messages(session, token)
        if message_id and email_text:
            verification_token = extract_verification_token(email_text)
            if verification_token:
                verify_email(session, verification_token)

def main():
    try:
        referral_count = int(input(Fore.YELLOW + "Berapa Referral? "))
    except ValueError:
        print(Fore.RED + "Masukkan angka yang valid!")
        return

    proxies = load_proxies()

    for i in range(referral_count):
        print(Fore.YELLOW + f"\nMendaftarkan akun ke-{i+1}...\n")
        
        session = get_proxy_session(proxies)
        
        email, password = create_account(session)
        if email and password:
            post_to_waitlist(session, email)
            check_latest_email(session, email, password)

if __name__ == "__main__":
    main()
