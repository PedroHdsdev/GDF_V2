#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

# SAP RFC SDK: definir antes de qualquer import que use pyrfc (o linker usa LD_LIBRARY_PATH)
_nwrfcsdk_lib = Path(__file__).resolve().parent.parent / "nwrfcsdk" / "lib"
if _nwrfcsdk_lib.exists():
    prev = os.environ.get("LD_LIBRARY_PATH", "")
    os.environ["LD_LIBRARY_PATH"] = f"{_nwrfcsdk_lib}{os.pathsep}{prev}".rstrip(os.pathsep)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
