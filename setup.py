"""Toolbox for control and optimization of water systems.

RTC-Tools is the Deltares toolbox for control and optimization of water systems.

"""
import sys

from setuptools import find_packages, setup

import versioneer

if sys.version_info < (3, 9):
    sys.exit("Sorry, Python 3.9 or newer is required.")

DOCLINES = __doc__.split("\n")

CLASSIFIERS = """\
Development Status :: 4 - Beta
Intended Audience :: Science/Research
Intended Audience :: Information Technology
License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)
Programming Language :: Python
Programming Language :: Python :: 3
Topic :: Scientific/Engineering :: GIS
Topic :: Scientific/Engineering :: Mathematics
Topic :: Scientific/Engineering :: Physics
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

setup(
    name="rtc-tools",
    version=versioneer.get_version(),
    maintainer="Deltares",
    author="Deltares",
    description=DOCLINES[0],
    long_description="\n".join(DOCLINES[2:]),
    url="https://oss.deltares.nl/web/rtc-tools/home",
    download_url="http://github.com/deltares/rtc-tools/",
    classifiers=[_f for _f in CLASSIFIERS.split("\n") if _f],
    platforms=["Windows", "Linux", "Mac OS-X", "Unix"],
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
        "casadi >= 3.6.3, == 3.6.*, !=3.6.6",
        "numpy >= 1.16.0",
        "scipy >= 1.0.0",
        "pymoca == 0.11.*",
        "rtc-tools-channel-flow >= 1.2.0",
        "rtc-tools-standard-library >= 0.1.1",
        "defusedxml >= 0.7.0",
        # Python 3.9's importlib.metadata does not support the "group" parameter
        # to entry_points yet.
        "importlib_metadata >= 5.0.0; python_version < '3.10'",
    ],
    tests_require=["pytest", "pytest-runner", "netCDF4"],
    extras_require={
        "netcdf": ["netCDF4"],
        "all": ["netCDF4"],
    },
    python_requires=">=3.9",
    cmdclass=versioneer.get_cmdclass(),
    entry_points={
        "console_scripts": [
            "rtc-tools-download-examples = rtctools.rtctoolsapp:download_examples",
            "rtc-tools-copy-libraries = rtctools.rtctoolsapp:copy_libraries",
        ]
    },
)
