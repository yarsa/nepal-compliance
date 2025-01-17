from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="nepal_compliance",
    version="0.0.1",
    description="ERPNext app to comply with Nepali laws and regulations",
    author="Yarsa Labs Pvt. Ltd.",
    author_email="support@yarsalabs.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)