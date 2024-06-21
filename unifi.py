#!/usr/bin/env python3
# https://ubntwiki.com/products/software/unifi-controller/api
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import sys
import argparse
import os

# Получаем аргументы командной строки
def createParser ():
    parser = argparse.ArgumentParser()
    # parser.add_argument ('-n', '--name', default='мир')
    parser.add_argument ('-item', default = '')
    parser.add_argument ('-mac', default = '')
    parser.add_argument ('-site', default = '')
    parser.add_argument ('-server', default = '')
    parser.add_argument ('-port', default = '')
    parser.add_argument ('-username', default = '')
    parser.add_argument ('-password', default = '')
    parser.add_argument ('-zabbix', default = '')
    return parser

if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])

if (namespace.server=='' or namespace.port=='' or namespace.username=='' or namespace.password==''):
    sys.exit('Missed server credentials')

# Переменные, которые понадобятся в дальнейшем
# Префикс для имени обнаруженных устройств
device_prefix = 'UniFi_'
# Путь до zabbix_sender
sender_path = '/usr/bin/zabbix_sender'
# Типы устройств
device_types = {
    'uap':'UniFi Access Point',
    'usw':'UniFi Switch',
    'ugw':'UniFi Gateway',
    'uck':'UniFi Cloud Key',
    'udm':'UniFi Dream Machine',
    'uph':'UniFi Phone',
    'uas':'UniFi Application Server',
    'ubb':'UniFi Building-to-Building Bridge',
    'uxg':'UniFi Next-Generation Gateway'
}
# Заготовка под блок подсчета клиентов на точках доступа
client_count = {}

# формируем данные для работы
base_url = 'https://' + namespace.server + ':' + namespace.port + '/api/'
headers = {"Accept": "application/json","Content-Type": "application/json"}

# Аутентифицируемся на сервере и проверяем пустили нас туда или нет
s = requests.Session()
r = s.post(base_url+'login', headers = headers,  json = {'username': namespace.username, 'password': namespace.password} , verify = False, timeout = 2)
# Если в результате попытки входа, мы не получили код 200 (ОК), закрываем скрипт
if (r.status_code != 200):
    sys.exit ('Error - invalid server response code. Check Crdentials!')

# Если сайт не указан, значит нада Discover
if (namespace.site == ''):
    # Возвращаем список устройств с разбивкой по сайтам
    printout = '['
    # Список сайтов
    response = s.get(base_url+'self/sites', headers = headers, verify = False, timeout = 2).json()
    for site in response['data']:
        # добываем список устройств, сайт - только по имени name!!
        # Если Ip-адрес не нужен, можно запрашивать ветку /stat/device-basic вместо /stat/device
        site_desc=site['desc'].replace('"','\\\"')
        devices = s.get(base_url+'s/'+site['name']+'/stat/device', headers = headers, verify = False, timeout = 2).json()
        for device in devices['data']:
            if ('name' in device):
                devname = device['name']
            else:
                devname = device['mac']
            device_id = device['mac'].replace(':','')
            printout = printout + '{"{#DEVICEID}":"'+device_id+'", "{#DEVICENAME}":"'+devname+'", "{#DEVICEIP}":"'+device['ip']+'", "{#DEVICEMAC}":"'+device['mac']+'", "{#SITENAME}":"'+site['name']+'", "{#SITEDESC}":"'+site_desc+'"},'
    # Удаляем лишнюю запятую
    printout = printout[:-1]
    printout = printout + ']'
    print (json.dumps(json.loads(printout), sort_keys=True, indent=2))
else:
    if (namespace.zabbix == ''):
        print ('Missed Zabbix IP')
    else:
        devices = s.get(base_url+'s/'+namespace.site+'/stat/device', headers = headers, verify = False, timeout = 2).json()
        # Сразу возвращаем количество устройств на сайте
        print (len(devices['data']))
        # Ползем по списку и выколупываем полезные данные
        for device in devices['data']:
            # Наполняем список оборудования на сайте
            client_count[device['mac']] = 0
            # Готовим корректный ID хоста для Zabbix
            device_id = device_prefix + device['mac'].replace(':','')
            # Отправлям всю эту помойку в Zabbix
            os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[state] -o ' + str(device['state']), buffering=-1)
            os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[model] -o ' + str(device['model']), buffering=-1)
            os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[serial] -o ' + str(device['serial']), buffering=-1)
            os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[model_in_eol] -o ' + str(device['model_in_eol']), buffering=-1)
            os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[adopted] -o ' + str(device['adopted']), buffering=-1)
            os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[devicetype] -o "' + str(device_types[device['type']]) + '"', buffering=-1)
# Тот самый блок Satisfaction
#            if ('satisfaction' in device):
#                os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[satisfaction] -o ' + str(device['satisfaction']), buffering=-1)
            if ('last_seen' in device):
                os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[last_seen] -o ' + str(device['last_seen']), buffering=-1)
            # Если вдруг есть обновление прошивки, то не просто говорим да/нет, а еще и номер доступной прошивки возвращаем
            if ('upgradable' in device):
                if (device['upgradable']):
                    upgradable = 'to ver. ' +  device['upgrade_to_firmware']
                else:
                    upgradable = 'No'
                os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[upgradable] -o "' + str(upgradable) + '"', buffering=-1)
            if ('uptime' in device):
                os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[uptime] -o ' + str(device['uptime']), buffering=-1)
        # Начинаем подсчет клиентов
        clients = s.get(base_url+'s/'+namespace.site+'/stat/sta', headers = headers, verify = False, timeout = 2).json()
        for client in clients['data']:
            if ('ap_mac' in client):
                client_count[client['ap_mac']] +=  1
        # Ну и отсылаем данные в Zabbix
        for device in client_count.keys():
            device_id = device_prefix + device.replace(':','')
            os.popen(sender_path + ' -z ' + namespace.zabbix + ' -s ' + device_id + ' -k unifi.data[usercount] -o ' + str(client_count[device]), buffering=-1)

# logout
s.post(base_url+'logout', headers = headers, verify = False, timeout = 2)

