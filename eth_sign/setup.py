from setuptools import setup, find_packages

setup(
    name='ethsign-cli',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['ethsign-cli=eth_sign_cli:cli']
    },
    classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
    install_requires=[
            'eth-utils == 1.7.0',
            'requests == 2.22.0',
            'eth-account == 0.5.9',
            'click == 7.0',
            'tornado == 6.0.3',
            'eth_abi == 2.0.0'
        ],
    version="0.1"
)