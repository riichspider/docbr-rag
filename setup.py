from setuptools import setup, find_packages
from pathlib import Path

HERE = Path(__file__).parent

README = (HERE / "README.md").read_text(encoding="utf-8")

requirements_file = HERE / "requirements.txt"

if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
else:
    requirements = []

core_requirements = [
    req for req in requirements
    if not any(
        dev_pkg in req.lower()
        for dev_pkg in [
            "pytest",
            "ruff",
            "mypy",
            "black",
            "isort",
            "pre-commit",
            "mkdocs",
            "jupyter",
            "ipython",
        ]
    )
]

setup(
    name="docbr-rag",
    version="0.1.0",

    description="RAG especializado em documentos brasileiros — 100% local e gratuito",
    long_description=README,
    long_description_content_type="text/markdown",

    author="riichspider",
    url="https://github.com/riichspider/docbr-rag",

    project_urls={
        "Source": "https://github.com/riichspider/docbr-rag",
        "Issues": "https://github.com/riichspider/docbr-rag/issues",
    },

    license="MIT",

    package_dir={"": "src"},
    packages=find_packages(where="src"),

    include_package_data=True,
    zip_safe=False,

    python_requires=">=3.10",

    install_requires=core_requirements,

    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=5.0.0",
            "pytest-mock>=3.12.0",
            "pytest-asyncio>=0.21.0",
            "ruff>=0.4.0",
            "mypy>=1.10.0",
            "black>=24.0.0",
            "isort>=5.13.0",
            "pre-commit>=3.6.0",
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.5.0",
            "mkdocstrings[python]>=0.24.0",
        ],
        "api": [
            "fastapi>=0.110.0",
            "uvicorn[standard]>=0.27.0",
            "httpx>=0.27.0",
        ],
        "gpu": [
            "torch>=2.2.0",
            "torchvision>=0.17.0",
        ],
        "jupyter": [
            "jupyter>=1.0.0",
            "ipython>=8.18.0",
            "notebook>=7.1.0",
        ],
    },

    entry_points={
        "console_scripts": [
            "docbr-rag=docbr_rag.cli:app",
        ],
    },

    package_data={
        "docbr_rag": [
            "*.json",
            "*.yaml",
            "*.yml",
        ],
    },

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries",
        "Natural Language :: Portuguese (Brazilian)",
    ],

    keywords=[
        "rag",
        "llm",
        "nlp",
        "pdf",
        "embedding",
        "vector-database",
        "documentos",
        "brazil",
    ],
)