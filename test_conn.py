import os
import sys
import socket
import urllib.parse

def test_supabase_connection():
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_file):
        print("[ERROR] .env file not found in project directory.")
        return False

    db_url = ""
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('DATABASE_URL='):
                db_url = line.split('=', 1)[1].strip().strip('\'"')
                break

    if not db_url:
        print("[ERROR] DATABASE_URL is missing or empty in .env.")
        return False

    try:
        parsed = urllib.parse.urlparse(db_url)
    except Exception as e:
        print(f"[ERROR] Could not parse DATABASE_URL: {e}")
        return False

    host = parsed.hostname
    port = parsed.port or 5432
    user = parsed.username
    dbname = parsed.path.lstrip('/') or 'postgres'

    print("==================================================")
    print("        SUPABASE CONNECTION TEST (SAFE)")
    print("==================================================")
    print(f"Target Host : {host}")
    print(f"Target Port : {port}")
    print(f"Database    : {dbname}")
    print(f"User / Pool : {user}")
    print("--------------------------------------------------")

    # 1. Test Network / TCP Socket
    print("Phase 1: Testing TCP socket reachability...")
    try:
        sock = socket.create_connection((host, port), timeout=7)
        sock.close()
        print(" -> [OK] TCP connection to Supabase pooler succeeded.")
    except socket.timeout:
        print(" -> [FAIL] Connection timed out.")
        print("    Paliwanag: Hindi maabot ang server sa loob ng 7 segundo.")
        print("    Solusyon: Tingnan ang internet connection o tiyaking tama ang host name.")
        return False
    except socket.gaierror:
        print(" -> [FAIL] DNS resolution failed.")
        print("    Paliwanag: Hindi ma-resolve ang host domain.")
        print("    Solusyon: Tiyaking tama ang Supabase pooler domain sa DATABASE_URL.")
        return False
    except Exception as e:
        print(f" -> [FAIL] Network error: {e}")
        return False

    # 2. Test PostgreSQL authentication (requires psycopg2)
    print("\nPhase 2: Testing PostgreSQL authentication & query...")
    try:
        import psycopg2
    except ImportError:
        print(" -> [WAITING] 'psycopg2' is not yet installed in virtualenv.")
        print("    Network is ready. Install requirements to test PostgreSQL handshake.")
        return True

    try:
        password = urllib.parse.unquote(parsed.password or '')
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            sslmode='require',
            connect_timeout=10
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(" -> [SUCCESS] Connected and authenticated successfully to Supabase!")
        print(f"    Server Info: {db_version.split(',')[0]}")
        return True
    except psycopg2.OperationalError as e:
        err_msg = str(e).strip()
        print(" -> [FAIL] PostgreSQL Authentication/Handshake Failed.")
        print(f"    Error Details: {err_msg}")
        print("\n--- Diagnostic & Troubleshooting Guide (Filipino / English) ---")
        if "password authentication failed" in err_msg.lower():
            print("1. Mali ang database password.")
            print("   - Kung may special characters ang password (e.g. '@', '#', '%', ':'), kailangan itong URL-encoded.")
            print("   - O i-reset ang database password sa Supabase Dashboard > Project Settings > Database.")
        elif "tenant or user not found" in err_msg.lower() or "role" in err_msg.lower():
            print("2. Mali ang username o pooler format.")
            print("   - Sa Supabase Session Pooler (port 5432 o 6543), ang username ay dapat: postgres.[YOUR-PROJECT-REF]")
        elif "ssl" in err_msg.lower():
            print("3. SSL Configuration error.")
            print("   - Siguraduhing may '?sslmode=require' sa dulo ng DATABASE_URL.")
        else:
            print(f"4. Error: {err_msg}")
        return False
    except Exception as e:
        print(f" -> [FAIL] Unexpected error: {e}")
        return False

if __name__ == '__main__':
    test_supabase_connection()
