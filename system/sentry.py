"""Install exception handler for process crash.

LUDICROUS-PILOT PRIVACY PATCH:
  All remote Sentry reporting is disabled.  Crashes are still saved to
  local disk via save_exception() so they can be inspected on-device.
  Every public function keeps its original signature so callers don't break.
"""
import os
import traceback
from datetime import datetime
from enum import Enum

from openpilot.system.hardware.hw import Paths
from openpilot.common.swaglog import cloudlog

CRASHES_DIR = Paths.crash_log_root()


class SentryProject(Enum):
  # keep the enum so existing code that references it doesn't break
  SELFDRIVE = "disabled"
  SELFDRIVE_NATIVE = SELFDRIVE


def report_tombstone(fn: str, message: str, contents: str) -> None:
  cloudlog.error({'tombstone': message})
  save_exception(f"tombstone: {fn}\n{message}\n{contents}")


def capture_exception(*args, **kwargs) -> None:
  cloudlog.error("crash", exc_info=kwargs.get('exc_info', 1))
  try:
    save_exception(traceback.format_exc())
  except Exception:
    cloudlog.exception("save_exception failed")


def save_exception(content: str) -> None:
  """Save crash info to local disk only — no remote reporting."""
  try:
    if not os.path.exists(CRASHES_DIR):
      os.makedirs(CRASHES_DIR)

    files = [
      os.path.join(CRASHES_DIR, datetime.now().strftime("%Y-%m-%d--%H-%M-%S.log")),
      os.path.join(CRASHES_DIR, "error.log")
    ]

    for fn in files:
      with open(fn, 'w') as f:
        if fn == "error.log":
          lines = content.splitlines()[-3:]
          f.write("\n".join(lines))
        else:
          f.write(content)

    cloudlog.error(f"logged crash to {files}")
  except Exception:
    cloudlog.exception("error when attempting to save exception")


def capture_fingerprint_mock() -> None:
  cloudlog.info("fingerprint mock — remote reporting disabled")


def capture_fingerprint(candidate: str, car_name: str) -> None:
  cloudlog.info(f"Fingerprinted {candidate} ({car_name}) — remote reporting disabled")


def set_tag(key: str, value: str) -> None:
  pass  # no-op: sentry disabled


def set_user() -> None:
  pass  # no-op: sentry disabled


def get_properties() -> tuple[str, str, str]:
  """Kept for any callers that use it, but no data leaves the device."""
  return ("", "", "")


def init(project: SentryProject) -> bool:
  cloudlog.info("sentry.init called — remote reporting disabled (ludicrous-pilot privacy patch)")
  return True
