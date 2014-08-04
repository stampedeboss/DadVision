import dadvision

__author__ = 'AJ Reynolds'

with open('README.rst') as f:
    readme = f.read()
with open('HISTORY.rst') as f:
    history = f.read()

packages = ['dadvision']
requires = ['tmdb3', 'tvdb', 'tvrage', 'trakt', 'psutil', 'fuzzywuzzy', 'rpyc']
description = 'Python application designed to assst with maintaining a viddeo library.'

setup(
    name='dadvision',
    version=dadvision.__version__,
    description=description,
    long_description='\n'.join([readme, history]),
    author='AJ Reynolds',
    author_email='stampedeboss@gmail.com',
    url='https://github.com/stampedeboss/PyTrakt',
    packages=packages,
    install_requires=requires,
    zip_safe=False,
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: Freely Distributable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3')
)