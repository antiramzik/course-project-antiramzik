from setuptools import find_packages, setup

setup(
    name="quiz-builder",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi==0.112.2",
        "uvicorn==0.30.5",
        "httpx==0.27.2",
    ],
)
