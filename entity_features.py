from rdflib import Graph, RDF, Literal, RDFS, plugin, OWL, XSD, SKOS, PROV
plugin.register('json-ld', 'Serializer', 'rdfextras.serializers.jsonld', 'JsonLDSerializer')
import csv
import pandas as pd
from collections import Counter
from nltk.tag import StanfordNERTagger
import spacy
import json
import re
import validators
import numpy as np


csv_links = "results/yago-links.csv"
csv_node_labels = "results/yago-node-labels.csv"
csv_nodes = "results/yago-nodes.csv"
entity_file = "results/entities_nodes.csv"
data_type_json = "results/data-type-validation.json"
csv_with_features = "results/features_selected_yago_nodes.csv"

def entgene():
    print("inside entity_recognition")
    web_sm = spacy.load(r'assets/en_core_web_sm-3.0.0/en_core_web_sm/en_core_web_sm-3.0.0')
    st = StanfordNERTagger('assets/stanford-ner-4.2.0/classifiers/english.all.3class.distsim.crf.ser.gz',
                           'assets/stanford-ner-4.2.0/stanford-ner-4.2.0.jar', encoding='utf-8')
    df_node_labels = pd.read_csv(csv_node_labels)
    dict_entity_type = {}
    entities = set(list(df_node_labels['subject']) + list(df_node_labels['object']))
    total_entities = len(entities)
    print("total_entities: " ,total_entities)
    count=0
    with open(entity_file, "a") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["entity", "entity_type"])
        for entity in entities:
            try:
                count = count + 1
                print("entity number: ", count)
                print("more to go number: ", total_entities-count)
                entity_types = []
                entity_split = entity.split("/")[-1]
                underscore_removed = entity_split.replace("_", " ")
                wordnet_removed = underscore_removed.replace('wordnet', "")
                wikicat_removed = wordnet_removed.replace('wikicategory', "")
                entity_final = "".join(filter(lambda x: not x.isdigit(), wikicat_removed))
                entity_final = entity_final.strip()
                print(entity_final)
                spacy_ner = [(X.text, X.label_) for X in web_sm(entity_final).ents]
                if spacy_ner:
                    for item in spacy_ner:
                        entity_types.append(item[1])
                else:
                    stanford_ner = st.tag([entity_final])
                    for item in stanford_ner + spacy_ner:
                        entity_types.append(item[1])
                replacements = {"ORG": "ORGANIZATION", "GPE": "LOCATION", "LOC": "LOCATION"}
                replacer = replacements.get  # For faster gets.
                entity_types = [replacer(n, n) for n in entity_types]
                dict_entity_type[entity] = set(entity_types)
                writer.writerow([entity, set(entity_types)])
            except:
                dict_entity_type[entity] = "{O}"
                writer.writerow([entity, set(entity_types)])
    df_node_labels['SubjectEntityType'] = df_node_labels.set_index(['subject']).index.map(dict_entity_type.get)
    df_node_labels['ObjectEntityType'] = df_node_labels.set_index(['object']).index.map(dict_entity_type.get)
    df_node_labels.to_csv(csv_node_labels, index=False)
    validate_literal_data_type()

def validate_literal_data_type():
    print("inside validate_literal_data_type")
    df_node_labels = pd.read_csv(csv_node_labels)
    json_file = open(data_type_json,)
    data_type_dict = json.load(json_file)
    print(data_type_dict)
    validity_score = []
    for index, row in df_node_labels.iterrows():
        pred_extracted = row['predicate']
        if validators.url(pred_extracted):
            pred_extracted = row['predicate'].split("/")[-1]
        validity = "na"
        for key in data_type_dict.keys():
            if key in pred_extracted.lower():
                data_type = data_type_dict[key]
                try:
                    if data_type == "url":
                        validity = is_url(row['object'])
                        break
                    if data_type == "date":
                        validity = is_date(row['object'])
                        break
                    if data_type == 'integer':
                        validity = row['object'].isnumeric()
                        break
                    if data_type == 'time':
                        validity = re.match('\d{2}:\d{2}:\d{2}', row['object'])
                        break
                    if data_type == 'string':
                        validity = ((not row['object'].isnumeric()) and (not row['object'] == "") and (not validators.url(row['object'])\
                                                                                                       and (not is_date(row['object']))))
                        break
                except:
                    validity = 0
        validity_score.append(validity)
    df_node_labels['ValidityOfLiteral'] = validity_score
    df_node_labels.to_csv(csv_node_labels, index=False)
    tot_literals()


