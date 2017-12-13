''' setup script '''
from setuptools import setup

setup(
    name='Metaphinder',
    version='0.0.1',

    author='Mouse Reeve',
    author_email='mousereeve@riseup.net',

    packages=['bot'],

    license='MIT',
    install_requires=['TwitterAPI==2.4.2'],
)
