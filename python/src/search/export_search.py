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

        # if index exists, delete it
        self._es.indices.delete(index='people', ignore=[400, 404])

        # index settings
        mapping = {
            "settings": {
                "analysis": {
                    "filter": {
                        "prefixes": {
                            "type": "edge_ngram",
                            "min_gram": 1,
                            "max_gram": 25
                        }
                    },
                    "analyzer": {
                        "my_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "prefixes"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "my_analyzer",
                        "search_analyzer": "standard"
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

        query_body={'query':{'match':{'name': n1}}}

        res = self._es.search(index=self.index_name, body=query_body)

        # To get max score
        #max_score = float(res['hits']['max_score'])

        data = [doc for doc in res['hits']['hits']]

        if data is None or len(data) == 0:
            print("There is no person with this name. Try again.")
            return False, None

        # Check if is exact match
        best_match = data[0]['_source']['name']

        if best_match == n1:
            return True, best_match, data[0]['_source']['birthdate'], data[0]['_source']['deathdate']

        print("These are the best results. Please specify your query according to this list.")

        num_of_print_recs = 0
        for doc in data:

            if num_of_print_recs >= 5:
                break
            num_of_print_recs += 1

            # Just to show how to compute score in %
            #score = float(doc['_score']) / max_score * 100

            print("%s" % (doc['_source']['name']))

        return False, None
