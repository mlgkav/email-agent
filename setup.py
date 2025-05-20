from setuptools import setup, find_packages

setup(
    name="email_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "imap-tools>=1.0.0",
        "python-dotenv>=0.19.0",
        "prettytable>=2.0.0",
        "pre-commit>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "pgvector>=0.1.0",
        "openai>=1.0.0",
        "langchain>=0.1.0",
        "tiktoken>=0.5.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "email-agent=email_agent.cli.main:cli",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="An intelligent email management tool using RAG",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/email-agent",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
