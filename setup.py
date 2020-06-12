from setuptools import setup, find_packages

setup(name='seaice',
      version='2.3.1',
      description=('CLIs and libraries for sea ice related computations.'),
      url='git@bitbucket.org:nsidc/seaice.git',
      author='NSIDC Development Team',
      author_email='programmers@nsidc.org',
      license='MIT',
      packages=find_packages(exclude=('*.tasks', '*.tasks.*', 'tasks.*', 'tasks',
                                      '*.test_data', '*.test_data.*', 'test_data.*', 'test_data')),
      include_package_data=True,
      zip_safe=False)
