from atlassian_tools.confluence.common import Confluence

c = Confluence("http://localhost:1990/confluence", "admin","admin")
r2 = c.get_attachments("ds", "Lay out your page (step 6 of 9)", expand_list="", media_type="")
for each_r in r2:
    print(each_r['title'])
