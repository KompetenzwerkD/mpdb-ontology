import yaml
import requests
from rdflib import Graph, Namespace, RDF, DCTERMS, SKOS, URIRef, Literal
from omeka_s_utils.api import OmekaApi
from omeka_s_utils.item_set import ItemSet

CONFIG_FILE = "config.yml"
OUT_DIR = "thesauri"

if __name__ == "__main__":
    with open(CONFIG_FILE) as f:
        config = yaml.load(f, Loader=yaml.BaseLoader)

    api = OmekaApi(
            config["API_URL"], 
            config["IDENTITY"], 
            config["CREDENTIALS"], 
            verbose=True)
    
    item_sets = api.get_item_sets_by_resource_class_label("Collection")
    print(item_sets)
    for i in item_sets:      
        id_ = i["id"]
        scheme_label = i["label"]

        print(f"building <{scheme_label}.ttl>")

        item_set = ItemSet(id_)

        thesaurus = Graph()
        thesaurus.namespace_manager.bind("skos", SKOS)
        thesaurus.namespace_manager.bind("dcterms", DCTERMS)
        thesaurus.namespace_manager.bind("mpdb_items", Namespace(f"{config['API_URL']}/items/"))
        thesaurus.namespace_manager.bind("mpdb_item_sets", Namespace(f"{config['API_URL']}/item_sets/"))
        
        scheme = URIRef(id_)
        thesaurus.add( (scheme, RDF["type"], SKOS["ConceptScheme"]) )
        thesaurus.add( (scheme, DCTERMS["title"], Literal(scheme_label, lang="de")) )

        for item, p, o in item_set.g.triples((None, RDF["type"], SKOS["Concept"])):
            thesaurus.add( (item, RDF["type"], SKOS["Concept"]) )
            thesaurus.add( (item, SKOS["inScheme"], scheme) )
            for s, p, label in item_set.g.triples((item, DCTERMS["title"], None)):
                if label.language:
                    thesaurus.add( (item, SKOS["prefLabel"], label) )

        thesaurus.serialize(destination=f"{OUT_DIR}/{scheme_label}.ttl", format="turtle")
        