from setuptools import setup, find_packages

setup(
    name='bookcrossing',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'Flask==2.0.1',
        'SQLAlchemy==1.4.22',
        'Flask-Login==0.5.0',
        'Flask-WTF==0.15.1',
        'WTForms==2.3.3',
        'Werkzeug==2.0.1',
        'python-dotenv==1.0.0',
    ],
    author='Павел Клеников, Павел Шмелев',
    description='Веб-приложение для буккроссинга',
)