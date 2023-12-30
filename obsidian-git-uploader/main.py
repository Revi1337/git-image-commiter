import asyncio
import aiohttp
import json
import requests
import argparse
import re
import os
import base64
from urllib.parse import unquote, quote

"""
v3. multi image commit
    replace image-local-path to git-uploaded-link in markdown 
"""

HEADERS = {}

CREATE_BLOB_URL = 'https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/git/blobs'                            # post, body, token
GET_TREE_URL = 'https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/git/trees/{GITHUB_BRANCH}'               # get
CREATE_TREE_URL = 'https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/git/trees'                            # post, body, token
GET_BRANCH_LAST_REF = 'https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/git/refs/heads/{GITHUB_BRANCH}'   # get
COMMIT_URL = 'https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/git/commits'                               # post, body, token
UPDATE_REF_URL = 'https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/git/refs/heads/{GITHUB_BRANCH}'        # patch, body, token

PATTERN_1 = r"!\[.{0,}\]\((.*?)\)"
PATTERN_2 = r"!\[\[(.*?)\]\]"
PATTERN_3 = r"!\[.{0,}\]\((.*?)\)|!\[\[(.*?)\]\]"


def do_dispatch(image_abspaths_for_upload, markdown_line_imagelink_keypair, git_path):
    with requests.Session() as sess:
        asyncio.run(create_blob(sess, image_abspaths_for_upload, git_path))



async def create_blob(sess, image_abspaths_for_upload, git_path):
    blob_metadatas = build_blob_request_metadatas(image_abspaths_for_upload)
    async with aiohttp.ClientSession() as session:
        blob_responses = await asyncio.gather(
            *[build_blob(session, blob_keypair) for blob_keypair in blob_metadatas.items()]
        )
    create_tree(sess, blob_responses, git_path)



def build_blob_request_metadatas(image_abspaths_for_upload):
    metadatas = {}
    for upload_image in image_abspaths_for_upload:
        unquoted_image_path = unquote(upload_image)
        with open(unquoted_image_path, 'rb') as image:
            body = {
                'content': base64.b64encode(image.read()).decode("utf8"),
                'encoding': 'base64'
            }
            metadatas[unquoted_image_path] = body
    return metadatas



async def build_blob(sess, blob_keypair):
    upload_image, image_request_body = blob_keypair[0], blob_keypair[1]
    async with sess.post(url=CREATE_BLOB_URL, data=json.dumps(image_request_body), headers=HEADERS) as response:
        blob_res = await response.json()
        return { upload_image : blob_res['sha'] }



def create_tree(sess, blob_responses, git_path):
    root_tree_sha_for_basetree = get_root_tree_sha(sess)
    body = build_tree_request_body(root_tree_sha_for_basetree, blob_responses, git_path)
    # if body['tree']:
    create_tree_response = sess.post(url=CREATE_TREE_URL, data=json.dumps(body), headers=HEADERS).json()
    changed_tree_sha = create_tree_response['sha']
    do_commit(sess, changed_tree_sha)



def get_root_tree_sha(sess):
    root_tree_response = sess.get(url=GET_TREE_URL, headers=HEADERS).json()
    return root_tree_response['sha']



def build_tree_request_body(root_tree_sha_for_basetree, blob_responses, git_path):
    tree_values = []
    for blob_metadata in blob_responses:
        for upload_image, image_sha in blob_metadata.items():
            tree_values.append(
                {
                    'path': f'{git_path}/{os.path.basename(upload_image)}',
                    'mode': '100644',
                    'type': 'blob',
                    'sha': f'{image_sha}'
                }
            )
    return {
        'base_tree': f'{root_tree_sha_for_basetree}',
        'tree': tree_values
    }



def do_commit(sess, changed_tree_sha):
    last_branch_sha = get_branch_last_ref(sess)
    body = {
        'tree': f'{changed_tree_sha}',
        'message': 'Commited By Obsidian Git Plugin Made By @Revi1337',
        'parents':  [f'{last_branch_sha}']
    }
    commit_response = sess.post(url=COMMIT_URL, data=json.dumps(body), headers=HEADERS).json()
    commited_sha = commit_response['sha']
    update_ref(sess, commited_sha)



def update_ref(sess, commited_sha):
    body = { 'sha': f'{commited_sha}' }
    response = sess.patch(url=UPDATE_REF_URL, data=json.dumps(body), headers=HEADERS)
    if int(response.status_code) == 200:
        print('success commmit')



def get_branch_last_ref(sess):
    branch_last_ref_response = sess.get(url=GET_BRANCH_LAST_REF).json()
    return branch_last_ref_response['object']['sha']



def process_needto_upload(image_path, markdown_line_imagelink_keypair):
    """ filter duplicate imagelink and build pure image links """
    image_links = set(markdown_line_imagelink_keypair.values())
    return [os.path.join(image_path, image_link) for image_link in image_links]



