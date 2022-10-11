#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
import random
import datetime
import time
import json
import glob

def get_random_user_agent():
    with open('ua.json', 'r', encoding='utf8') as fp_ua:
        return random.choice(json.load(fp_ua))

def login_jasper():
    # Login into Jasper and save the session cookies
    print(':: Logging-in')

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'user-agent={get_random_user_agent()}')
    chrome_options.add_argument('user-data-dir=./chrome-prefs')

    driver_path = glob.glob('./chromedriver*')[0]
    print(f':: Found driver path : {driver_path}')

    print(':: Starting webdriver Chrome...')
    browser_handle = webdriver.Chrome(executable_path=driver_path, options=chrome_options)

    print(':: Setting random window size...')
    browser_handle.set_window_size(random.randint(1280, 1920), random.randint(720, 1080))

    print(':: Connecting')
    browser_handle.get('https://app.jasper.ai/')

    try:
        print(':: Waiting until we have an email address field (Expecting a timeout otherwise)')
        WebDriverWait(browser_handle, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div/div/div[3]/div/form/div[1]/div/input')))
    except:
        # Assume we're already logged-in
        print('\n:: Caught TimeoutException, assuming already logged-in.')
        return

    with open('creds.json', 'r', encoding='utf8') as creds_fp:
        print(':: Submitting username keys...')
        username_value = json.load(creds_fp)['username']
        username_field = browser_handle.find_element(By.ID, 'email')
        username_field.clear()
        username_field.send_keys(username_value)
        username_field.submit()

        # User will now manually log-in
        # So we'll wait 10 minutes 'till we have a dashboard available
        print(f'\n:: Please enter the code sent at { username_value } - waiting 10 minutes for you to do it.\n')
        WebDriverWait(browser_handle, 600).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div[1]/div/div[2]/div[2]/div/div[1]/button[2]')))

    print(':: Found Jasper.ai dashboard')
    print(':: Closing window.')
    browser_handle.close()

def run_prompts(prompts_list):
    # Initialize a new browser window
    # Assume we're already logged-in
    print('\n:: Starting prompt step')
    print(f':: Prompts to generate : {len(prompts_list)}')

    print(':: Initializing webdriver...')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'user-agent={get_random_user_agent()}')
    chrome_options.add_argument('user-data-dir=./chrome-prefs')

    driver_path = glob.glob('./chromedriver*')[0]
    print(f':: Found driver path : {driver_path}')

    print(':: Starting webdriver Chrome...')
    browser_handle = webdriver.Chrome(executable_path=driver_path, options=chrome_options)

    print(':: Setting window size...')
    browser_handle.set_window_size(random.randint(1280, 1920), random.randint(720, 1080))

    print(':: Getting Jasper.ai...')
    browser_handle.get('https://app.jasper.ai/')

    print(':: Entering edit page...')

    try_count = 0

    while True:
        if try_count == 5:
            print('* Aborting script. Too many failed attempts to enter ql-editor !')
            sys.exit(1)

        try:
            print(':: Trying to enter ql-editor...')
            WebDriverWait(browser_handle, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div[1]/div/div[2]/div[2]/div/div[2]/div[1]/button/button'))).click()
            WebDriverWait(browser_handle, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div[1]/div/div[5]/div/div/div/div/ul/li[1]/div'))).click()
            break

        except:
            print(f'* Warning : Failed to enter ql-editor ! (attempt { try_count })')
            try_count += 1
            continue

    composed_list = []

    for prompt_line in prompts_list:
        try_count = 0

        while True:
            if try_count == 20:
                print('* Aborting script. Too many failed attempts to clear ql-editor ! (Check internet connection ?)')
                sys.exit(1)

            try:
                print('\n:: Clearing ql-editor')
                input_editor = WebDriverWait(browser_handle, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ql-editor')))
                time.sleep(2)
                input_editor.clear()
                break

            except:
                print(f'* Warning : Failed to clear ql-editor ! (attempt { try_count })')
                continue

        time.sleep(2)
        print(':: Sending prompt keys')
        input_editor.send_keys(prompt_line)
        time.sleep(2)

        print(':: Highlighting the prompt and generating...')
        actions = ActionChains(browser_handle)

        input_editor.send_keys(Keys.PAGE_DOWN)

        actions.key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()

        print(':: Waiting for Jasper to finish...')
        time.sleep(15)

        print(':: Saving composed prompt...')
        composed_prompt = browser_handle.find_element(By.CLASS_NAME, 'ql-editor')
        composed_list.append([prompt_line, composed_prompt.text])
        time.sleep(2)

    print(':: Closing window.')
    browser_handle.quit()

    return composed_list

def split_list(lst, n):
    # Yield successive n-sized chunks from lst.
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

if __name__ == '__main__':
    print(':: Jasper auto prompt script')
    print('----------------------------')

    print('\n:: Loading prompts in-memory...\n')
    prompt_list = None

    with open('query.json', 'r', encoding='utf8') as prompt_fp:
        prompt_list = json.load(prompt_fp)

    login_jasper()

    time_start = datetime.datetime.now().replace(microsecond=0)
    now = datetime.datetime.now().strftime('%Y-%m-%d')

    for prompts_block in split_list(prompt_list, 25):
        composed_list = run_prompts(prompts_block)

        print('\n:: Saving composed prompts to filesystem...\n')
        os.makedirs('./output/', exist_ok=True)

        with open(f'./output/composed_{now}.csv', 'a', encoding='utf8') as f_composed:
            for composed_line in composed_list:
                f_composed.write(f'"{str(composed_line[0]).rstrip()}","{str(composed_line[1]).strip(composed_line[0]).strip()}"\n')

        if len(prompts_block) < 50:
            # No need to wait after finishing the last prompt block
            break

        hours_waiting = random.randint(1,4)
        print(f':: Waiting for { hours_waiting } hours...\n')
        time.sleep(60 * 60 * hours_waiting)

    time_end = datetime.datetime.now().replace(microsecond=0)
    runtime = time_end - time_start

    print('\n:: Script done !')
    print(':: Stats -------------------------')
    print(f':: Script runtime : { runtime }')
    print(f':: Composed prompts : { len(prompt_list) }\n')
