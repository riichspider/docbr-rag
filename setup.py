"""
Setup script for docbr-rag package distribution.
"""

from setuptools import setup, find_packages
import pathlib

# Read the contents of README file
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8")

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Core requirements (exclude dev dependencies)
core_requirements = [
    req for req in requirements 
    if not any(dev_pkg in req for dev_pkg in [
        "pytest", "ruff", "mypy", "black", "isort", 
        "pre-commit", "mkdocs", "jupyter", "ipython"
    ])
]

setup(
    name="docbr-rag",
    use_scm_version={
        "write_to": "src/docbr_rag/_version.py",
        "fallback_version": "0.1.0",
    },
    setup_requires=["setuptools_scm"],
    
    # Package description
    description="RAG especializado em documentos brasileiros — 100% local e gratuito",
    long_description=README,
    long_description_content_type="text/markdown",
    
    # Author and license
    author="Seu Nome",
    author_email="seu@email.com",
    url="https://github.com/seu-usuario/docbr-rag",
    project_urls={
        "Bug Reports": "https://github.com/seu-usuario/docbr-rag/issues",
        "Source": "https://github.com/seu-usuario/docbr-rag",
        "Documentation": "https://github.com/seu-usuario/docbr-rag/wiki",
    },
    license="MIT",
    
    # Package discovery
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    
    # Dependencies
    install_requires=core_requirements,
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=5.0.0",
            "pytest-mock>=3.12.0",
            "pytest-asyncio>=0.21.0",
            "ruff>=0.4.0",
            "mypy>=1.10.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "pre-commit>=3.5.0",
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.4.0",
            "mkdocstrings[python]>=0.23.0",
        ],
        "gpu": [
            "torch-audio>=2.0.0",
            "torchvision>=0.15.0",
        ],
        "api": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "httpx>=0.24.0",
        ],
        "jupyter": [
            "jupyter>=1.0.0",
            "ipython>=8.15.0",
            "notebook>=7.0.0",
        ],
    },
    
    # Python version requirement
    python_requires=">=3.10",
    
    # Package classifiers
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
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Natural Language :: Portuguese (Brazilian)",
    ],
    
    # Keywords
    keywords=[
        "rag", "nlp", "brazil", "documentos", "llm", "pdf", 
        "nfe", "contrato", "boleto", "embedding", "vector-database"
    ],
    
    # Entry points
    entry_points={
        "console_scripts": [
            "docbr-rag=src.docbr_rag.cli:app",
        ],
    },
    
    # Package data
    package_data={
        "docbr_rag": [
            "*.yaml",
            "*.yml",
            "*.json",
        ],
    },
    
    # Zip safe
    zip_safe=False,
)