def extract_image_from_markdown(markdown_file_path) -> dict[str, str]:
    wiki_link_list = {}
    with open(markdown_file_path, 'r', encoding='UTF-8') as file:
        for line_number, line in enumerate(file, 0):
            if not line:
                break
            line = line.strip('\n')
            match_regex = re.search(PATTERN_1, line) or re.search(PATTERN_2, line)
            if match_regex is not None:
                st_inx, end_idx = match_regex.span()
                if len(line) > len(line[st_inx : end_idx]):
                    continue
                url_links = re.findall(PATTERN_1, line) or re.findall(PATTERN_2, line)
                if url_links[-1].startswith("https://raw.githubusercontent.com"):
                    continue
                wiki_link_list[line_number] = url_links[-1]
    return wiki_link_list



def collect_images(image_path):
    return [os.path.join(image_path, image_name) for image_name in os.listdir(image_path)]



def parse_file_metadata(markdown_file_path, images_folder_name):
    file_path, markdown_file = os.path.split(markdown_file_path)
    image_path = os.path.join(file_path, images_folder_name)
    return os.path.basename(file_path), markdown_file, image_path



def initialize(arguments):
    global CREATE_BLOB_URL
    global GET_TREE_URL
    global CREATE_TREE_URL
    global GET_BRANCH_LAST_REF
    global COMMIT_URL
    global UPDATE_REF_URL

    HEADERS['Authorization'] = f'Bearer {arguments["token"]}'
    HEADERS['Accept'] = 'application/vnd.github+json'

    CREATE_BLOB_URL = f'https://api.github.com/repos/{arguments["username"]}/{arguments["repo"]}/git/blobs'
    GET_TREE_URL = f'https://api.github.com/repos/{arguments["username"]}/{arguments["repo"]}/git/trees/{arguments["branch"]}'
    CREATE_TREE_URL = f'https://api.github.com/repos/{arguments["username"]}/{arguments["repo"]}/git/trees'
    GET_BRANCH_LAST_REF = f'https://api.github.com/repos/{arguments["username"]}/{arguments["repo"]}/git/refs/heads/{arguments["branch"]}'
    COMMIT_URL = f'https://api.github.com/repos/{arguments["username"]}/{arguments["repo"]}/git/commits'
    UPDATE_REF_URL = f'https://api.github.com/repos/{arguments["username"]}/{arguments["repo"]}/git/refs/heads/{arguments["branch"]}'



def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', required=True, help='github username')
    parser.add_argument('--repo', required=True, help='github repo expected to be uploaded')
    parser.add_argument('--token', required=True, help='github token required to upload')
    parser.add_argument('--branch', required=True, help='github repo branch expected to be uploaded')
    parser.add_argument('--upload', required=True, nargs=2, metavar=('markdown_path', 'iamge_folder_name'),
                        help='markdown_path and iamge_folder_name')
    return parser.parse_args().__dict__



def guess_image_uploaded_address(arguments, git_path, markdown_line_imagelink_keypair):
    local_remote_keypair = {}
    for local_image in markdown_line_imagelink_keypair.values():
        local_remote_keypair[local_image] = \
            f'https://raw.githubusercontent.com/{arguments["username"]}/{arguments["repo"]}/{arguments["branch"]}/{git_path}/{local_image}'
    return local_remote_keypair



def replace_address_in_markdown(markdown_file_path, markdown_line_imagelink_keypair, local_remote_keypair):
    markdown_contents = open(markdown_file_path, encoding='UTF-8').readlines()
    with open(markdown_file_path, 'w+', encoding='UTF-8') as file:
        for line in range(len(markdown_contents)):
            if markdown_line_imagelink_keypair.get(line) is None:
                file.writelines(markdown_contents[line])
                continue
            future_change_links = re.findall(PATTERN_3, markdown_contents[line])
            if future_change_links:
                pattern1_link, pattern2_link = future_change_links[-1]
                if pattern1_link:
                    changed_link = markdown_contents[line].replace(pattern1_link, local_remote_keypair[pattern1_link])
                elif pattern2_link:
                    remote_link = local_remote_keypair[pattern2_link]
                    path, name = os.path.split(remote_link)
                    changed_link = f'![]({path}/{quote(name)})\n'
                else:
                    raise RuntimeError("error occured while replacing links in markdown")

            file.writelines(changed_link)


def main():
    # parse arguments and initialize web components
    arguments = parse_arguments()
    initialize(arguments)

    # parse markdown file to extract metatdata information of images that need to be uploaded and commited to github
    markdown_file_path, images_folder_name = arguments['upload']
    git_path, markdown_file, image_path = parse_file_metadata(markdown_file_path, images_folder_name)
    images = collect_images(image_path)
    markdown_line_imagelink_keypair = extract_image_from_markdown(markdown_file_path)
    image_abspaths_for_upload = process_needto_upload(image_path, markdown_line_imagelink_keypair)

    if not markdown_line_imagelink_keypair:
        raise RuntimeError("no files to upload.")

    # commit images to github
    do_dispatch(image_abspaths_for_upload, markdown_line_imagelink_keypair, git_path)

    # replace the image linked in markdown with the path to the images uploaded to github
    local_remote_keypair = guess_image_uploaded_address(arguments, git_path, markdown_line_imagelink_keypair)
    replace_address_in_markdown(markdown_file_path, markdown_line_imagelink_keypair, local_remote_keypair)


if __name__ == '__main__':
    main()
