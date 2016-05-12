try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Simple NEF format parser',
    'author': 'TJ Ragan',
    'url': 'http://github.com/tragan',
    'download_url': 'http://github.com/tragan.',
    'author_email': 'tjr22@le.ac.uk',
    'version': '0.1',
    'install_requires': ['nose', 'numpy', 'pandas'],
    'packages': ['NEFreader'],
    'scripts': [],
    'name': 'NEFreader'
}

if __name__ == '__main__':
  setup(**config)