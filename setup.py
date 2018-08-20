from setuptools import find_packages, setup
from channels_mqtt import __version__

setup(
    name='channel-mqtt',
    version=__version__,
    url='http://github.com/ruralscenery/channels_mqtt',
    author='blue',
    author_email='',
    description="django channels bridge with mqtt chient paho.",
    license='BSD',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=[
        'channels>=2.0',
        'paho-mqtt>=1.3.1',
    ],
    extras_require={
        'tests': [
        ],
    },
    classifiers=[
        "Framework :: Django",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
    ],
)