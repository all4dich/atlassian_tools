from setuptools import setup, find_packages

setup(
    name='atlassian_tools',
    version='0.1',
    zip_safe=False,
    description='Custom tools for Atlassian Product',
    author='Sunjoo Park',
    author_email='all4dich@gmail.com',
    package_dir={'': 'src/main/python/'},
    packages=find_packages(where='src/main/python/')
)
