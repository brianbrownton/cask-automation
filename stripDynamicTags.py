#!/usr/bin/env python

import re

def stripDynamicTags(incText):
    tmp = incText
    tmp = re.sub("<pubDate>.*</pubDate>","", incText, 0, flags=re.S|re.I)
    tmp = re.sub('<head.*</head>','', tmp, 0, flags=re.S|re.I)
    tmp = re.sub("<script.*</script>","", tmp, 0, flags=re.S|re.I)
    return tmp