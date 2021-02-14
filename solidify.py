import json
import pprint
with open("hashtags_malu/waldgang_rawfeed.json", encoding="utf-8") as f:
    data = json.load(f)

with open("profiles.json", encoding="utf-8") as f:
    profiles = json.load(f)


pretty = []
for i, post in enumerate(data):
    pprint.pprint(post)
    user = profiles[post["user"]["username"]]
    pretty_post = {
        'id' : i,
        'user_id': user['user_id'],
        'username': user['username'],
        'full_name': user['full_name'],
        'profile_pic_url': user['profile_pic_url'],
        'media_count': user['media_count'],
        'follower_count': user['follower_count'],
        'following_count': user['following_count'],
        'date': post['taken_at'],
        'pic_url': post['image_versions2']['candidates'][0]['url'],
        'like_count': post['like_count'],
        'comment_count': post['comment_count'],
        'caption': post['caption']['text']
    }
