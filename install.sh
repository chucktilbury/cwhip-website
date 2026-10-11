#!/usr/bin/env bash
python3 build.py
scp -r site/* jhgfrgmy@50.6.19.179:~/public_html/website_a2dded8b/
