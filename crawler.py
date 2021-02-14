import json
import os
from re import findall
from time import sleep
import os
from random import gauss
from tqdm import tqdm


def wait(mu, sigma=3.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            time_to_sleep = abs(gauss(mu, sigma))
            sleep(time_to_sleep)
            return ret

        return wrapper

    return decorator


class ProfileDict:
    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._dict, f, indent=2, ensure_ascii=False)

    def __init__(self, path, api):
        self.path = path
        self.api = api
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self._dict = json.load(f)
                print(f"Loaded {len(self._dict)} users from disk.")
        else:
            self._dict = {}

    def get(self, user_id):
        if str(user_id) in self._dict.keys():
            return self._dict[str(user_id)]
        elif int(user_id) in self._dict.keys():
            return self._dict[int(user_id)]

        else:
            user = self.get_profile_from_instagram(user_id)
            self.add(user_id, user)
            return user

    def add(self, user_id, user_dict):
        self._dict[user_id] = user_dict
        self.save()

    @wait(8, 4)
    def get_profile_from_instagram(self, user_id):
        result = self.api.user_info(user_id)
        return result


def crawl(api, hashtag, config):
    profiles = ProfileDict("profiles.json", api)

    if visit_profile(api, hashtag, config, profiles):
        pass


def add_comments(api, posts, config):
    for post in tqdm(posts):
        user_id = post['user']['pk']
        try:
            if post["comment_count"] > 0:
                comments = get_comments(api, post["id"], post["comment_count"])
            else:
                comments = []
            post["comments"] = comments
            if post["comment_count"] > 0:
                break
        except Exception as e:
            print(f"Failed to get comments. {e}")
            break
    return posts


def crawl_users(api, user_ids, target_path_for_profiles, config):
    profiles = ProfileDict(target_path_for_profiles, api)
    for user_ids in tqdm(user_ids):
        _ = profiles.get(user_ids)
    return profiles


def visit_profile(api, hashtag, config, profiles):
    while True:
        try:
            processed_tagfeed = {
                'posts': []
            }
            feed = get_posts(api, hashtag, config)
            with open(config['profile_path'] + os.sep + str(hashtag) + '_rawfeed.json', 'w') as outfile:
                json.dump(feed, outfile, indent=2)
            posts = [beautify_post(api, post, profiles) for post in feed]
            posts = list(filter(lambda x: not x is None, posts))
            if len(posts) < config['min_collect_media']:
                return False
            else:
                processed_tagfeed['posts'] = posts[:config['max_collect_media']]

            try:
                if not os.path.exists(config['profile_path'] + os.sep): os.makedirs(config['profile_path'])
            except Exception as e:
                print('exception in profile path')
                raise e

            try:
                with open(config['profile_path'] + os.sep + str(hashtag) + '.json', 'w') as outfile:
                    json.dump(processed_tagfeed, outfile, indent=2)
            except Exception as e:
                print('exception while dumping')
                raise e
        except Exception as e:
            print('exception while visiting profile', e)
            if str(e) == '-':
                raise e
            return False
        else:
            return True


@wait(6.0)
def get_comments(api, id, no_of_comments):
    all_comments = []
    comments = api.media_comments(id, count=min(no_of_comments, 20))
    all_comments.extend([comment for comment in comments["comments"]])
    return all_comments


def extract_relevant_from_comments(j):
    result = {
        "name": j["user"]["username"],
        "full_name": j["user"]["full_name"],
        "text": j["text"]
    }
    return result


def beautify_post(api, post, profiles):
    try:
        if post['media_type'] != 1:  # If post is not a single image media
            return None
        keys = post.keys()
        # print(post)
        user_id = post['user']['pk']
        comments = get_comments(api, post["id"], post["comment_count"])
        profile = profiles.get(user_id)

        processed_media = {
            'user_id': user_id,
            'username': profile['user']['username'],
            'full_name': profile['user']['full_name'],
            'profile_pic_url': profile['user']['profile_pic_url'],
            'media_count': profile['user']['media_count'],
            'follower_count': profile['user']['follower_count'],
            'following_count': profile['user']['following_count'],
            'date': post['taken_at'],
            'pic_url': post['image_versions2']['candidates'][0]['url'],
            'like_count': post['like_count'] if 'like_count' in keys else 0,
            'comment_count': post['comment_count'] if 'comment_count' in keys else 0,
            'caption': post['caption']['text'] if 'caption' in keys and post['caption'] is not None else '',
            'comments': comments
        }
        processed_media['tags'] = findall(r'#[^#\s]*', processed_media['caption'])
        # print(processed_media['tags'])
        return processed_media
    except Exception as e:
        print('exception in beautify post')
        raise e


@wait(8.0)
def request_posts_from_instagram(api, hashtag, rank_token, max_id=None):
    if max_id is None:
        results = api.feed_tag(hashtag, rank_token=rank_token)
    else:
        results = api.feed_tag(hashtag, rank_token=rank_token, max_id=max_id)
    print(f"Successfully requested {len(results.get('items', ''))} more for {hashtag} ({max_id})..")
    return results


@wait(7.5, 2.0)
def request_likers(api, post_id, count):
    return api.media_likers(post_id, count=count)


def add_likers(api, raw_data, config):
    for post in raw_data:
        try:
            like_count = post["like_count"]
            likers = post.get("likers", [])
            if like_count > 0 and len(likers) < like_count:
                num_of_likers_to_get = min(50, post["like_count"])
                new_likers = request_likers(api, post["id"], num_of_likers_to_get)
                likers.extend(new_likers)
            likers = list(set(likers))
            post["likers"] = likers
        except Exception as e:
            print(e)
            break
    return raw_data


def get_posts(api, hashtag, config):
    feed = []
    uuid = api.generate_uuid(return_hex=False, seed='0')
    result = request_posts_from_instagram(api, hashtag, uuid)
    feed.extend(result.get("items", []))
    while result["more_available"] and len(feed) < config['max_collect_media']:
        try:
            next_max_id = result["next_max_id"]
            result = request_posts_from_instagram(api, hashtag, uuid, next_max_id)
            feed.extend(result.get("items", []))
        except Exception as e:
            print(e)
            break
    print(f"Collected {len(feed)} posts for hashtag {hashtag}")
    return feed
