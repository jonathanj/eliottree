from setuptools import setup

setup(
    name='eliot-tree',
    version='17.1.0',
    description='Render Eliot logs as an ASCII tree',
    author='Jonathan Jacobs',
    url='https://github.com/jonathanj/eliottree',
    platforms='any',
    license='MIT',
    packages=['eliottree', 'eliottree.test'],
    test_suite='eliottree',
    entry_points={
        # These are the command-line programs we want setuptools to install.
        'console_scripts': [
            'eliot-tree = eliottree._cli:main',
        ],
    },
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Topic :: System :: Logging',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires=[
        "six>=1.9.0",
        "jmespath>=0.7.1",
        "iso8601>=0.1.10",
        "tree-format>=0.1.1",
        "termcolor>=1.1.0",
        "toolz>=0.8.2",
        "eliot>=0.12.0",
    ],
    extras_require={
        "dev": ["pytest>=2.7.1", "testtools>=1.8.0"],
    },
)
