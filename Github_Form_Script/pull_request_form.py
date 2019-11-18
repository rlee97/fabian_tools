import requests
import pandas as pd
import sys, getopt, os
import configparser
import logging
from enum import Enum
import ast
from time import time

from pprint import pprint


vyaire_repos_base = 'https://api.github.com/repos/vyaire/' # Add repository
vyaire_pull_req_base = 'https://api.github.com/repos/vyaire/fabian-gui/pulls?state=closed&per_page=' # Add number


# Configuring the logger this will be used as a global over the whole program
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename="pull_request_form.log", level=logging.DEBUG, format=LOG_FORMAT, filemode='w')
logger = logging.getLogger()


authentication = [None, None]


class Indexing(Enum):
    USERNAME = 0
    PASSWORD = 1
    CONFIG_COMMIT_START = 0
    CONFIG_COMMIT_END = 1
    CLASS_REPO_NAME = 0
    CLASS_COMMIT_START = 1
    CLASS_COMMIT_END = 2
    CLASS_REPO_BRANCH = 3


class Repositories(Enum):
    # Repository, Start commit, End commit
    fabian_gui = ['fabian-gui', None, None, 'master']
    fabian_monitor = ['fabian-monitor', None, None, 'master']
    fabian_controller = ['fabian-controller', None, None, 'master']
    fabian_alarm = ['fabian-alarm', None, None, 'master']
    fabian_blender = ['fabian-blender', None, None, 'master']
    fabian_power = ['fabian-power', None, None, 'master']
    fabian_power_evo = ['fabian-power-evo', None, None, 'master']
    fabian_hfo = ['fabian-hfo', None, None, 'master']
    fabian_controller_bootloader = ['fabian-controller_bootloader', None, None, 'master']
    fabian_alarm_bootloader = ['fabian-alarm_bootloader', None, None, 'master']
    fabian_monitor_bootloader = ['fabian-monitor_bootloader', None, None, 'master']
    fabian_hfo_bootloader = ['fabian-hfo_bootloader', None, None, 'master']


class Columns(Enum):
    df_files = 'files'
    df_filenames = 'filename'
    df_users = 'user'


class PRItems(Enum):
    title = 'title'
    user = 'user'
    merged_at = 'merged_at'
    parents = 'parents'
    sha = 'sha'


class QueryItems(Enum):
    pulls = '/pulls/'
    commits = "/commits/"
    commit_break = " || "


class FormHeader(Enum):
    pr_num = 'PR #'
    submitter = 'Submitter'
    merged_date = 'Merged Date'
    title = 'Title'
    reviewers = 'Reviewers'
    files = 'Files'
    commits = 'Commits'


class MiscValues(Enum):
    COMMIT_LENGTH = 40
    COMMIT_BREAK_SIZE = len(QueryItems.commit_break.value)
    PR_ITEM_LENGTH = 11


