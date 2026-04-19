import subprocess, os, time, sys, pathlib

APPDATA = os.getenv("APPDATA")
RelayX_exe_location = pathlib.Path(sys.executable).parent
RelayX_exe_location = os.path.join(os.getenv("PROGRAMFILES"), "RelayX")

HSDIR = os.path.join(APPDATA, "RelayX", "data", "HiddenService")
hostname_path = os.path.join(HSDIR, "hostname")
tor_necessities = os.path.join(HSDIR, "tor_necessities")
tor_path = os.path.join(RelayX_exe_location, "tor", "tor.exe" )


os.makedirs(HSDIR, exist_ok=True)
os.makedirs(tor_necessities, exist_ok=True)

async def tor_hostname_creation():
    tor_process = subprocess.Popen(
        [
            tor_path,
            "--DataDirectory", tor_necessities,
            "--HiddenServiceDir", HSDIR,
            "--HiddenServicePort", "5050 127.0.0.1:5050"
        ],
        stdout=open(os.path.join(tor_necessities, "tor.log"), "w"),
        stderr=subprocess.STDOUT,
        text=True
    )


    timeout = 60
    start_time = time.time()

    while not os.path.isfile(hostname_path):
        if time.time() - start_time > timeout:
            tor_process.terminate()
            raise RuntimeError("Tor failed to start within 60 seconds")
        time.sleep(0.5)

    with open(hostname_path, "r") as f:
        onion_address = f.read().replace("\n", "").strip()
        tor_process.terminate()