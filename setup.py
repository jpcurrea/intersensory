from setuptools import setup

setup(name="ISR",
      version='0.1',
      description='Classes for unimodal and bimodal stimuli.',
      url="https://github.com/jpcurrea/intersensory.git",
      author='Pablo Currea',
      author_email='johnpaulcurrea@gmail.com',
      license='MIT',
      packages=['ISR'],
      setup_requires=['numpy']
      install_requires=[
          'matplotlib',
          'scipy',
          'pigpio',
          'pygame'
      ],
      zip_safe=False)
