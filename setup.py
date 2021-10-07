from setuptools import setup, find_packages

setup(
    name="thishappened",
    version='0.1',
    author="Greger Stolt Nilsen",
    author_email="gregersn@gmail.com",
    description="A utility to convert markdown to images",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    packages=find_packages(),
    python_requires=">=3.9",
    entry_points={
        'console_scripts': [
            'thishappened = thishappened.cli:main'
        ]
    }
)
