from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


version = '0.1'

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    'click',
    'gevent',
    'pyserial',
    'salesforce-requests-oauthlib',
    'salesforce-streaming-client',
]


setup(name='c64-serial-proxy',
    version=version,
    description="",
    long_description=README + '\n\n' + NEWS,
    classifiers=[
    ],
    keywords='c64 salesforce dreamforce',
    author='Adam J. Lincoln',
    author_email='alincoln@salesforce.com',
    url='https://github.com/SalesforceFoundation/c64-salesforce-demo',
    license='BSDv3',
    packages=find_packages('src'),
    package_dir = {'': 'src'},include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        'console_scripts':
            ['c64-serial-proxy=c64serialproxy:main']
    }
)
