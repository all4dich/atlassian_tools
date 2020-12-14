from atlassian_tools.confluence.common import Confluence

c = Confluence("http://collab.lge.com/main", "allessunjoo.park", "Yooahrim1!")
r2 = c.get_attachments("NC50", "starfish-jcl4tv-official-o20 #60", expand_list="", media_type="")
for each_r in r2:
    print(each_r['title'])
