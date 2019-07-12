from setuptools import setup, find_packages

#packages=['lge'],
#package_dir={'': 'src/main/python'}
setup(
    name='confluence',
    version='0.1',
    zip_safe=False,
    description='Custom tools for Atlassian Product',
    author='Sunjoo Park',
    author_email='all4dich@gmail.com',
    package_dir={'': 'src'},
    packages=find_packages(where='src')
)
