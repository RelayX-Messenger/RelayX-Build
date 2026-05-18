import os, pathlib, sys


# All paths here to decouple config and path, and make this the source of truth everywhere.

APPDATA = os.getenv("APPDATA")
HSDIR = os.path.join(APPDATA, "RelayX", "data", "HiddenService")
RelayX_exe_location = pathlib.Path(sys.executable).parent # sys.executable returns python.exe's Location, But after compiling, It will point to RelayX.exe's Location.

LOCALAPPDATA = os.getenv("LOCALAPPDATA")

torrc_path = os.path.join(APPDATA, "RelayX", "torrc")
hostname_path = os.path.join(HSDIR, "hostname")
tor_necessities = os.path.join(HSDIR, "tor_necessities")
libs_dir = os.path.join(RelayX_exe_location, "..", "libs") 
db_filepath = os.path.join(LOCALAPPDATA, "RelayX", "RelayX.db")

tor_path = os.path.join(RelayX_exe_location, '..', "tor", "tor.exe" )
relay_file = os.path.join(APPDATA, "RelayX", "Routing", "relay_list.json")