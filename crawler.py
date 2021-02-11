import json
import os
from re import findall
from time import sleep
from random import gauss


def wait(mu, sigma=3.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            time_to_sleep = abs(gauss(mu, sigma))
            sleep(time_to_sleep)
            return ret

        return wrapper

    return decorator


def crawl(api, hashtag, config):
    # print('Crawling started at origin hashtag', origin['user']['username'], 'with ID', origin['user']['pk'])
    if visit_profile(api, hashtag, config):
        pass


def visit_profile(api, hashtag, config):
    while True:
        try:
            processed_tagfeed = {
                'posts': []
            }
            feed = get_posts(api, hashtag, config)[:5]
            with open(config['profile_path'] + os.sep + str(hashtag) + '_rawfeed.json', 'w') as outfile:
                json.dump(feed, outfile, indent=2)
            profile_dic = {}
            posts = [beautify_post(api, post, profile_dic) for post in feed]
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
    all_comments.extend([extract_relevant_from_comments(comment) for comment in comments["comments"]])
    return all_comments


def extract_relevant_from_comments(j):
    result = {
        "name": j["user"]["username"],
        "full_name": j["user"]["full_name"],
        "text": j["text"]
    }
    return result


@wait(0.5, .5)
def get_profile(api, user_id):
    result = api.user_info(user_id)
    user_name = result.get('user', {}).get("username", "")
    print(f"Got profile for {user_name}.")
    return result

def beautify_post(api, post, profile_dic):
    try:
        if post['media_type'] != 1:  # If post is not a single image media
            return None
        keys = post.keys()
        # print(post)
        user_id = post['user']['pk']
        profile = profile_dic.get(user_id, False)
        comments = get_comments(api, post["id"], post["comment_count"])
        if profile is False:
            profile = get_profile(api, user_id)
            profile_dic[user_id] = profile

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


def request_posts_from_instagram(api, hashtag, rank_token, max_id=None):
    if max_id is None:
        results = api.feed_tag(hashtag, rank_token=rank_token)
    else:
        results = api.feed_tag(hashtag, rank_token=rank_token, max_id=max_id)
    print(f"Successfully requested {len(results.get('items', ''))} more for {hashtag} ({max_id})..")
    return results


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

#
# def get_posts(api, hashtag, config):
# 	try:
# 		feed = []
# 		try:
# 			uuid = api.generate_uuid(return_hex=False, seed='0')
# 			results = api.feed_tag(hashtag, rank_token=uuid, min_timestamp=config['min_timestamp'])
# 		except Exception as e:
# 			print('exception while getting feed1')
# 			raise e
# 		feed.extend(results.get('items', []))
#
# 		if config['min_timestamp'] is not None: return feed
#
# 		next_max_id = results.get('next_max_id')
# 		while next_max_id and len(feed) < config['max_collect_media']:
# 			print("next_max_id", next_max_id, "len(feed) < max_collect_media", len(feed) < config['max_collect_media'] , len(feed))
# 			try:
# 				results = api.feed_tag(hashtag, rank_token=uuid, max_id=next_max_id)
# 			except Exception as e:
# 				print('exception while getting feed2')
# 				if str(e) == 'Bad Request: Please wait a few minutes before you try again.':
# 					sleep(60)
# 				else:
# 					raise e
# 			feed.extend(results.get('items', []))
# 			next_max_id = results.get('next_max_id')
#
# 		return feed
#
# 	except Exception as e:
# 		print('exception while getting posts')
# 		raise e
#
