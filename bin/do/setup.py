from setuptools import find_packages
from setuptools import setup


setup(
    name='ebdo',
    version='1.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'pexpect',
    ],
    entry_points={
        'console_scripts': [
            'ebdo=cli:cli'
        ]
    },
)