def tot_literals():
#count total number of literal based triples an entity has
    print("inside tot_predicates")
    df_node_labels = pd.read_csv(csv_node_labels)
    total_groups = df_node_labels.groupby(['subject'])
    label_count = {}
    for group in total_groups.groups:
        try:
            label_count[group] = len(total_groups.get_group(group))
        except:
            continue
    data = {'node':list(label_count.keys()), 'CountLiterals': list(label_count.values()) }
    df_nodes = pd.DataFrame.from_dict(data)
    df_nodes.to_csv(csv_nodes, index=False)
    count_dif_literal_types()

def count_dif_literal_types():
#count different types of predicates an entity has got where the object is a literal
    print("inside count_dif_literal_types")
    df_node_labels = pd.read_csv(csv_node_labels)
    df_nodes = pd.read_csv(csv_nodes)
    total_groups = df_node_labels.groupby(['subject'])
    label_count = {}
    for group in total_groups.groups:
        fetched_group = total_groups.get_group(group)
        print(fetched_group)
        count_dif_literals = len(fetched_group['predicate'].unique())
        label_count[group] = count_dif_literals
    df_nodes['CountDifLiteralTypes'] = df_nodes.set_index(['node']).index.map(label_count.get)
    df_nodes.to_csv(csv_nodes, index=False)
    count_isa_triples()

def count_isa_triples():
#count different types of predicates an entity has got where the object is a literal
    print("inside count_isa_triples")
    df_node_labels = pd.read_csv(csv_node_labels)
    df_nodes = pd.read_csv(csv_nodes)
    total_groups = df_node_labels.groupby(['subject'])
    label_count = {}
    for group in total_groups.groups:
        fetched_group = total_groups.get_group(group)
        print(fetched_group)
        count_dif_literals = len(fetched_group[fetched_group['predicate']=='isa'])
        label_count[group] = count_dif_literals
    df_nodes['CountIsaPredicate'] = df_nodes.set_index(['node']).index.map(label_count.get)
    df_nodes.to_csv(csv_nodes, index=False)
    count_haslabel_triples()

def count_haslabel_triples():
#count different types of predicates an entity has got where the object is a literal
    print("inside count_haslabel_triples")
    df_node_labels = pd.read_csv(csv_node_labels)
    df_nodes = pd.read_csv(csv_nodes)
    total_groups = df_node_labels.groupby(['subject'])
    label_count = {}
    for group in total_groups.groups:
        fetched_group = total_groups.get_group(group)
        print(fetched_group)
        count_dif_literals = len(fetched_group[fetched_group['predicate']=='has_label'])
        label_count[group] = count_dif_literals
    df_nodes['CountHaslabelPredicate'] = df_nodes.set_index(['node']).index.map(label_count.get)
    df_nodes.to_csv(csv_nodes, index=False)
    count_subclassof_triples()


def count_subclassof_triples():
#count different types of predicates an entity has got where the object is a literal
    print("inside count_subclassof_triples")
    df_node_labels = pd.read_csv(csv_node_labels)
    df_nodes = pd.read_csv(csv_nodes)
    total_groups = df_node_labels.groupby(['subject'])
    label_count = {}
    for group in total_groups.groups:
        fetched_group = total_groups.get_group(group)
        print(fetched_group)
        count_dif_literals = len(fetched_group[fetched_group['predicate']=='subClassOf'])
        label_count[group] = count_dif_literals
    df_nodes['CountSubclassofPredicate'] = df_nodes.set_index(['node']).index.map(label_count.get)
    df_nodes.to_csv(csv_nodes, index=False)
    count_subpropertyof_triples()

