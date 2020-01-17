#!/usr/bin/python3
# -*- coding: utf8 -*-

"""
Author: Jeeva
Description: Download video courses from linkedin learning.
"""

import argparse
import os
import platform
import re
import requests
from selenium import webdriver
from slugify import slugify
import sys
from time import sleep


class Bot:
    def __init__(self):
        self.args = self.parse_arguments()
        self.email = self.args.email
        self.password = self.args.password
        self.url = "https://www.linkedin.com/learning/me"
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        if not self.args.show_window:
            options.add_argument("--headless")
        options.add_argument("--log-level=3")
        options.add_argument("--mute-audio")
        
        if platform.system() == "Windows":
            self.browser = webdriver.Chrome("./chromedriver.exe", options=options)
        else:
            self.browser = webdriver.Chrome("./chromedriver", options=options)

    def parse_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-e", "--email", help="Linkedin learning login email address")
        parser.add_argument("-p", "--password", help="Linkedin learning login password")
        parser.add_argument("-w", "--show-window", default=False, action="store_true", help="Show browser window")
        return parser.parse_args()

    def run(self):
        self.browser.get(self.url)
        print("[+] Signing in ...")
        self.browser.execute_script("""
            var email = document.querySelector("input[type='email']");
            var submit = document.querySelector("#auth-id-button");
            email.value = "{}";
            submit.disabled = false;
            submit.click();
        """.format(self.email))
        self.wait_for("#password")
        self.browser.execute_script("""
            var password = document.querySelector("#password");
            password.value = "{}";
            document.querySelector("button[type='submit']").click();
        """.format(self.password))
        self.wait_for("input[placeholder='Search for skills, subjects or software']")

        url = input("Eneter a course URL: ")
        url_pattern = re.compile(r"^http(s)?:\/\/\w+\.[a-z]{2,3}(.*)$")

        if url_pattern.match(url):
            try:
                Downloader(self.browser).download(url)
            except: pass
        else:
            print("Err: Invalid URL")

        self.browser.quit()

    def wait_for(self, id):
        while True:
            is_exist = self.browser.execute_script("""
                return document.querySelector("{}") !== null;
            """.format(id))
            if is_exist:
                break
            sleep(0.1)


class Downloader:
    def __init__(self, browser):
        self.browser = browser
        self.video_urls = []

    def download(self, url):
        self.browser.get(url)
        sleep(5)
        total_videos = self.browser.execute_script("""
            var urls = [];
            var btns = document.querySelectorAll(".classroom-toc-chapter__toggle");
            for (var i = 0; i < btns.length; i++) { 
                if (btns[i].getAttribute("aria-expanded") === "false") {
                    btns[i].click()
                }
            }

            var items = document.querySelectorAll("a[data-control-name='toc_item']");
            return items.length;
        """)

        folder_name = input("Enter a folder name to save videos: ")
        try:
            os.mkdir(folder_name)
        except FileExistsError:
            pass
        _, _, files = next(os.walk(folder_name))
        index = len(files)
        for i in range(total_videos):
            video_title = self.browser.execute_script("""
                var item = document.querySelectorAll("a[data-control-name='toc_item']")[{}];

                if (item.textContent.indexOf("question") === -1) {{
                    item.click()
                }}
                return item.querySelector(".classroom-toc-item-layout__title").textContent.trim()
            """.format(i))
            sleep(5)

            video_url = self.browser.execute_script("""
                return document.querySelector("video").src
            """)

            if video_url not in self.video_urls:
                print("Downloading ... {}".format(video_title))
                self.download_file(folder_name, slugify(video_title), video_url, index)
                self.video_urls.append(video_url)
                index += 1

        print("Done.")

    def download_file(self, folder_name, file_name, url, index):
        res = requests.get(url, stream=True)
        video_file = open("{}/{}. {}.mp4".format(folder_name, index, file_name), "wb+")
        file_size = res.headers.get("content-length")
        if file_size is None:
            video_file.write(res.content)
        else:
            dl = 0
            file_size = int(file_size)
            for data in res.iter_content(chunk_size=4096):
                dl += len(data)
                video_file.write(data)
                done = int(50 * dl / file_size)
                progress = int(dl / file_size * 100)
                if progress < 10:
                    progress = "  {}".format(progress)
                elif progress < 100:
                    progress = " {}".format(progress)
                sys.stdout.write("\r{}% |{}{}|".format(progress, "█" * done, " " * (50-done)) )    
                sys.stdout.flush()
            print()


if __name__ == "__main__":
    Bot().run()
