from setuptools import setup, find_packages

setup(
    name="desktop-commander-py",
    version="0.1.0",
    description="Python port of Desktop Commander MCP server for terminal operations and file editing",
    author="Original by Eduard Ruzga, Python port by You",
    author_email="you@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pydantic>=2.0.0",
        "psutil>=5.9.0",
        "rich>=13.4.0",
    ],
    entry_points={
        "console_scripts": [
            "desktop-commander-py=desktop_commander.mcp_server:main",
            "desktop-commander-py-setup=scripts.setup_claude_server:main"
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Source": "https://github.com/wonderwhy-er/ClaudeComputerCommander/tree/main/py",
        "Bug Reports": "https://github.com/wonderwhy-er/ClaudeComputerCommander/issues",
    },
)