def count_subpropertyof_triples():
#count different types of predicates an entity has got where the object is a literal
    print("inside count_subpropertyof_triples")
    df_node_labels = pd.read_csv(csv_node_labels)
    df_nodes = pd.read_csv(csv_nodes)
    total_groups = df_node_labels.groupby(['subject'])
    label_count = {}
    for group in total_groups.groups:
        fetched_group = total_groups.get_group(group)
        print(fetched_group)
        count_dif_literals = len(fetched_group[fetched_group['predicate']=='subPropertyOf'])
        label_count[group] = count_dif_literals
    df_nodes['CountSubpropofPredicate'] = df_nodes.set_index(['node']).index.map(label_count.get)
    df_nodes.to_csv(csv_nodes, index=False)
    count_high_sim_labels()

def count_high_sim_labels():
#count different types of predicates an entity has got where the object is a literal
    print("inside count_high_sim_labels")
    df_node_labels = pd.read_csv(csv_node_labels)
    df_nodes = pd.read_csv(csv_nodes)
    total_groups = df_node_labels.groupby(['subject'])
    label_count = {}
    for group in total_groups.groups:
        fetched_group = total_groups.get_group(group)
        count = 0
        for index, row in fetched_group.iterrows():
            if row['SimSubjectObject'] != 'na' and float(row['SimSubjectObject']) >=0.5:
                count+=1
        label_count[group] = count
    df_nodes['CountHighSimLabels'] = df_nodes.set_index(['node']).index.map(label_count.get)
    df_nodes.to_csv(csv_nodes, index=False)
    count_low_sim_labels()

def count_low_sim_labels():
#count different types of predicates an entity has got where the object is a literal
    print("inside count_low_sim_labels")
    df_node_labels = pd.read_csv(csv_node_labels)
    df_nodes = pd.read_csv(csv_nodes)
    total_groups = df_node_labels.groupby(['subject'])
    label_count = {}
    for group in total_groups.groups:
        fetched_group = total_groups.get_group(group)
        count = 0
        for index, row in fetched_group.iterrows():
            if row['SimSubjectObject'] != 'na' and float(row['SimSubjectObject']) <0.5:
                count+=1
        label_count[group] = count
    df_nodes['CountLowSimLabels'] = df_nodes.set_index(['node']).index.map(label_count.get)
    df_nodes.to_csv(csv_nodes, index=False)
    tot_outgoing_links()

def tot_outgoing_links():
    print("inside tot_incoming_links")
    df_node_labels = pd.read_csv(csv_node_labels)
    df_nodes = pd.read_csv(csv_nodes)
    df_links = pd.read_csv(csv_links)
    groups_in_node_labels = df_node_labels.groupby(['subject'])
    groups_in_links = df_links.groupby(['subject'])
    label_count = {}
    for group in df_nodes['node']:
        try:
            fetched_node_label_groups = len(groups_in_node_labels.get_group(group))
        except:
            fetched_node_label_groups = 0
        try:
            fetched_link_groups = len(groups_in_links.get_group(group))
        except:
            fetched_link_groups = 0
        label_count[group] = fetched_node_label_groups + fetched_link_groups
    df_nodes['OutDegree'] = df_nodes.set_index(['node']).index.map(label_count.get)
    df_nodes.to_csv(csv_nodes, index=False)
    tot_incoming_links()

def tot_incoming_links():
    print("inside tot_outgoing_links")
    df_nodes = pd.read_csv(csv_nodes)
    df_links = pd.read_csv(csv_links)
    groups_in_links = df_links.groupby(['object'])
    label_count = {}
    for group in df_nodes['node']:
        try:
            fetched_link_groups = len(groups_in_links.get_group(group))
        except:
            fetched_link_groups = 0
        label_count[group] = fetched_link_groups
    df_nodes['InDegree'] = df_nodes.set_index(['node']).index.map(label_count.get)
    df_nodes.to_csv(csv_nodes, index=False)
    find_com_rare_entity_type()

