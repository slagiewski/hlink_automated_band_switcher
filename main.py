import speedtest
import json
import time
from datetime import datetime

from huawei_lte_api.Client import Client
from huawei_lte_api.AuthorizedConnection import AuthorizedConnection
from huawei_lte_api.Connection import Connection

### Router Access Credentials ###
ROUTER_IP = "192.168.1.1"
ROUTER_PASSWORD = ""
### Router Access Credentials ###

VALIDATION_SECOND_CHECK_DELAY_SECS = 15
CONFIG_CHANGES_SAVE_WAIT_SECS = 5

ONLY_4G_MODE = "03"
ONLY_3G_MODE = "02"

EU_LTE_BANDS_CODE = "20000800C5"
ALL_SUPPORTED_3G_BANDS_CODE = "3FFFFFFF"

NETWORK_CONFIGS = {
    "4G B3 band": {"network_mode": ONLY_4G_MODE, "network_band": ALL_SUPPORTED_3G_BANDS_CODE, "lte_band": "4"},
    "4G B7 band": {"network_mode": ONLY_4G_MODE, "network_band": ALL_SUPPORTED_3G_BANDS_CODE, "lte_band": "40"},
    "4G B20 band": {"network_mode": ONLY_4G_MODE, "network_band": ALL_SUPPORTED_3G_BANDS_CODE, "lte_band": "80000"},
    "4G B3+B7 band": {"network_mode": ONLY_4G_MODE, "network_band": ALL_SUPPORTED_3G_BANDS_CODE, "lte_band": "44"},
    "4G B3+B20 band": {"network_mode": ONLY_4G_MODE, "network_band": ALL_SUPPORTED_3G_BANDS_CODE, "lte_band": "80004"},
    "4G B7+B20 band": {"network_mode": ONLY_4G_MODE, "network_band": ALL_SUPPORTED_3G_BANDS_CODE, "lte_band": "80040"},
    "3G": {"network_mode": ONLY_3G_MODE, "network_band": ALL_SUPPORTED_3G_BANDS_CODE, "lte_band": EU_LTE_BANDS_CODE}
}

MIN_ACCEPTABLE_SPEED_MBITS = 1.5
MIN_ACCEPTED_PING_MS = 350


def __test_download_speed():
    tests_performed_count = 0
    while tests_performed_count < 2:
        time.sleep(10)
        try:
            speedtester = speedtest.Speedtest()
            speedtester.get_best_server()
            result_Mbits = round(speedtester.download() / 1000000, 2)
            return (result_Mbits, speedtester.results.ping)
        except:
            tests_performed_count += 1
    else:
        return (0.00, 9999)


def test_download_speed(test_id):
    print(f"Testing download speed ({test_id})...")
    (result_Mbits, ping) = __test_download_speed()
    print(
        f"Received download speed results ({test_id}): \n{result_Mbits}Mb/s \n{ping}ms")
    return (result_Mbits, ping)


def __download_speed_valid(download_speed_Mbit, ping):
    if (download_speed_Mbit >= MIN_ACCEPTABLE_SPEED_MBITS and ping <= MIN_ACCEPTED_PING_MS):
        return True
    else:
        return False


def download_speed_valid():
    (download_Mbits, ping) = test_download_speed("1/2")
    if __download_speed_valid(download_Mbits, ping):
        print(f"Waiting {VALIDATION_SECOND_CHECK_DELAY_SECS}s...")
        time.sleep(VALIDATION_SECOND_CHECK_DELAY_SECS)
        (download_Mbits, ping) = test_download_speed("2/2")
        if __download_speed_valid(download_Mbits, ping):
            print("Results are OK!")
            return (True, download_Mbits, ping)
    print("Results are bad!")
    return (False, download_Mbits, ping)


def change_router_config(config_name, network_band_config):
    print(f"Switching to [{config_name}] config...")
    network_mode = network_band_config['network_mode']
    network_band = network_band_config['network_band']
    lte_band = network_band_config['lte_band']
    connection = AuthorizedConnection(
        f'http://admin:{ROUTER_PASSWORD}@{ROUTER_IP}/')
    client = Client(connection)

    print(f"Connected to: {client.device.information()['DeviceName']} router.")
    router_response = client.net.set_net_mode(
        lte_band, network_band, network_mode)
    print(
        f"Router response to config change: {router_response}")

    print("Waiting for changes to be saved...")
    time.sleep(CONFIG_CHANGES_SAVE_WAIT_SECS)
    print("Config changes saved!")


def update_best_config_of_invalid(best_config_dict, config_name, download_speed_Mbits):
    if (best_config_dict['result_Mbits'] < download_speed_Mbits):
        best_config_dict['result_Mbits'] = download_speed_Mbits
        best_config_dict['name'] = config_name


def change_router_config_to_best_config_of_invalid(best_config_of_invalid):
    print(
        f"""None of the given configs is currently valid. 
            Setting the best one: 
            {best_config_of_invalid['name']} ({best_config_of_invalid['result_Mbits']}Mb/s)""")
    change_router_config(
        best_config_of_invalid['name'], NETWORK_CONFIGS[best_config_of_invalid['name']])

def print_log_entry_separator():
    print("\n\n\n")

def current_datetime():
    return f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]\n"

def main():
    print_log_entry_separator()
    print(current_datetime())
    (test_succeeded, result_Mbits, ping) = download_speed_valid()
    if test_succeeded:
        return

    best_config_of_invalid = {
        "name": None,
        "result_Mbits": 0
    }
    for config_name, config in NETWORK_CONFIGS.items():
        change_router_config(config_name, config)
        (test_succeeded, result_Mbits, ping) = download_speed_valid()
        if test_succeeded:
            return
        update_best_config_of_invalid(
            best_config_of_invalid, config_name, result_Mbits)
    else:
        change_router_config_to_best_config_of_invalid(best_config_of_invalid)

if __name__ == "__main__":
    main()
