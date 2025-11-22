import importlib.resources
import logging
import os
import shutil
import sys
from importlib import metadata as importlib_metadata
from pathlib import Path

import rtctools

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("rtctools")
logger.setLevel(logging.INFO)


def copy_libraries(*args):
    if not args:
        args = sys.argv[1:]

    if not args:
        path = input("Folder to put the Modelica libraries: [.] ") or "."
    else:
        path = args[0]

    if not os.path.exists(path):
        sys.exit("Folder '{}' does not exist".format(path))

    def _copytree(src, dst, symlinks=False, ignore=None):
        if not os.path.exists(dst):
            os.makedirs(dst)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                _copytree(s, d, symlinks, ignore)
            else:
                if not os.path.exists(d):
                    shutil.copy2(s, d)
                elif Path(s).name.lower() == "package.mo":
                    # Pick the largest one, assuming that all plugin packages
                    # to not provide a meaningful package.mo
                    if os.stat(s).st_size > os.stat(d).st_size:
                        logger.warning(
                            "Overwriting '{}' with '{}' as the latter is larger.".format(d, s)
                        )
                        os.remove(d)
                        shutil.copy2(s, d)
                    else:
                        logger.warning(
                            "Not copying '{}' to '{}' as the latter is larger.".format(s, d)
                        )
                else:
                    raise OSError("Could not combine two folders")

    dst = Path(path)

    library_folders = []

    for ep in importlib_metadata.entry_points(group="rtctools.libraries.modelica"):
        if ep.name == "library_folder":
            library_folders.append(Path(importlib.resources.files(ep.module).joinpath(ep.attr)))

    tlds = {}
    for lf in library_folders:
        for x in lf.iterdir():
            if x.is_dir():
                tlds.setdefault(x.name, []).append(x)

    for tld, paths in tlds.items():
        if Path(tld).exists():
            sys.exit("Library with name '{}'' already exists".format(tld))

        try:
            for p in paths:
                _copytree(p, dst / p.name)
        except OSError:
            sys.exit("Failed merging the libraries in package '{}'".format(tld))

    sys.exit("Succesfully copied all library folders to '{}'".format(dst.resolve()))


def download_examples(*args):
    if not args:
        args = sys.argv[1:]

    if not args:
        path = input("Folder to download the examples to: [.] ") or "."
    else:
        path = args[0]

    if not os.path.exists(path):
        sys.exit("Folder '{}' does not exist".format(path))

    path = Path(path)

    import urllib.request
    from urllib.error import HTTPError
    from zipfile import ZipFile

    version = rtctools.__version__
    try:
        url = "https://github.com/rtc-tools/rtc-tools/zipball/{}".format(version)

        opener = urllib.request.build_opener()
        urllib.request.install_opener(opener)
        # The security warning can be dismissed as the url variable is hardcoded to a remote.
        local_filename, _ = urllib.request.urlretrieve(url)  # nosec
    except HTTPError:
        sys.exit("Could not found examples for RTC-Tools version {}.".format(version))

    with ZipFile(local_filename, "r") as z:
        target = path / "rtc-tools-examples"
        zip_folder_name = next(x for x in z.namelist() if x.startswith("Deltares-rtc-tools-"))
        prefix = "{}/examples/".format(zip_folder_name.rstrip("/"))
        members = [x for x in z.namelist() if x.startswith(prefix)]
        z.extractall(members=members)
        shutil.move(prefix, target)
        shutil.rmtree(zip_folder_name)

        sys.exit("Succesfully downloaded the RTC-Tools examples to '{}'".format(target.resolve()))

    try:
        os.remove(local_filename)
    except OSError:
        pass
