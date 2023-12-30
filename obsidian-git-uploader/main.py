"""
@Author Revi1337

Reference

- https://siddharthav.medium.com/push-multiple-files-under-a-single-commit-through-github-api-f1a5b0b283ae
- https://docs.github.com/ko/rest/git/trees?apiVersion=2022-11-28#about-git-trees
- https://gist.github.com/quilicicf/41e241768ab8eeec1529869777e996f0
- 파일 모드 : 100644파일(blob), 100755실행 파일(blob), 040000하위 디렉터리(트리), 160000하위 모듈(커밋) 또는 120000심볼릭 링크의 경로를 지정하는 blob 중 하나 입니다.

"""

import json
import time
import aiohttp
import asyncio


HEADERS = {
    'Authorization': 'Bearer {YOUR TOKEN}',
    'Accept': 'application/vnd.github+json'
}


CREATE_BLOB_URL = f'https://api.github.com/repos/Revi1337/BlogImageFactory/git/blobs'               # post, body, token
GET_TREE_URL = f'https://api.github.com/repos/Revi1337/BlogImageFactory/git/trees/main'             # get
CREATE_TREE_URL = f'https://api.github.com/repos/Revi1337/BlogImageFactory/git/trees'               # post, body, token
GET_BRANCH_LAST_REF = f'https://api.github.com/repos/Revi1337/BlogImageFactory/git/refs/heads/main' # get
COMMIT_URL = f'https://api.github.com/repos/Revi1337/BlogImageFactory/git/commits'                  # post, body, token
UPDATE_REF_URL = f'https://api.github.com/repos/Revi1337/BlogImageFactory/git/refs/heads/main'      # patch, body, token



async def update_ref(sess, commited_sha):
    body = { 'sha': f'{commited_sha}' }
    async with sess.patch(url=UPDATE_REF_URL, data=json.dumps(body), headers=HEADERS) as response:
        res_json = await response.json()
        if int(response.status) == 200:
            print('success commmit')



async def do_commit(sess, changed_tree_sha):
    last_branch_sha = await get_branch_last_ref(sess)
    body = {
        'tree': f'{changed_tree_sha}',
        'message': 'Commited By Obsidian Git Plugin Made By @Revi1337',
        'parents':  [f'{last_branch_sha}']
    }
    async with sess.post(url=COMMIT_URL, data=json.dumps(body), headers=HEADERS) as response:
        commit_response = await response.json()
        commited_sha = commit_response['sha']
        await update_ref(sess, commited_sha)



async def get_branch_last_ref(sess):
    async with sess.get(url=GET_BRANCH_LAST_REF) as response:
        branch_last_ref_response = await response.json()
        return branch_last_ref_response['object']['sha']



async def create_tree(sess, blob_sha, blob_url):
    root_tree_sha_for_basetree = await get_root_tree_sha(sess)
    body = {
        'base_tree': f'{root_tree_sha_for_basetree}',
        'tree': [
            {
                'path': 'zzzzz/dummy.py',
                'mode': '100644',
                'type': 'blob',
                'sha': f'{blob_sha}'
            }
        ]
    }
    async with sess.post(url=CREATE_TREE_URL, data=json.dumps(body), headers=HEADERS) as response:
        create_tree_response = await response.json()
        changed_tree_sha = create_tree_response['sha']
        await do_commit(sess, changed_tree_sha)



async def get_root_tree_sha(sess):
    async with sess.get(url=GET_TREE_URL, headers=HEADERS) as response:
        root_tree_response = await response.json()
        return root_tree_response['sha']



async def create_blob(sess):
    body = { "content": "print('hello world')", "encoding": "utf-8" }
    async with sess.post(url=CREATE_BLOB_URL, data=json.dumps(body), headers=HEADERS) as response:
        create_blob_response = await response.json()
        blob_sha, blob_url = create_blob_response['sha'], create_blob_response['url']
        await create_tree(sess, blob_sha, blob_url)



async def do_dispatch():
    async with aiohttp.ClientSession() as sess:
        await create_blob(sess)



async def main():
    return await do_dispatch()


if __name__ == '__main__':
    st_time = time.perf_counter()
    asyncio.run(main())
    end_time = time.perf_counter() - st_time
    print(end_time)