class PullRequestForm:

    def __init__(self):
        pd.set_option("display.max_columns", 500)
        pd.set_option("display.max_rows", 500)
        pd.set_option("display.max_colwidth", 500)

    def generate_form(self, auth_info):
        for repo in Repositories:
            if repo.value[Indexing.CLASS_COMMIT_START.value] is None or repo.value[Indexing.CLASS_COMMIT_END.value] is None:  # We do not find pull request for these repos
                logging.debug("Will not generate output for " + repo.value[Indexing.CLASS_REPO_NAME.value])
            else:  # We find the commits for these repos
                # Get output form from each repository
                output_form = self.get_all_commits(auth_info, vyaire_repos_base + repo.value[Indexing.CLASS_REPO_NAME.value], repo.value[Indexing.CLASS_COMMIT_START.value], repo.value[Indexing.CLASS_COMMIT_END.value])
                self.make_form(repo.value[Indexing.CLASS_REPO_NAME.value], output_form)

    def get_all_commits(self, auth_info, input_query, start_commit, end_commit):
        final_commit = end_commit
        # Final output
        final_output = []
        headers_info = {'Accept': 'application/vnd.github.groot-preview+json'}

        # Getting the following commits
        start_time = time()
        while final_commit != start_commit:
            commit_json = requests.get(input_query + QueryItems.commits.value + final_commit, auth=auth_info).json()
            commits_pulls_json = requests.get(input_query + QueryItems.commits.value + final_commit + '/pulls', auth=auth_info, headers=headers_info).json()

            # Get the pull requests number from the commits here
            try:
                pull_number = commits_pulls_json[0]['number']
            except KeyError:
                logging.warning("Incorrect Credentials")
                break

            # Get the pull request reviewers and numbers here
            pull_json = requests.get(input_query + QueryItems.pulls.value + str(pull_number), auth=auth_info).json()

            reviewers = self.get_review_list(auth_info, input_query + QueryItems.pulls.value + str(pull_number) + '/reviews')

            merged_date = pull_json[PRItems.merged_at.value]
            pull_title = pull_json[PRItems.title.value]
            submitter = pull_json[PRItems.user.value]['login']

            files = [file['filename'] for file in commit_json['files']]

            last_commit = final_commit
            final_commit = commit_json[PRItems.parents.value][0][PRItems.sha.value]
            title_commit = commit_json['commit']['message']
            newline_index = title_commit.find('\n')
            if newline_index == -1:
                final_title_commit = title_commit
            else:
                final_title_commit = title_commit[:(newline_index)]
            # PR #, Submitter, Merged Date, Title, Reviewers, Files, Commits
            final_output.append([pull_number, submitter, merged_date, pull_title, reviewers, '\n'.join(files), last_commit + " || " + final_title_commit])

            cur_time = time()
            if cur_time - start_time > 900: # If we have waited longer than 15 minutes we break out
                logger.warning("Could not find all commits within the 15 minute window")
                break

        final_output = pd.DataFrame(final_output)

        return final_output

    def get_review_list(self, auth_info, query):
        # This will generate the reviewer list
        review_json = requests.get(query, auth=auth_info).json()
        df = pd.DataFrame.from_dict(review_json).query('state == "APPROVED"', engine='python')
        users = df[Columns.df_users.value].apply(lambda x: x.get('login'))
        df[Columns.df_users.value] = users
        df.drop_duplicates(subset=[Columns.df_users.value], keep='last', inplace=True)
        return_review_list = list(df.loc[:, Columns.df_users.value])
        return '\n'.join(return_review_list)

    def make_form(self, repo_name, input_pr_list):
        # This will make the output form for the repository
        col_map = {0:FormHeader.pr_num.value, 1:FormHeader.submitter.value, 2:FormHeader.merged_date.value, 3:FormHeader.title.value, 4:FormHeader.reviewers.value, 5:FormHeader.files.value, 6:FormHeader.commits.value}

        input_pr_list.rename(columns=col_map, inplace=True)

        input_pr_list.to_csv(str(repo_name) + '.csv')
        input_pr_list.to_html(str(repo_name) + '.html')


