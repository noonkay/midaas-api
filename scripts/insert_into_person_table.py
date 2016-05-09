import json
import psycopg2
import os
import boto
from boto.s3.key import Key
from boto.s3.connection import S3Connection

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname('midaas-api'),'..'))

rds_config_path = os.path.join(BASE_DIR, 'rds-config.json')
s3_config_path = os.path.join(BASE_DIR, 's3-config.json')

# with open("./local-config.json") as rdsConfigFile:
with open(rds_config_path) as rdsConfigFile:
    config = json.load(rdsConfigFile)

conn = psycopg2.connect(host=config["host"], password=config["password"], user=config["user"], database=config["database"], port=config["port"])

cursor = conn.cursor()

with open(s3_config_path) as s3ConfigFile:
    credential = json.load(s3ConfigFile)

s3conn = S3Connection(credential["AWS_ACCESS_KEY_ID"], credential["AWS_SECRET_ACCESS_KEY"])
bucket = s3conn.get_bucket('midaas')
k = Key(bucket)
bucket_list = bucket.list()
for l in bucket_list:
    k.key = l.name
    temp_path = os.path.join(BASE_DIR, 'tmp', l.name)
    k.get_contents_to_filename(temp_path)
    f = open(temp_path)
    cursor.copy_expert("COPY PUMS_2014_Persons FROM STDIN WITH CSV HEADER NULL ''", file = f)
    f.close()
    try:
        conn.commit()
        print ("copied %s" % (temp_path))
    except psycopg2.Error as e:
        conn.rollback()
        print(e, 'rolledback')
