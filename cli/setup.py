from io import open
from setuptools import setup, find_packages


setup(
    name='fathom-web',
    version='3.7.3',
    description='Commandline tools for training Fathom rulesets',
    long_description=open('README.rst', 'r', encoding='utf8').read(),
    author='Erik Rose',
    author_email='erik@mozilla.com',
    license='MPL',
    packages=find_packages(exclude=['*.test']),
    url='https://mozilla.github.io/fathom/',
    install_requires=[
        'click>=7.0,<8.0',
        'more-itertools>=8.2,<9.0',
        'numpy>=1.18.1,<1.24.0',
        'filelock>=3.0.12',
        'scikit-learn>=0.22.2',
        'selenium>=4.10.0,<5.0',
        'tensorboardX>=1.6,<2.0',
        'torch>=1.0,<2.0',
        'protobuf <= 3.20.1',
    ],
    dependency_links=[
        'https://download.pytorch.org/whl/cu110/torch_stable.html'
    ],
    entry_points={'console_scripts': [
        'fathom = fathom_web.commands:fathom',
    ]},
    package_data={'': ['fathom.zip']},
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python :: 3'
    ],
    keywords=['machine learning', 'ml', 'semantic extraction'],
)
