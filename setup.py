from setuptools import setup, find_packages

setup(
    name='twitstream',
    version='0.1',
    description="A simple asynchronous HTTP library in python for speaking with Twitter's streaming API, with numerous example applications",
    long_description="A simple asynchronous HTTP library in python for speaking with Twitter's streaming API, with numerous example applications",
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Web Environment",
    ],
    keywords='twitter,stream',
    author='Adam Lindsay',
    author_email='person@example.com',
    url='http://github.com/atl/twitstream',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['setuptools'],
)