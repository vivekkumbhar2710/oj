from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in outsourcing_jobwork/__init__.py
from outsourcing_jobwork import __version__ as version

setup(
	name="outsourcing_jobwork",
	version=version,
	description="This emphasizes the aspect of sending jobs to other businesses.",
	author="Quantbit Technologies Pvt ltd",
	author_email="contact@erpdata.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
