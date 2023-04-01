"""Setup configuration rushd.
For local development, use
`pip install -e .[dev]`
which will install additional dev tools.
"""

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="internal-acme-dns",
    version="0.0.1",
    author="Christopher Johnstone",
    author_email="meson800@gmail.com",
    description="Package for maintaining robust, reproducible data management.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/meson800/internal-acme-dns",
    project_urls={
        "Bug Tracker": "https://github.com/meson800/internal-acme-dns",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Topic :: Utilities",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "dnslib",
        "toml",
    ],
    extras_require={
        "dev": [
            "pre-commit",
            "ruff",
            "build",
            "twine",
        ]
    },
)
