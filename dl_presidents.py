#!/usr/bin/env python
# Based on code from Laurent Dinh (laurent-dinh)
# Author: Kyle Kastner
# License: BSD 3-Clause

from __future__ import print_function
import requests
import time
import random
from bs4 import BeautifulSoup
import urllib
import os
import io
import shutil
import subprocess
import stat


def pwrap(args, shell=True):
    p = subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                         universal_newlines=True)
    return p

# Print output
# http://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
def execute(cmd, shell=True):
    popen = pwrap(cmd, shell=shell)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line

    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def pe(cmd, shell=True):
    """
    Print and execute command on system
    """
    res = []
    for line in execute(cmd, shell=shell):
        print(line, end="")
        res.append(line)
    return res


# http://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
def download_file(url, filename):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian


url_opener = urllib.FancyURLopener()

def save_content(mp3_link, transcript, only_transcript=False):
    basename = mp3_link.split("/")[-1].split(".")[0]
    txt_name = basename + ".txt"
    mp3_name = basename + ".mp3"

    save_txt = "txt/" + txt_name
    save_mp3 = "mp3/" + mp3_name

    if not os.path.exists("mp3"):
        os.mkdir("mp3")

    if not os.path.exists("txt"):
        os.mkdir("txt")

    if not os.path.exists(save_mp3):
        if only_transcript:
            pass
        else:
            url_opener.retrieve(mp3_link, save_mp3)

    with open(save_txt, "w") as f:
        f.write(transcript)

    rr = pe("file %s" % save_mp3)
    if "HTML document" in rr[0] or "cannot open" in rr[0] or "No such" in rr[0]:
        print("mp3 file not found error for %s" % save_mp3)
        pe("rm %s" % save_txt)
        pe("rm %s" %  save_mp3)
        return

# need to collate all the links
all_links = []
for p_file in os.listdir("paginations"):
    if "presidential-speeches" not in p_file:
        continue
    with open("paginations/" + p_file, "r") as f:
        lines = f.readlines()
    content = "\n".join([line.strip() for line in lines])
    soup = BeautifulSoup(content, "html.parser")
    sub_links = [elem.get("href") for elem in soup.find_all("a")
                 if elem.get("class") is None
                 and elem.get("href") is not None
                 and "/the-presidency/presidential-speeches/" in elem.get("href")]
    all_links.extend(sub_links)

if not os.path.exists("sub_paginations"):
    os.mkdir("sub_paginations")

mp3_links = []
transcripts = []
for al in all_links:
    link_path = "https://millercenter.org" + al
    al_fname = al.split("/")[-1] + ".html"
    sub_pages = os.listdir("sub_paginations")
    if al_fname not in sub_pages:
        print("%s not found, downloading..." % al_fname)
        pe("wget %s -O %s" % (link_path, al_fname))
        pe("mv %s sub_paginations/" % al_fname)

    with open("sub_paginations/%s" % al_fname, "r") as f:
        lines = f.readlines()

    try:
        mp3_lines = [l for l in lines if ".mp3" in l and "?download" not in l]
        if len(mp3_lines) != 1:
            raise ValueError("Incorrect mp3 lines in %s" % al_fname)
        mp3_url_path = mp3_lines[0].split("src=")[-1].strip().replace('"', '')
        mp3_links.append(mp3_url_path)

        content = "\n".join([line.strip() for line in lines])
        soup = BeautifulSoup(content, "html.parser")
        raw_transcript = [" ".join(str(elem.find_all("div")[0]).split("\n")[2:-1])
                          for elem in soup.find_all("div")
                          if elem.get("class") is not None
                          and "expandable-text-container" in elem.get("class")][0]
        to_replace = ["</p>", "</br>", "<br/>", "</p>", "</em>", "<em>", "<p>", "<br>"]
        for r in to_replace:
            raw_transcript = raw_transcript.replace(r, " ")
        transcripts.append(raw_transcript)
    except Exception as e:
        mp3_lines = [l for l in lines if ".mp3" in l and "?download" not in l]
        if len(mp3_lines) < 1:
            continue
        print("Issue in %s" % al_fname)
        print(e)

assert len(transcripts) == len(mp3_links)

for n, (mp3_link, transcript) in enumerate(zip(mp3_links, transcripts)):
    time.sleep(random.random() * 5)
    try:
        print("Downloading %s" % mp3_link)
        save_content(mp3_link, transcript)
    except Exception as e:
        print("Failed %i: %s!" % (n, mp3_link))
        print(e)
        pass
