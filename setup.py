from setuptools import setup, find_packages

setup(
    name             = 'git_image_commiter',
    version          = '1.0.0',
    description      = 'Git Image Commiter',
    author           = 'Revi1337',
    author_email     = 'david122123@gmail.com',
    url              = '',
    download_url     = '',
    install_requires = [
        'requests',
        'beautifulsoup4',
        'clipboard',
        'Markdown',
        'aiohttp'
    ],
	include_package_data=True,
	packages         = find_packages(),
    entry_points     = {
        'console_scripts': [
            'image_commit = git_image_commiter.image_upload:main'
        ]
    },
    keywords         = [
        'GIT COMMITER',
        'git commiter',
        'IMAGE COMMITER',
        'image commiter'
    ],
    python_requires  = '>=3',
    zip_safe=False,
    classifiers      = [
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows"
    ]
)