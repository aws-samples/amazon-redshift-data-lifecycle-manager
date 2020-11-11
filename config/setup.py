from setuptools import setup

setup(
    name="validator",
    version="0.1",
    include_package_data=True,
    packages=["validator"],
    package_dir={
                'validator':'validator',
                 },
    package_data ={'validator':['validator.py','dataclasses.py']}
)