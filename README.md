# obsidian-git-uploader

Utility for `Obsidian` to Upload Image Automatically

## Table of Contents

  * [Installation](#installation)
  * [Usage](#Usage)
  * [Quick start](#quick-start)
  * [Features](#features)
  
## Installation

Download using pip via PyPI.

```bash
$ pip install git_image_commiter
```

or 

Download using git.

```bash
$ git clone https://github.com/Revi1337/git-image-commiter.git
$ cd git-image-commiter
$ python setup.py install
```

## Usage

```bash
$ image_commit -h
usage: image_commit [-h] --username USERNAME --repo REPO --token TOKEN --branch BRANCH --upload markdown_abs_path image_folder_name --gitpath GITPATH

options:
  -h, --help            show this help message and exit
  --username USERNAME   github username
  --repo REPO           github repo expected to be uploaded
  --token TOKEN         github token required to upload
  --branch BRANCH       github repo branch expected to be uploaded
  --upload markdown_abs_path image_folder_name
                        specify markdown absolute path and name of the folder containing the images
  --gitpath GITPATH     specify the path to the github repository where the image will be saved.
```

## Quick start

```bash
$ image_commit [-h] --username USERNAME 
                    --repo REPO 
                    --token TOKEN 
                    --branch BRANCH 
                    --upload markdown_abs_path image_folder_name 
                    --gitpath GITPATH
```

## Features

  * Utility for Uploading Image to Git
