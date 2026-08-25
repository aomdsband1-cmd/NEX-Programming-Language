from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="nex-lang",
    version="1.1.0",
    description="NEX Programming Language - A lightweight scripting language with .N extension and Python integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="NEX",
    author_email="nex@nex-lang.dev",
    url="https://github.com/nex-lang/nex-lang",
    project_urls={
        "Documentation": "https://github.com/nex-lang/nex-lang/blob/main/docs/language-spec.md",
        "Source": "https://github.com/nex-lang/nex-lang",
        "Tracker": "https://github.com/nex-lang/nex-lang/issues",
    },
    py_modules=["interpreter"],
    entry_points={
        "console_scripts": [
            "nex=interpreter:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Interpreters",
        "Topic :: Software Development :: Compilers",
        "Topic :: Education",
    ],
    python_requires=">=3.8",
    license="MIT",
    keywords="language interpreter scripting nex .N programming",
)
