import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sengled-client", # Replace with your own username
    version="0.0.2",
    author="Vincent Roy",
    author_email="vincentroy8@gmail.com",
    description="A simple python API client to control Sengled smart devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vroy/python-sengled-client",
    packages=["sengled"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "requests>=2.22.0"
    ]
)
