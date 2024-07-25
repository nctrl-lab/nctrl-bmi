from setuptools import setup

setup(
    name="nctrl-bmi",
    version="0.0.1",
    description="realtime BMI with spiketag",
    url="https://github.com/lapis42/nctrl-bmi",
    author="Nahyun Kim, Dohoung Kim",
    packages=["nctrl"],
    entry_points={
        "console_scripts": [
            "nctrl=nctrl.cli:main",
        ]
    }
)
