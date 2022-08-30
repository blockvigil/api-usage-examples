from setuptools import setup, find_packages

setup(
    name='erc20-cli',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['erc20-cli=cli:cli']
    },
    classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
    install_requires=[
            'eth-utils == 1.6.1',
            'requests == 2.22.0',
            'eth-account == 0.5.9',
            'click == 7.0',
            'tornado == 6.0.3'
        ],
    version="0.1"
)