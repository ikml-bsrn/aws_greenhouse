from setuptools import setup, find_packages

setup(
    name='greenhouse-data-ingestion',
    version='0.1.0',
    description='A package for ingesting Greenhouse IoT data into AWS S3 Bucket via Data Firehose',
    author='IB',
    url="https://github.com/ikml-bsrn/aws_greenhouse",
    packages=find_packages(),
    install_requires=[
        'boto3',
        'moto',
        'requests'
    ]
)