from setuptools import setup, find_packages
import unittest


def my_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite


setup(name='pokemon-go-raid-bot',
      version='0.0.2',
      author='Daniel DeSousa',
      author_email='pgo-raid-bot@daniel.desousa.cc',
      packages=find_packages("src"),
      package_dir={"": "src"},
      include_package_data=True,
      install_requires=[
        'discord.py>=0.16.8',
        'pytz>=2017.2',
      ],
      test_suite='setup.my_test_suite',
      entry_points={'console_scripts': ['raid_bot = raid_bot.bot:main', 'channel_repair = raid_bot.channels:main']}
      )
