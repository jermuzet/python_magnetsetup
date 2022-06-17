#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [ ]

setup_requirements = [ ]

test_requirements = ['pytest>=3', ]

setup(
    author="Christophe Trophime",
    author_email='christophe.trophime@lncmi.cnrs.fr',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python Magnet SetUp to create json and cfg files for simulation",
    entry_points={
        'console_scripts': [
            'python_magnetsetup=python_magnetsetup.setup:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords='python_magnetsetup',
    name='python_magnetsetup',
    packages=find_packages(include=['python_magnetsetup', 'python_magnetsetup.*', 'python_magnetsetup.workflows.*', 'python_magnetsetup.postprocessing.*']),
    package_data={'': [
        'settings.env', 
        'flow_params.json', 
        'magnetsetup.json', 
        'machines.json', 
        'templates/cfpdes/Axi/thelec/*.mustache', 
        'templates/cfpdes/Axi/thelec/*.json',
        'templates/cfpdes/Axi/thmag/*.mustache', 
        'templates/cfpdes/Axi/thmag/*.json',
        'templates/cfpdes/Axi/thmagel/*.mustache', 
        'templates/cfpdes/Axi/thmagel/*.json',
        'templates/cfpdes/Axi/thmqs/*.mustache', 
        'templates/cfpdes/Axi/thmqs/*.json',
        'templates/cfpdes/Axi/mqs/*.mustache', 
        'templates/cfpdes/Axi/mqs/*.json',
        'templates/cfpdes/Axi/mag/*.mustache', 
        'templates/cfpdes/Axi/mag/*.json',
        'templates/cfpdes/Axi/thmag_hcurl/*.mustache', 
        'templates/cfpdes/Axi/thmag_hcurl/*.json',
        'templates/cfpdes/Axi/thmagel_hcurl/*.mustache', 
        'templates/cfpdes/Axi/thmagel_hcurl/*.json',
        'templates/cfpdes/Axi/thmqs_hcurl/*.mustache', 
        'templates/cfpdes/Axi/thmqs_hcurl/*.json',
        'templates/cfpdes/Axi/mag_hcurl/*.mustache', 
        'templates/cfpdes/Axi/mag_hcurl/*.json',
        'templates/cfpdes/Axi/mqs_hcurl/*.mustache', 
        'templates/cfpdes/Axi/mqs_hcurl/*.json',
        'templates/cfpdes/3D/thelec/*.mustache', 
        'templates/cfpdes/3D/thelec/*.json',
        'templates/CG/3D/thelec/*.mustache', 
        'templates/CG/3D/thelec/*.json'
        ]},
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/Trophime/python_magnetsetup',
    version='0.1.0',
    zip_safe=False,
)
