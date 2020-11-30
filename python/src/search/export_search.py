from elasticsearch import Elasticsearch, helpers
import json
import re

class ExportSearch:

    def __init__(self, index_name='people'):
        # run elasticsearch
        self._es = None
        self._es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        self.is_es_prepared = False
        self.index_name = index_name

    def prepare_elasticsearch(self, ):
        if self._es.ping():
            self.create_index(self.index_name)
            self.is_es_prepared = True

        else:
            print('Elasticsearch could not connect!')

    def insert_data(self, parsed_file, bulk_size):
        # store data
        output = ""
        count = 0

        # creating dictionary
        with open(parsed_file, encoding="utf-8") as fh:
            for line in fh:
                l1,l2,l3 = self.handle_line_split(line.split("\n")[0])
                output += "{0} \"name\":\"{1}\",\"birthdate\":\"{2}\",\"deathdate\":\"{3}\" {4}\n".format("{",l1,l2,l3,"}")
                count += 1
                data = None

                if count == bulk_size:
                    count = 0

                    try:
                        data = [json.loads(l) for l in output.splitlines()]
                    except Exception as e:
                        print(e)

                        pass

                    if data:
                        output = ""
                        self.store_records(self.index_name, data)
                        print("Successfully bulked ", bulk_size, " records.")

    @staticmethod
    def handle_line_split(line):
        split = line.split(",")
        length = len(split)
        a, b, c = "","",""
        if length > 3:
            fullname_arr = split[0 : length - 2]
            fullname = '-'.join(map(str, fullname_arr))

            a = fullname
            b = split[-2]
            c = split[-1]

        else:
            if split[2] == "'alive'":
                split[2] = "alive"

            a = split[0]
            b = split[1]
            c = split[2]

        if "BC" in b:
            b = b.replace("(BC: False)", "")
            b = b.replace("(BC: True)", "BC")

        if "BC" in c:
            c = c.replace("(BC: False)", "")
            c = c.replace("(BC: True)", "BC")

        a = a.replace("\"", "\'")

        return a,b,c


    def create_index(self, index_name):
        created = False
        self._es.indices.delete(index='people', ignore=[400, 404])

        # index settings
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "dynamic": "strict",
                "properties": {
                    "name": {
                        "type": "text"  # formerly "string"
                    },
                    "birthdate": {
                        "type": "text"
                    },
                    "deathdate": {
                        "type": "text"
                    },
                }
            }
        }

        try:
            if not self._es.indices.exists(index_name):
                # Ignore "Index Already Exist"
                self._es.indices.create(index=index_name, ignore=400, body=mapping)
                print('Created Index')
            created = True

        except Exception as ex:
            print(str(ex))

        finally:
            return created

    def store_record(self, index_name, record):
        try:
            outcome = self._es.index(index=index_name, body=record)

        except Exception as ex:
            print('Error in indexing data')
            print(str(ex))

    def store_records(self, index_name, records):
        try:
            outcome = helpers.bulk(self._es, records, index=index_name)

        except Exception as ex:
            print('Error in indexing data')
            print(str(ex))

    def find(self, n1):

       # query_body = {
       #     "query": {
       #         "match": {
       #             "name": n1
       #         }
       #     }
       # }

        query_body={
           "query": {
                "match": {
                    "message": {
                        "query": n1
                    }
                }
            }
        }

        res = self._es.search(index=self.index_name, body=query_body)
        return res
