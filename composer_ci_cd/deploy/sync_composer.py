import re
import click
from google.cloud import storage
from git import Repo


@click.command(name='sync')
@click.option('-b', '--bucket-name', default='your_default', required=True)
@click.option('-p', '--prefix', default='dags/')
@click.option('-f', '--folder', multiple=True, required=True)
@click.option('-s', '--last-commit-sha-file-name', required=True)
def sync(bucket_name, prefix, need_sync_folders, last_commit_sha_file_name):
    print()
    print('------------------------------------------------')
    print('---------- Starting cloud build script ---------')
    print('------------------------------------------------')

    git_repository_location = './'
    repository = Repo(git_repository_location)
    last_sync_sha_file_name = last_commit_sha_file_name

    print()
    print('------------------------------------------------')
    print('------------ Getting full GIT tree -------------')
    print('------------------------------------------------')

    git_fetch_command = ['--unshallow']
    repository.git.fetch(*git_fetch_command)

    print()
    print('------------------------------------------------')
    print('-- Getting last synced commit SHA from bucket --')
    print('------------------------------------------------')

    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    git_diff_tree_command = handle_last_synced_commit_file(bucket, last_sync_sha_file_name)

    print()
    print('------------------------------------------------')
    print('------------ Getting modified files ------------')
    print('------------------------------------------------')

    modified_files = []
    # Matches: A  root/folder/file
    type_and_name_pattern = re.compile(r'^(?P<modification_type>\w)\t(?P<full_file_name>.*)')
    diff_tree = repository.git.diff_tree(*git_diff_tree_command)
    if not diff_tree:
        print('No modified files to be synced')
        print('Exiting...')
        return

    for type_and_name in diff_tree.split('\n'):
        type_and_name_match = re.match(type_and_name_pattern, type_and_name)
        modified_files.append(
            ModifiedFile(
                modification_type=type_and_name_match.group('modification_type'),
                full_file_name=type_and_name_match.group('full_file_name'),
                need_sync_folders=need_sync_folders,
                prefix=prefix,
            )
        )

    print()
    print('------------------------------------------------')
    print('---------------- Syncing files -----------------')
    print('------------------------------------------------')

    for file in modified_files:
        if file.need_sync:
            if file.is_delete_type:
                handle_file_deletion(bucket, file)
                continue

            handle_file_upload(bucket, file)
            continue

        print(f'Skipping.... [ {file} ]')

    print()
    print('------------------------------------------------')
    print('-------- Getting last synced commit SHA --------')
    print('------------------------------------------------')

    git_last_commit_sha_command = ['HEAD']
    git_last_commit_sha = repository.rev_parse(*git_last_commit_sha_command).hexsha

    print()
    print('------------------------------------------------')
    print('----- Updating last synced commit SHA file -----')
    print('------------------------------------------------')

    updated_last_sync_commit_sha = bucket.blob(last_sync_sha_file_name)
    updated_last_sync_commit_sha.upload_from_string(git_last_commit_sha)


class ModifiedFile:
    def __init__(self, modification_type: str, full_file_name: str, need_sync_folders: tuple, prefix: str = ''):
        self.modification_type = modification_type.lower()
        self.full_file_name = full_file_name
        self.need_sync_folders = need_sync_folders
        self.prefix = prefix
        pattern = re.compile(r'^(?P<folder>[^/]*)/.*')  # Matches: root/folder/file
        match = re.match(pattern, full_file_name)
        self.folder_name = match.group('folder') if match and match.groups() else ''

    def __str__(self):
        return self.full_file_name

    @property
    def is_delete_type(self):
        return self.modification_type == 'd'

    @property
    def need_sync(self):
        return self.folder_name in self.need_sync_folders

    @property
    def bucket_file_name(self):
        return f'{self.prefix}{self.full_file_name}'


def handle_file_deletion(bucket, file):
    print(f'Deleting.... [ {file} ]')
    synced_bucket_file = bucket.blob(file.bucket_file_name)
    synced_bucket_file.delete()


def handle_file_upload(bucket, file):
    print(f'Uploading... [ {file} ]')
    synced_bucket_file = bucket.blob(file.bucket_file_name)
    synced_bucket_file.upload_from_filename(file.full_file_name)


def handle_last_synced_commit_file(bucket, last_sync_sha_file_name) -> list:
    try:
        last_sync_sha_file = bucket.get_blob(last_sync_sha_file_name)
        last_sync_commit_sha = last_sync_sha_file.download_as_text()
        return ['--no-commit-id', '--name-status', '-r', last_sync_commit_sha, 'HEAD']
    except Exception as exc:
        print('Unable to find last synced commit SHA file')
        print()
        print(f'Exception={exc}')
        print()
        print('Comparing with last commit as fallback')
        return ['--no-commit-id', '--name-status', '-r', 'HEAD']


if __name__ == '__main__':
    sync()