class ConfigurationParser:
    def __init__(self, input_file):
        dir_list = os.listdir(os.getcwd())
        if input_file in dir_list:
            config = configparser.ConfigParser()
            config.read(input_file)

            # COMMITS in Config file
            fabian_gui_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_gui']))
            fabian_monitor_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_monitor']))
            fabian_controller_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_controller']))
            fabian_alarm_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_alarm']))
            fabian_blender_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_blender']))
            fabian_power_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_power']))
            fabian_power_evo_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_power_evo']))
            fabian_hfo_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_hfo']))
            fabian_controller_bootloader_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_controller_bootloader']))
            fabian_alarm_bootloader_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_alarm_bootloader']))
            fabian_monitor_bootloader_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_monitor_bootloader']))
            fabian_hfo_bootloader_commits = self.check_commits(ast.literal_eval(config['COMMITS']['fabian_hfo_bootloader']))

            # Copying over to the class
            Repositories.fabian_gui.value[Indexing.CLASS_COMMIT_START.value] = fabian_gui_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_gui.value[Indexing.CLASS_COMMIT_END.value] = fabian_gui_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_monitor.value[Indexing.CLASS_COMMIT_START.value] = fabian_monitor_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_monitor.value[Indexing.CLASS_COMMIT_END.value] = fabian_monitor_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_controller.value[Indexing.CLASS_COMMIT_START.value] = fabian_controller_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_controller.value[Indexing.CLASS_COMMIT_END.value] = fabian_controller_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_alarm.value[Indexing.CLASS_COMMIT_START.value] = fabian_alarm_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_alarm.value[Indexing.CLASS_COMMIT_END.value] = fabian_alarm_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_blender.value[Indexing.CLASS_COMMIT_START.value] = fabian_blender_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_blender.value[Indexing.CLASS_COMMIT_END.value] = fabian_blender_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_power.value[Indexing.CLASS_COMMIT_START.value] = fabian_power_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_power.value[Indexing.CLASS_COMMIT_END.value] = fabian_power_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_power_evo.value[Indexing.CLASS_COMMIT_START.value] = fabian_power_evo_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_power_evo.value[Indexing.CLASS_COMMIT_END.value] = fabian_power_evo_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_hfo.value[Indexing.CLASS_COMMIT_START.value] = fabian_hfo_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_hfo.value[Indexing.CLASS_COMMIT_END.value] = fabian_hfo_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_controller_bootloader.value[Indexing.CLASS_COMMIT_START.value] = fabian_controller_bootloader_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_controller_bootloader.value[Indexing.CLASS_COMMIT_END.value] = fabian_controller_bootloader_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_alarm_bootloader.value[Indexing.CLASS_COMMIT_START.value] = fabian_alarm_bootloader_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_alarm_bootloader.value[Indexing.CLASS_COMMIT_END.value] = fabian_alarm_bootloader_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_monitor_bootloader.value[Indexing.CLASS_COMMIT_START.value] = fabian_monitor_bootloader_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_monitor_bootloader.value[Indexing.CLASS_COMMIT_END.value] = fabian_monitor_bootloader_commits[Indexing.CONFIG_COMMIT_END.value]

            Repositories.fabian_hfo_bootloader.value[Indexing.CLASS_COMMIT_START.value] = fabian_hfo_bootloader_commits[Indexing.CONFIG_COMMIT_START.value]
            Repositories.fabian_hfo_bootloader.value[Indexing.CLASS_COMMIT_END.value] = fabian_hfo_bootloader_commits[Indexing.CONFIG_COMMIT_END.value]
        else:
            logger.warning("Missing INI file")


    def check_commits(self, input_commits):
        length = len(input_commits)
        temp_return = input_commits

        for commit in input_commits:
            if commit is None or len(commit) != MiscValues.COMMIT_LENGTH.value:
                temp_return = [None] * length
                break

        return temp_return


def print_help():
    help_output = '\n' \
                  'How to run:\n' \
                  '    python pull_request_form -u github_username -p github_password\n' \
                  '\n' \
                  'How to set up form.ini file:\n' \
                  '    fabian_gui = [first_commit, latest_commit]\n' \
                  '    Example:\n' \
                  '        fabian_gui = ["872ae671e4b33849dc45c41596f485f9bf1bdcc1", "9dd23dad0db0e21ec30ab4e56fd640e66d0f26f0"]\n' \
                  '\n' \
                  'This script will output a .csv and .html file based on the repository\n'

    print(help_output)

def main(args):
    logger.info("Pull Request Form Start:")

    password = None
    username = None
    for i in range(0, len(args)):
        if args[i] == '-u':
            username = args[i+1]
        elif args[i] == '-p':
            password = args[i+1]
        elif args[i] == '-h' or args[i] == 'help' or args[i] == '?':
            print_help()
            sys.exit()

    # INI file parser
    config = ConfigurationParser("form.ini")

    global authentication
    authentication[Indexing.USERNAME.value] = username
    authentication[Indexing.PASSWORD.value] = password

    # Pull Request Generated Form
    auth_info = tuple(authentication)
    if auth_info[0] is None or auth_info[1] is None:
        logger.warning("No authentication!")
    else:
        form = PullRequestForm()
        form.generate_form(auth_info)


if __name__ == "__main__":
   main(sys.argv[1:])
