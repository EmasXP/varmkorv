from setuptools import find_packages, setup

setup(
    name='Varmkorv',
    packages=find_packages(include=['varmkorv']),
    version='0.1.0',
    description='A proof-of-concept CherryPy inspired Python micro framework',
    author='Magnus Karlsson',
    license='MIT',
    install_requires=[
        'werkzeug',
    ],
)