import json
import pymongo

def get_config_obj():
    f = open('./config.json')
    data = json.load(f)
    return data

def get_info_for_org(org):
    data = get_config_obj()
    if data['use_mongo']:
        myclient = pymongo.MongoClient(get_mongo_connection_string())
        mydb = myclient[get_mongo_db()]
        mycol = mydb["accounts"]
        myquery = { "gitorg": org }
        x = mycol.find_one(myquery)
        if x is not None:
            return x
    # found nothing or not using mongodb, try looking up the json file
    item = next((item for item in data["installs"] if item["gitorg"] == org), None)
    if item is not None:
        return item
    return None

def get_mongo_state():
    return get_config_obj()['use_mongo']

def get_mongo_connection_string():
    return get_config_obj()['mongodb_conn']

def get_mongo_db():
    return get_config_obj()['mongodb_db']

