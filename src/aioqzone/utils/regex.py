"""
some patterns for matching html and so on.
"""
import re

# use this to match qzone api response
response_callback = re.compile(r"callback\(\s*(\{.*\})\s*\)", re.S | re.I)
# use this to get unikey & curkey of a html
uni_cur_key = re.compile(r'data-unikey="([^"]*)"[^d]*data-curkey="([^"]*)"')
