from setuptools import setup, find_packages
import unittest


def my_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite


setup(name='discord-raid-coordinator',
      version='0.1.0',
      author='Daniel DeSousa',
      author_email='discord-raid-coordinator@daniel.desousa.cc',
      license='UNLICENSE',
      packages=find_packages("src"),
      package_dir={"": "src", "": ["LICENSE"]},
      include_package_data=True,
      install_requires=[
        'discord.py>=0.16.8',
        'pytz>=2017.2',
      ],
      platforms='any',
      test_suite='setup.my_test_suite',
      entry_points={'console_scripts': ['raid_coordinator = raid_coordinator.bot:main']},
      classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      ],
)
