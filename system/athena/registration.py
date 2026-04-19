#!/usr/bin/env python3
"""
LUDICROUS-PILOT PRIVACY PATCH:
  Device registration is performed locally using the hardware serial number.
  No network calls are made to comma servers (api.commadotai.com).
  The dongle ID is derived from the device serial for local identification only.
  Existing dongle IDs (from /persist or params) are preserved.
"""
import hashlib
from pathlib import Path

from openpilot.common.params import Params
from openpilot.selfdrive.selfdrived.alertmanager import set_offroad_alert
from openpilot.system.hardware import HARDWARE, PC
from openpilot.system.hardware.hw import Paths
from openpilot.common.swaglog import cloudlog


UNREGISTERED_DONGLE_ID = "UnregisteredDevice"


def is_registered_device() -> bool:
  dongle = Params().get("DongleId")
  return dongle not in (None, UNREGISTERED_DONGLE_ID)


def register(show_spinner=False) -> str | None:
  """
  Generate a local-only dongle ID from the hardware serial.
  No network calls — the ID is a deterministic hash of the serial,
  prefixed with 'lp-' to distinguish from comma-issued IDs.

  If a dongle ID already exists (from /persist or a previous run),
  it is preserved as-is.
  """
  params = Params()

  dongle_id: str | None = params.get("DongleId")

  # Preserve existing dongle ID from /persist (factory-provisioned devices)
  if dongle_id is None and Path(Paths.persist_root() + "/comma/dongle_id").is_file():
    with open(Paths.persist_root() + "/comma/dongle_id") as f:
      dongle_id = f.read().strip()

  # Generate a local dongle ID if none exists
  if dongle_id is None:
    serial = HARDWARE.get_serial()
    if serial:
      # Deterministic 16-char hex ID from serial
      local_hash = hashlib.sha256(f"ludicrous-pilot-{serial}".encode()).hexdigest()[:16]
      dongle_id = f"lp-{local_hash}"
      cloudlog.info(f"generated local dongle ID: {dongle_id}")
    else:
      dongle_id = UNREGISTERED_DONGLE_ID
      cloudlog.warning("no serial available, using unregistered dongle ID")

  if dongle_id:
    params.put("DongleId", dongle_id)
    set_offroad_alert("Offroad_UnregisteredHardware", (dongle_id == UNREGISTERED_DONGLE_ID) and not PC)

  return dongle_id


if __name__ == "__main__":
  print(register())
