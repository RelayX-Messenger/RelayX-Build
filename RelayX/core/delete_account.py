import os, shutil, asyncio, signal
from plyer import notification


from RelayX.core.tor_bootstrap import stop_tor
from RelayX.utils.config import db_filepath as db_file
from utilities.network.network_service import HSDIR


async def shutdown_backend(delay : float = 0.5):
    await asyncio.sleep(delay)
    os.kill(os.getpid(), signal.SIGINT)

async def perform_account_deletion():
    try:
        stop_tor()
        if os.path.exists(db_file):
            with open(db_file, "w") as f:
                f.write("")
        data_dir = os.path.join(HSDIR, "..")
        shutil.rmtree(data_dir)
        shutil.rmtree(db_file)
        asyncio.create_task(shutdown_backend())
    except Exception:
        notification.notify(title="RelayX Core : Identity Deletion", message=f"Identity Deletion was Unsuccessful. Please try again.", timeout=4)
        return 