import os
import codecs
import versioneer
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(HERE, *parts), 'rb', 'utf-8') as f:
        return f.read()


setup(
    name='eliot-tree',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='Render Eliot logs as an ASCII tree',
    license='MIT',
    url='https://github.com/jonathanj/eliottree',
    author='Jonathan Jacobs',
    author_email='jonathan@jsphere.com',
    maintainer='Jonathan Jacobs',
    maintainer_email='jonathan@jsphere.com',
    include_package_data=True,
    long_description=read('README.rst'),
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    entry_points={
        # These are the command-line programs we want setuptools to install.
        'console_scripts': [
            'eliot-tree = eliottree._cli:main',
        ],
    },
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: System :: Logging',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires=[
        'six>=1.9.0',
        'jmespath>=0.7.1',
        'iso8601>=0.1.10',
        'tree-format>=0.1.2',
        'termcolor>=1.1.0',
        'toolz>=0.8.2',
        'eliot>=0.12.0',
    ],
    extras_require={
        'test': ['testtools>=1.8.0'],
    },
)
