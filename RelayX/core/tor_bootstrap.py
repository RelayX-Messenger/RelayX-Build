import subprocess
from utilities.network.network_service import HSDIR
from RelayX.utils.paths import torrc_path, tor_path
green = "\033[0;32m"
cyan = "\033[0;36m"
reset = "\033[0m"


tor_process : subprocess.Popen | None = None

def start_tor():
    global tor_process
    with open(torrc_path, "w") as f:
        f.write(
f"""SocksPort 127.0.0.1:9050

HiddenServiceDir {HSDIR}
HiddenServicePort 5050 127.0.0.1:5050
""")
    tor_process = subprocess.Popen([tor_path, "-f", torrc_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f"{green}INFO{reset}:     [{cyan}Tor{reset}] RelayX transport started.")
    
def stop_tor():
    global tor_process
    if tor_process is None:
        return
    
    try:
        tor_process.terminate()
        tor_process.wait(timeout=5)
    except Exception:
        tor_process.kill()
    finally:
        tor_process = None