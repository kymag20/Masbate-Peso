import urllib.parse
import os

env_file = os.path.join(os.path.dirname(__file__), '.env')
with open(env_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip().startswith('DATABASE_URL='):
            url = line.strip().split('=', 1)[1].strip().strip('\'"')
            parsed = urllib.parse.urlparse(url)
            print("Host in .env:", parsed.hostname)
            print("Port in .env:", parsed.port)
            print("User in .env:", parsed.username)
            print("Has password:", bool(parsed.password))
