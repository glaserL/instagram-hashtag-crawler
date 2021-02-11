import sys
import json
from tqdm import tqdm
import urllib.request
from pathlib import Path
img_dir = "img"

Path(img_dir).mkdir(parents=True, exist_ok=True)
dump = {}

if len(sys.argv) > 1:
    with open(sys.argv[1], encoding="utf-8") as f:
        dump = json.load(f)
else:
    print(f"Please provide a link to a post dump json.")
    sys.exit(1)

for post_id, post in enumerate(tqdm(dump["posts"])):
    pic_url = post["pic_url"]
    file_name = f"img/{post_id}.png"
    urllib.request.urlretrieve(pic_url, file_name)
    post["file_name"] = file_name
    post["id"] = post_id

with open(sys.argv[1].replace(".json", "final.json"), "w", encoding="utf-8") as f:
    json.dump(dump["posts"], f, indent=2, ensure_ascii=False)
