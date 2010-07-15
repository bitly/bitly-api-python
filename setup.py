from setuptools import setup

version = '0.1.c'

setup(name='bitly_api',
      version=version,
      description="An API for bit.ly",
      long_description=open("./README.txt", "r").read(),
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Intended Audience :: End Users/Desktop",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
          "Topic :: Utilities",
          "License :: OSI Approved :: MIT License",
          ],
      keywords='bit.ly bitly j.mp jmp',
      author='Jehiah Czebotar',
      author_email='jehiah@gmail.com',
      url='http://github.com/bitly/bitly-api-python',
      license='MIT License',
      packages=['bitly_api'],
      include_package_data=True,
      zip_safe=True,
      )
