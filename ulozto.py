#uložto sťahuvačka, vznikla jak cli verzia pre sťahuvaní súborov a jak vhodná alternatíva
#pre mobilné apky keré neni ždy sranda obsluhuvať
#Morc, 1.12.2023

import requests, json, os, configparser
from getpass import getpass
from urllib.parse import urlparse
config = configparser.ConfigParser()
config['ulozto'] = {}
settings = config['ulozto']

def link(uri, label=None):
    if label is None: 
        label = uri
    parameters = ''

    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST 
    escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'

    return escape_mask.format(parameters, uri, label)
    
def cfg_save():
	with open('ulozto.cfg', 'w') as cfgfile:
		config.write(cfgfile)

def get_session_cookie():
	params = {
	    'key': 'logreg',
	}
	
	response = requests.head('https://uloz.to/login', params=params)
	for cookie in response.cookies:
		settings[cookie.name] = cookie.value

def login():
	#first stage - initiating login
	headers = {
	    'X-Auth-Token': settings['x_auth_token'],
	    'Accept': 'application/json',
	    'Sec-Fetch-Site': 'same-site',
	    'Sec-Fetch-Mode': 'cors',
	    'Origin': 'https://uloz.to',
	    'Referer': 'https://uloz.to/',
	    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
	    'Connection': 'keep-alive',
	    'Host': 'apis.uloz.to',
	    'Sec-Fetch-Dest': 'empty',
	    'Content-Type': 'application/x-www-form-urlencoded',
	}
	
	data = '{"success_url":"ulozto:\\/\\/login-success","error_url":"ulozto:\\/\\/login-error"}'
	
	request = requests.post('https://apis.uloz.to/v5/auth/login-request/', headers=headers, data=data, cookies={'_nss': '1'})
	response = json.loads(request.text)
	
	settings["login_user_token"] = response['token']
	temp_login_url = response['url']


	#second stage - authentication
	headers = {
	    'X-Auth-Token': settings['x_auth_token'],
	    'Content-Type': 'application/x-www-form-urlencoded',
	}
	
	username = input("Username: ")
	password = getpass("Password: ")
	
	data = {
	    'username': username,
	    'password': password, 
	    'fakeUsername': '',
	    'fakePassword': '',
	    '_do': 'loginForm-form-submit',
	}
	
	request = requests.post(temp_login_url, headers=headers, data=data,allow_redirects=False, cookies={'_nss': '1'})
	
	for cookie in request.cookies:
		settings[cookie.name] = cookie.value
		
		
	#third stage - getting real user token, user name and user id
	cookies = {
	    'ULOSESSID': settings['ulosessid'],
	    'uloztoid': settings['uloztoid'],
	    'permanentLogin3': settings['permanentlogin3'],
	    'adblock_detected': 'false',
	    'uloztoid2': settings['uloztoid'],
	}
	
	headers = {
	    'Accept': 'application/json, text/plain, */*',
	    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
	    'Referer': 'https://uloz.to/fm?_fid=zq8m',
	    'Connection': 'keep-alive'
	}
	
	request = requests.get('https://uloz.to/p-api/get-api-current-user-token', cookies=cookies, headers=headers)
	response = json.loads(request.text)
	
	settings['loggeduserid'] = str(response['loggedUserId'])
	settings['loggedusername'] = response['loggedUserName']
	settings['user_token'] = response['token']

	print("Successfully logged in as " + settings['loggedusername'] + " with the ID " + settings['loggeduserid'])
	cfg_save()

def download_file(slug, captcha_token = None):

	headers = {
	    'X-Auth-Token': settings['x_auth_token'],
	    'X-User-Token': settings['user_token'],
	    'Content-Type': 'application/x-www-form-urlencoded',
	}
	
	if captcha_token is not None:
		data = '{"captcha_token":"' + captcha_token + '","user_login":"370network","file_slug":"' + slug + '","device_id":"be3655f4c7978625"}'
	else:
		data = '{"user_login":"' + settings['loggedusername'] + '","file_slug":"' + slug + '","device_id":"be3655f4c7978625"}'
	
	request = requests.post('https://apis.uloz.to/v5/file/download-link/free', cookies={'_nss': '1'}, headers=headers, data=data)
	response = json.loads(request.text)
	if 'link' in response:
		print("Link is valid until " + response['download_url_valid_until'])
		print("Download link: " + link(response['link']))
		return False, None
	else:
		print(str(response['code']) + " | " + response['message'])
		if response['code'] == 403:
			print("This file can't be downloaded anymore")
			return False, None
		elif response['code'] == 422:
			print("Input file link doesn't seem to come from Ulož.to")
			return False, None
		elif response['code'] == 401:
			return True, response['data']['captcha_token']
		else:
			return False, None

def captcha_request(captcha_token):	
	headers = {
	    'X-Auth-Token': settings['x_auth_token'],
	    'X-User-Token': settings['user_token'],
	    'Content-Type': 'application/x-www-form-urlencoded',
	}
	
	data = '{"success_url":"ulozto:\\/\\/captcha-success","cancel_url":"ulozto:\\/\\/captcha-cancel","error_url":"ulozto:\\/\\/captcha-error"}'
	
	request = requests.post('https://apis.uloz.to/v5/captcha/' + captcha_token + '/url', cookies={'_nss': '1'}, headers=headers,data=data)
	response = json.loads(request.text)
	print("Captcha link: " + link(response['url']))
	
print("Uložto sťahuvačka")	
get_session_cookie()
if not os.path.isfile('ulozto.cfg'): #je šanca že apka sa pustila prvý raz
	print('Uložto sťahuvačka | First run')
	settings['x_auth_token'] = "}p^YyPpxkIT2MB)#!MHE"
	login()

config.read('ulozto.cfg')

while True:
	download_link = input("File link: ")
	parsed_link = urlparse(download_link).path[1:]
	parts = parsed_link.split('/')
	captcha_required, second_captcha = download_file(parts[1])	
	while captcha_required:
		captcha_request(second_captcha)
		temp_captcha = second_captcha
		input("Press Enter after you finished the captcha...")
		captcha_required, second_captcha = download_file(parts[1], temp_captcha)
