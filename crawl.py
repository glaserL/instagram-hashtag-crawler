#!/usr/bin/python
# -*- coding: utf-8 -*- 
# @File Name: crawl.py
# @Created:   2017-05-21 12:30:29  seo (simon.seo@nyu.edu) 
# @Updated:   2017-05-21 13:41:42  Simon Seo (simon.seo@nyu.edu)

import os.path
import argparse
from tqdm import tqdm
from time import sleep
import sys
import json
from util import file_to_list
from crawler import crawl, crawl_users, get_posts, add_comments, add_likers
import pathlib

from instagram_private_api import (
    Client, __version__ as client_version)

if __name__ == '__main__':
    available_tasks = ["get_users", "get_posts", "get_comments"]
    parser = argparse.ArgumentParser(description='Crawling')
    parser.add_argument('-u', '--username', dest='username', type=str, required=True)
    parser.add_argument('-p', '--password', dest='password', type=str, required=True)
    parser.add_argument('-t', '--hashtag', dest='hashtag', type=str, required=True)
    parser.add_argument('tasks', metavar='N', type=str, nargs='+',
                        help=f'the tasks to execute ({available_tasks})')
    parser.add_argument('--profiles', dest='path_to_profiles', type=str, required=False)
    parser.add_argument('--max', dest='max_collect_media', type=int, required=False, default=10)

    args = parser.parse_args()
    config = {'search_algorithm': 'BFS', 'profile_path': './hashtags', 'min_collect_media': 1,
              'min_timestamp': None, "max_collect_media": args.max_collect_media}

    user_name = args.username
    password = args.password
    if user_name is not None and password is not None:
        api = Client(args.username, args.password)
    else:
        sys.exit(0)

    raw_path = pathlib.Path("new_tags", args.hashtag)
    pathlib.Path(raw_path).mkdir(parents=True, exist_ok=True)
    if "get_posts" in args.tasks:
        raw_data = get_posts(api, args.hashtag, config)
        with open(f"{raw_path}.json", "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
    else:
        with open(f"{raw_path}.json", encoding="utf-8") as f:
            raw_data = json.load(f)
    if "get_users" in args.tasks:
        user_ids = list(set(post['user']['pk'] for post in raw_data))
        if args.path_to_profiles is not None:
            target_path_for_profiles = args.path_to_profiles
        else:
            target_path_for_profiles = f"{raw_path}_profiles.json"
        _ = crawl_users(api, user_ids, target_path_for_profiles, config)
    if "get_comments" in args.tasks:
        raw_data = add_comments(api, raw_data, config)
        with open(f"{raw_path}_comments.json", "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
    if "get_likers" in args.tasks:
        raw_data = add_likers(api, raw_data, config)
        with open(f"{raw_path}_likers.json", "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
