from setuptools import setup

setup(
    name="saturn-run",
    entry_points={
        "console_scripts": [
            "saturn = saturn_run.cli:cli",
        ]
    },
)
