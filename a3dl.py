#!/usr/bin/python3

import requests
import sys
import json
import re
import os
import argparse

savefmt = "mp4"
sourcefmt = "application/vnd.apple.mpegurl"

class A3Player:
    username = None
    password = None

    s = None

    urls = {
        "login": "https://servicios.atresplayer.com/j_spring_security_check",
    }

    channels = None
    debug = False

    def __init__(self, username, password, session=None, debug=None):
        self.username = username
        self.password = password
        self.debug = debug
        self.s = session if session else requests.Session()
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:62.0) Gecko/20100101 Firefox/62.0"
        })

    def login(self):

        logindata = {
            "j_username": username,
            "j_password": pw,
        }

        r = self.s.post(self.urls["login"], data=logindata)
        try:
            rep = r.json()
            if "error" in err:
                print(err)
                sys.exit(0)

        except Exception as e:
            pass

        print(r.text)

    def update_channels(self):
        self.channels = self.get("https://api.atresplayer.com/client/v1/info/channels")

    def get_channel(self, title):
        for channelmeta in self.channels:
            if channelmeta["title"] == title:
                link = channelmeta["link"]
                href = link["href"]
                channeldata = self.get(href)
                return channeldata

    #def get_channel_categories(self, channeldata, category):
        
            
    def get_programs_by_category(self, channeldata, category):
        for row in channeldata["rows"]:
            if row["title"] == category:
                href = row["href"]
                return self.get(href)

    def get_category_programs(self, category, program):
        for row in category["itemRows"]:
            if row["title"] == program:
                link = row["link"]
                href = link["href"]
                return self.get(href)

    def get_program_chapters(self, programmeta):
        for row in programmeta["rows"]:
            if row["title"][:3] == "Cap": #"Cap\xedtulos".encode("utf8"):
                href = row["href"]
                return self.get(href)

    def get_latest_chapter(self, chapters):
        chapter = chapters["itemRows"][0]
        link = chapter["link"]
        href = link["href"]
        return self.get(href)

    def get_chapter_video(self, chapter):
        #print json.dumps(chapter, indent=2)
        urlvideo = chapter["urlVideo"]
        return self.get(urlvideo)

    def get_video_url(self, video, mime):
        #print json.dumps(video, indent=2)
        omniture = video["omniture"]
        title = "{channel} - {format} - {season} - {name}".format(**omniture) 

        sources = video["sources"]
        for source in sources:
            if source["type"] == mime:
                return source["src"], title

    def get(self, href):
        if self.debug:
            print("URL", href)
        r = self.s.get(href)
        #data = json.loads(r.text.encode("utf8"))
        data = r.json()
        #print json.dumps(data, indent=2)
        return data



def ffdl(source, path, title, fmt):
    filename = "{}.{}".format(title, fmt)
    filepath = "{}/{}".format(path, filename)
    os.system("ffmpeg -i \"{}\" -c:v copy -c:a copy -f {} \"{}\"".format(source, fmt, filepath))


if __name__ == '__main__':
    cmdline = argparse.ArgumentParser()
    cmdline.add_argument("-u", "--username", type=str, required=True)
    cmdline.add_argument("-p", "--password", type=str, required=True)
    cmdline.add_argument("-c", "--channel", type=str)
    cmdline.add_argument("-s", "--section", type=str)
    cmdline.add_argument("-n", "--program", type=str)
    
    cmdline.add_argument("-t", "--saveto", type=str)
    cmdline.add_argument("-d", "--debug", action="store_true")

    args = cmdline.parse_args()

    a3p = A3Player(args.username, args.password, debug=args.debug)
    
    a3p.update_channels()

    channeldata = a3p.get_channel(args.channel)

    sectiondata = a3p.get_programs_by_category(channeldata, args.section)
    programmeta = a3p.get_category_programs(sectiondata, args.program)
    program_chapters = a3p.get_program_chapters(programmeta)

    latest = a3p.get_latest_chapter(program_chapters)

    video = a3p.get_chapter_video(latest)
    videourl, title = a3p.get_video_url(video, sourcefmt)
    
    if args.debug:
        print(videourl, title)
    
    if args.saveto:
        ffdl(videourl, args.saveto, title, savefmt)
