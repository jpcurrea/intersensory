from setuptools import setup

setup(name="ISR",
      version='0.1',
      description='Classes for unimodal and bimodal stimuli.',
      url="https://github.com/jpcurrea/intersensory.git",
      author='Pablo Currea',
      author_email='johnpaulcurrea@gmail.com',
      license='MIT',
      packages=['ISR'],
      install_requires=[
          'numpy',
          'scipy',
          'matplotlib',
          'pigpio',
          'pygame'
      ],
      zip_safe=False)
