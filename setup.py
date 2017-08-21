from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    'python-dateutil',
]

setup_requirements = [
]

test_requirements = [
    'pytest',
]

entry_points = {
    'console_scripts': [
        'ledger-to-beancount = ledger_to_beancount.__main__:main',
    ]
}


setup(name='ledger-to-beancount',
      version='0.0.1',
      description='Another converter from ledger to beancount',
      long_description=readme,
      license='Apache License (2.0)',
      classifiers=[
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: Implementation :: CPython',
          'License :: OSI Approved :: Apache Software License',
      ],
      keywords='beancount ledger accounting',
      author='Ethan Glasser-Camp',
      author_email='ethan@betacantrips.com',
      url='https://github.com/glasserc/ledger-to-beancount/',
      packages=find_packages(),
      test_suite='tests',
      install_requires=requirements,
      tests_require=test_requirements,
      setup_requires=setup_requirements,
      entry_points=entry_points,
)
