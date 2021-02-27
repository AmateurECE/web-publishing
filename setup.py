import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="web-publishing",
    version="0.1.0",
    author="Ethan Twardy",
    author_email="ethan.twardy@gmail.com",
    description="Tools for publishing static documentation-style web pages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AmateurECE/web-publishing",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        'bs4',
        'cerberus',
        'importlib',
        'pyyaml',
    ],
    provides=['web_publishing'],
    entry_points={
        'console_scripts': [
            'wp-genmakefile=web_publishing.GenerateMakefile:main',
            'wp-navigation=web_publishing.Navigation:main',
            'wp-prepare=web_publishing.Prepare:main',
        ]
    }
)