def find_com_rare_entity_type():
# counts the no. of times a predicate occurs within the entity's group
    print("inside find_com_rare_entity_type")
    df_node_links = pd.read_csv(csv_node_labels)
    df_nodes = pd.read_csv(csv_nodes)
    total_groups = df_node_links.groupby(['subject'])
    entity_count_node_max, entity_count_node_min = {}, {}
    for group in total_groups.groups:
        entity_count = {}
        sub_group = total_groups.get_group(group).groupby(['SubjectEntityType','ObjectEntityType'])
        for entity_group in sub_group.groups:
            entity_count[entity_group] = len(sub_group.get_group(entity_group))
        key_max = max(entity_count.keys(), key=(lambda k: entity_count[k]))
        key_min = min(entity_count.keys(), key=(lambda k: entity_count[k]))
        entity_count_node_max[group] = [key_max]
        entity_count_node_min[group] = [key_min]
    df_nodes['CommonPredType'] = df_nodes.set_index(['node']).index.map(entity_count_node_max.get)
    df_nodes['RarePredType'] = df_nodes.set_index(['node']).index.map(entity_count_node_min.get)
    df_nodes.to_csv(csv_nodes, index=False)
    count_invalid_literals()


def count_invalid_literals():
    print("inside count_invalid_literals")
    df_node_labels = pd.read_csv(csv_node_labels)
    df_nodes = pd.read_csv(csv_nodes)
    total_groups = df_node_labels.groupby(['subject'])
    label_count = {}
    for group in total_groups.groups:
        count=0
        for index, row in total_groups.get_group(group).iterrows():
            if row['ValidityOfLiteral'] == False:
                count+=1
        label_count[group] = count
    df_nodes['CountInvalidTriples'] = df_nodes.set_index(['node']).index.map(label_count.get)
    df_nodes.to_csv(csv_nodes, index=False)

########################################Special Functions###################################
def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.
    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    from dateutil.parser import parse
    try:
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

def is_url(url):
#check for valid URL
    if not validators.url(url):
        return False
    else:
        return True

def feature_reduction():
    df = pd.read_csv(csv_node_labels)
    df_fileterd = df.iloc[:,3:]
    for feature in df_fileterd.columns:
        if df_fileterd.dtypes[feature] != np.int64 or df_fileterd.dtypes[feature] != np.float64:
            df_fileterd[feature].replace(['1','0','True','False',True,False],[1,0,1,0,1,0], inplace=True)
            df_fileterd[feature] = df_fileterd[feature].astype(np.float)
    for col in df_fileterd.columns:
        count_unique = len(df[col].unique())
        if count_unique == 1:
            print(col)
            df_fileterd.drop(col, inplace=True, axis=1)
    columns = list(df_fileterd.columns)
    corr_feature_list = []
    for i in range(0, len(columns)-1):
        for j in range(i+1, len(columns)):
            print(columns[i],columns[j])
            correlation = df_fileterd[columns[i]].corr(df_fileterd[columns[j]])
            if correlation == 1:
                print(columns[i], columns[j])
                corr_feature_list.append(columns[i])
                corr_feature_list.append(columns[j])
    remove_corr_features(corr_feature_list, df_fileterd, df)

def remove_corr_features(corr_feature_list, df_fileterd, df):
    print("Correlated Features: ", corr_feature_list)
    features_to_remove  = [input("Enter the features to remove seperated by a comma without spaces: ")]
    if features_to_remove[0] == '':
        gen_binary_feature(df_fileterd, df)
    else:
        for feature in features_to_remove:
            df_fileterd.drop(feature, inplace=True, axis=1)
        gen_binary_feature(df_fileterd, df)

def gen_binary_feature(df_fileterd, df):
    columns = df_fileterd.columns
    for column in columns:
        new_col = []
        new_col_name = "Freq" + column
        for index, row in df_fileterd.iterrows():
            if row[column] > df_fileterd[column].median():
                new_col.append(1)
            else:
                new_col.append(0)
        df[new_col_name] = new_col
    df.to_csv(csv_with_features, index=False)


entgene()