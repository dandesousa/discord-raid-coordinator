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
      packages=find_packages("src"),
      package_dir={"": "src"},
      include_package_data=True,
      install_requires=[
        'discord.py>=0.16.8',
        'pytz>=2017.2',
      ],
      test_suite='setup.my_test_suite',
      entry_points={'console_scripts': ['raid_coordinator = raid_coordinator.bot:main']}
      )
