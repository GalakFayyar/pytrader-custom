#!/usr/bin/env python
"""
    Intègres les données à destination de l'application pytrader-custom dans Elasticsearch

    Usage:
        init_data.py [--type_doc=<doc_type>] [--source_folder=<folder_path>] [--debug] 

    Example:
        python init_data.py --type_doc=crypto --source_folder=./data/

    Options:
        --help                              Affiche l'aide
        --type_doc=<doc_type>               Type de document à traiter
        --source_filefolder=<file_path>     Fichier contenant les données à importer ou à mettre à jour
"""
from elasticsearch import Elasticsearch, TransportError
from logger import logger, configure
from docopt import docopt
import json, time, glob

from swallow.inout.ESio import ESio
from swallow.inout.CSVio import CSVio
from swallow.inout.JsonFileio import JsonFileio
from swallow.Swallow import Swallow

def file_to_elasticsearch(p_docin, p_type, p_es_conn, p_es_index, p_arguments):
    doc = {
        'date_operation': p_docin[0]
    }
    for pair in p_docin[1:]:
        currency = pair.split(':')[0]
        value = pair.split(':')[1]
        doc[currency] = {
            'libelle': currency,
            'value': value
        }

    document = {
        '_type': p_type,
        '_source': doc,
        '_retry_on_conflict': 10
    }
    return [document]

def run_import(conf, type_doc = None, source_file = None):
    logger.debug("Running import...")

    configure(conf['log']['level_values'][conf['log']['level']],
              conf['log']['dir'], 
              conf['log']['filename'],
              conf['log']['max_filesize'], 
              conf['log']['max_files'])

    #
    #   Création du mapping
    # 

    try:
        es_mappings = json.load(open('data/es.mappings.json'))
    except Exception as e:
        pass

    # Connexion ES métier
    try:
        param = [{'host': conf['connectors']['elasticsearch']['host'],
                  'port': conf['connectors']['elasticsearch']['port']}]
        es = Elasticsearch(param)
        logger.info('Connected to ES Server: %s', json.dumps(param))
    except Exception as e:
        logger.error('Connection failed to ES Server : %s', json.dumps(param))
        logger.error(e)

    # Création de l'index ES metier cible, s'il n'existe pas déjà
    index = conf['connectors']['elasticsearch']['index']
    if not es.indices.exists(index):
        logger.debug("L'index %s n'existe pas : on le crée", index)
        body_create_settings = {
            "settings" : {
                "index" : {
                    "number_of_shards" : conf['connectors']['elasticsearch']['number_of_shards'],
                    "number_of_replicas" : conf['connectors']['elasticsearch']['number_of_replicas']
                },
                "analysis" : {
                    "analyzer": {
                        "lower_keyword": {
                            "type": "custom",
                            "tokenizer": "keyword",
                            "filter": "lowercase"
                        }
                    }
                }
            }
        }
        es.indices.create(index, body=body_create_settings)
        # On doit attendre 5 secondes afin de s'assurer que l'index est créé avant de poursuivre
        time.sleep(2)

        # Création des type mapping ES
        try:
            es_mappings = json.load(open('conf/es.mappings.json'))

            if es_mappings:
                for type_es, properties in es_mappings['crypto'].items():
                    logger.debug("Création du mapping pour le type de doc %s", type_es)
                    es.indices.put_mapping(index=index, doc_type=type_es, body=properties)

                time.sleep(2)
        except expression as identifier:
            logger.info("No mapping provided.")
            pass

    #
    #   Import des données initiales
    #

    # Objet swallow pour la transformation de données
    swal = Swallow()

    # On lit dans un fichier
    reader = CSVio()
    logger.info("Import data from file %s", source_file)
    swal.set_reader(reader, p_file=source_file, p_delimiter='|')

    # On écrit dans ElasticSearch
    writer = ESio(conf['connectors']['elasticsearch']['host'],
                  conf['connectors']['elasticsearch']['port'],
                  conf['connectors']['elasticsearch']['bulk_size'])
    swal.set_writer(writer, p_index=conf['connectors']['elasticsearch']['index'], p_timeout=30)

    # On transforme la donnée avec la fonction
    swal.set_process(file_to_elasticsearch, p_type=type_doc, p_es_conn=es, p_es_index=conf['connectors']['elasticsearch']['index'], p_arguments=arguments)

    logger.debug("Indexation sur %s du type de document %s", conf['connectors']['elasticsearch']['index'], type_doc)
    
    swal.run(1)

    logger.debug("Opération terminée pour le type de document %s ", type_doc)    

if __name__ == '__main__':
    conf = json.load(open('./conf.json'))

    # Command line args
    arguments = docopt(__doc__, version=conf['version'])

    # Tentative de récupération des paramètres en argument
    type_doc = arguments['--type_doc'] if '--type_doc' in arguments and arguments['--type_doc'] else "crypto"
    source_folder = arguments['--source_folder'] if '--source_folder' in arguments and arguments['--source_folder'] else './data/'

    files_ext = '*.txt'
    
    files = glob.glob(source_folder + files_ext)
    
    for file in files:
        try:
            run_import(conf, type_doc, file)
        except Exception as e:
            logger.error("Error importing file %s", file)
            logger.error(e)
