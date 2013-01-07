from setuptools import setup

version = '0.2'

setup(name='bitly_api',
      version=version,
      description="An API for bit.ly",
      long_description=open("./README.md", "r").read(),
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
      keywords='bitly bit.ly',
      author='Jehiah Czebotar',
      author_email='jehiah@gmail.com',
      url='https://github.com/bitly/bitly-api-python',
      download_url="https://bitly-downloads.s3.amazonaws.com/bitly_api/bitly_api-%s.tar.gz" % version,
      license='MIT License',
      packages=['bitly_api'],
      include_package_data=True,
      zip_safe=True,
      )
