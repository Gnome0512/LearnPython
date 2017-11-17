#!/usr/bin/env python

import time
import datetime
import re
import requests
import pymysql
import signal
import sys,os
import logging
from multiprocessing import Process

LOGIN_LOG = '/var/log/secure'
#LOGIN_LOG = '/home/python/script/LoginAlert/test'
REGEX_FAILLOGIN = re.compile(r'[A-Z][a-z]{2}\s+\d{1,2}\s+\d\d:\d\d:\d\d\s+.*\s+sshd\[\d+\]:\s+Failed\s+\w+\s+for\s+.*\s+from\s+\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s+port\s+\d{1,5}.*')
REGEX_SUCCESSLOGIN = re.compile(r'[A-Z][a-z]{2}\s+\d{1,2}\s+\d\d:\d\d:\d\d\s+.*\s+sshd\[\d+\]:\s+Accepted\s+\w+\s+for\s+.+\s+from\s+\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s+port\s+\d{1,5}.*')
STR_FINDIP = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
IP_INFO_URL = 'http://freegeoip.net/json/'

DB_HOST = 'localhost'
DB_USER = 'test'
DB_PASSWD = 'aaa111'
DB_NAME = 'test'
TABLE_NAME = 'mail_alarm'



logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s %(filename)s[%(lineno)d] %(levelname)s:%(message)s',
					datefmt='%Y-%m-%d %H:%M:%S',
					filename='alert.log')


def follow(log):
	log.seek(0,2)
	while True:
		line = log.readline()
		if not REGEX_FAILLOGIN.match(line) and not REGEX_SUCCESSLOGIN.match(line):
			time.sleep(0.1)
			continue
		logging.debug(line)
		yield line

def ip_parse(line):
	ip=re.findall(STR_FINDIP,line)
	if len(ip) == 1:
		return requests.get(IP_INFO_URL+ip[0]).json(),ip[0]

def monitor_log():
	login_log = open(LOGIN_LOG,'r')
	lines = follow(login_log)
	for line in lines:
		ip_info=ip_parse(line)[0]
		ip_address = ip_parse(line)[1]
		conuntry = ip_info['country_name']
		region = ip_info['region_name']
		city = ip_info['city']
		longitude = str(ip_info['longitude'])
		latitude = str(ip_info['latitude'])
		time_now = datetime.datetime.now()
		str_time_now = time_now.strftime('%Y-%m-%d %H:%M:%S')
		time_delay = time_now + datetime.timedelta(minutes=+2)
		str_time_delay = time_delay.strftime('%Y-%m-%d %H:%M:%S')

		if REGEX_FAILLOGIN.match(line):
			mail_context = '阿里云主机正在被尝试非法登录:IP地址:%s 国家:%s,地区:%s,城市:%s 经度:%s,纬度:%s' % (ip_address,conuntry,region,city,longitude,latitude)
			sql_insert1 = 'INSERT INTO `mail_alarm` VALUES (null,0,"%s","%s","%s");' % (mail_context,str_time_delay,str_time_now)
			sql_insert2 = 'INSERT INTO `fail_login_records` VALUES ("%s","%s","%s","%s","%s",%s,%s);' % (str_time_now,ip_address,conuntry,region,city,longitude,latitude)
		else:
			mail_context = '阿里云主机已登录:IP地址:%s 国家:%s,地区:%s,城市:%s 经度:%s,纬度:%s' % (ip_address,conuntry,region,city,longitude,latitude)
			sql_insert1 = 'INSERT INTO `mail_alarm` VALUES (null,0,"%s","%s","%s");' % (mail_context,str_time_delay,str_time_now)
			sql_insert2 = None

		conn = pymysql.connect(DB_HOST,DB_USER,DB_PASSWD,DB_NAME,charset='utf8')
		logging.debug('Mysql connection:%s' % (conn,))
		cur = conn.cursor()
		try:
			for sql in (sql_insert1,sql_insert2): 
				if sql:
					cur.execute(sql) 
			conn.commit()
		finally:
			cur.close()
			conn.close()
			logging.debug('Mysql Connection is close:%s' % (conn._closed,))


if __name__ == '__main__':
	#run as a daemon
	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError as e:
		print(e)
	os.chdir('/')
	os.setsid()
	os.umask(0)
	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError as e:
		print(e)

	#double process
	monitor_process = Process(target=monitor_log)
	monitor_process.start()

	last_change_date='19700101'
	while True:
		date=datetime.datetime.now().strftime('%Y%m%d')
		log_name=LOGIN_LOG+'-'+date
		#if log_name exist and it's the frist time main process find log_name,then restart the monitor subprocess.
		if os.path.isfile(log_name) and last_change_date != date:
			logging.info('Exist %s,restart monitor now...' % (log_name,))
			monitor_process.terminate()
			time.sleep(1)
			monitor_process = Process(target=monitor_log)
			monitor_process.start()
			last_change_date = date
			logging.info('Monitor restart over.')
		time.sleep(10)
