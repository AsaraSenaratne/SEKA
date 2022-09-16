from rdflib import Graph, FOAF, URIRef, RDF, Literal, RDFS, plugin

plugin.register('json-ld', 'Serializer', 'rdfextras.serializers.jsonld', 'JsonLDSerializer')
import csv
from collections import Counter
import networkx as nx
import pandas as pd
import spacy
import numpy as np
import re
from itertools import chain
import time


csv_links = "results/yago-links.csv"
csv_node_labels = "results/yago-node-labels.csv"
csv_with_features = "results/features_selected_yago_links.csv"


# print("Populating the graph")
graph = Graph()
graph.parse('assets/yago-1.0.0-turtle.ttl', format='ttl')

def construct_df():
    #this step is only required if you wish to reduce memory consumption. Then the graph will be handled as a 2D structure.
    print("inside construct_df")
    with open(csv_links, 'w', encoding="utf-8") as yago_links:
        writer = csv.writer(yago_links)
        writer.writerow(["subject", "predicate", "object"])
        for statement in graph:
            if statement[1] == RDF.type or isinstance(statement[2], Literal):
                continue
            else:
                writer.writerow([statement[0], statement[1], statement[2]])

    with open(csv_node_labels, 'w', encoding="utf-8") as yago_nodes:
        writer = csv.writer(yago_nodes)
        writer.writerow(["subject", "predicate", "object"])
        for statement in graph:
            if statement[1] == RDF.type:
                writer.writerow([statement[0], "isa", statement[2]])
            elif statement[1] == RDFS.label and isinstance(statement[2], Literal) and RDFS.subClassOf:
                writer.writerow([statement[0], "has_label", statement[2]])
            elif statement[1] == RDFS.subClassOf and isinstance(statement[2], Literal):
                writer.writerow([statement[0], "subClassOf", statement[2]])
            elif statement[1] == RDFS.subPropertyOf and isinstance(statement[2], Literal):
                writer.writerow([statement[0], "subPropertyOf", statement[2]])
            elif isinstance(statement[2], Literal):
                writer.writerow([statement[0], statement[1], statement[2]])
    del globals()['graph']


def find_paths():
    df_links = pd.read_csv(csv_links)
    pathsList = []
    G = nx.MultiDiGraph()
    for index, rows in df_links.iterrows():
        G.add_edge(rows["subject"], rows["object"], predicate=rows["predicate"])
        print(rows["subject"], rows["object"])
    total_groups = df_links.groupby(['predicate'])
    group_count = {}
    #an example of identifying anomalies related to one specific target predicate
    group_one = total_groups.get_group("http://yago-knowledge.org/resource/bornIn")
    # you can uncomment the below line and comment the line above, if you wish to identify anomalies in the entire graph
    # group_one = df_links
    for group in total_groups.groups:
        group_count[group] = len(total_groups.get_group(group))
    group_one = df_links
    so_with_pred = {}
    for index, rows in group_one.iterrows():
        paths = list(nx.all_simple_edge_paths(G, rows["subject"], rows["object"], cutoff=2))
        print(paths)
        edge_list = []
        for path in paths:
            if len(path) == 1:
                edge = G.get_edge_data(path[0][0], path[0][1], key=path[0][2])
                edge_list.append(edge['predicate'])
            else:
                edge_concat = ""
                for section in path:
                    print(section)
                    edge = G.get_edge_data(section[0], section[1], key=section[2])
                    edge_concat = edge_concat + edge['predicate'] + "-"
                edge_concat = edge_concat[:-1]
                edge_list.append(edge_concat)
        so_with_pred[(rows["subject"], rows["object"])] = edge_list
    construct_features(so_with_pred, group_one, df_links)


def construct_features(so_with_pred, group_one, df_links):
    values_list = so_with_pred.values()
    features = []
    for values in values_list:
        for value in values:
            features.append(value)
    unique_features = set(features)
    for feature in unique_features:
        columnVal = []
        for index, rows in group_one.iterrows():
            if feature in so_with_pred[(rows["subject"], rows["object"])]:
                columnVal.append(1)
            else:
                columnVal.append(0)
        group_one[feature] = columnVal
    print(group_one)
    group_one.to_csv("only_circular_features.csv", index=False)
    half_path_features(group_one, df_links)


def half_path_features(group_one, df_links):
    list_sp = list(zip(list(df_links['subject']), list(df_links['predicate'])))
    list_op = list(zip(list(df_links['object']), list(df_links['predicate'])))

    row_val = []
    for index, row in group_one.iterrows():
        if list_sp.count((row['subject'], row['predicate'])) > 1:
            row_val.append(1)
        else:
            row_val.append(0)
    group_one['SPSP'] = row_val

    row_val = []
    for index, row in group_one.iterrows():
        if (row['subject'], row['predicate']) in list_op:
            row_val.append(1)
        else:
            row_val.append(0)
    group_one['SPOP'] = row_val

    row_val = []
    for index, row in group_one.iterrows():
        if list_op.count((row['object'], row['predicate'])) > 1:
            row_val.append(1)
        else:
            row_val.append(0)
    group_one['OPOP'] = row_val

    row_val = []
    for index, row in group_one.iterrows():
        if (row['object'], row['predicate']) in list_sp:
            row_val.append(1)
        else:
            row_val.append(0)
    group_one['OPSP'] = row_val
    group_one.to_csv("with_half_path_features.csv")
    single_node_features(group_one, df_links)


def single_node_features(group_one, df_links):
    list_s = list(df_links['subject'])
    list_o = list(df_links['object'])

    row_val = []
    for index, row in group_one.iterrows():
        if row['subject'] in list_o:
            row_val.append(1)
        else:
            row_val.append(0)
    group_one['SO'] = row_val

    row_val = []
    for index, row in group_one.iterrows():
        if row['object'] in list_s:
            row_val.append(1)
        else:
            row_val.append(0)
    group_one['OS'] = row_val
    group_one.to_csv("with_single_node_features.csv")



def entity_based_matrix_construction():
    start_time = time.time()
    group_one = pd.read_csv("yago_people_only.csv")
    entity_groups = group_one.groupby('predicate').agg(list) #group by predicate and aggregate other columns in to a list
    all_unique_predicates = list(entity_groups.index)  # this gives all unique predicates in the graph
    all_subjects = list(chain.from_iterable(entity_groups['subject'])) #merge nested lists
    all_objects = list(chain.from_iterable(entity_groups['object']))
    all_unique_nodes = list(set(all_subjects + all_objects)) #this gives all unique nodes in the graph

    dict_predicate_entities = {}
    for index, row in entity_groups.iterrows():
        dict_predicate_entities[index] = list(set(row['subject'] + row['object']))

    df_entities = pd.DataFrame(index=set(all_subjects))
    print("getting inside for loop")
    for predicate in dict_predicate_entities.keys():
        col_values = []
        for index,row in df_entities.iterrows():
            if index in dict_predicate_entities[predicate]:
                col_values.append(1)
            else:
                col_values.append(0)
        df_entities[predicate] = col_values
    df_entities.to_csv("entity_based_matrix.csv", index=False)
    execution_time = time.time() - start_time
    print('Total runtime taken for entity-based matrix construction: %.6f sec' % (execution_time))

def aggregate_predicate_features():
    start_time = time.time()
    print("inside aggregate predicate features")
    predicate_based_matrix = pd.read_csv("with_single_node_features.csv")
    entity_groups = predicate_based_matrix.groupby('subject').agg(list)
    df=pd.DataFrame()
    for index,row in entity_groups.iterrows():
        entity_row = {}
        entity_row["entity"] = index
        for col in entity_groups.columns[4:]:
            entity_row[col] = max(row[col])
        print(entity_row)
        df = df.append(entity_row, ignore_index=True, sort=False)
    df.to_csv("entity_and_predicate_aggregated_matrix.csv", index=False)
    execution_time = time.time() - start_time
    print('Total runtime taken to aggregate predicate features: %.6f sec' % (execution_time))

def merge_predicates_and_entities():
    start_time = time.time()
    print("this function generates table2")
    df1 = pd.read_csv("entity_based_matrix.csv")
    df2 = pd.read_csv("entity_and_predicate_aggregated_matrix.csv")
    df3 = pd.merge(df1, df2, left_index=True, right_index=True)
    df3.to_csv("final_table.csv", index=False)
    execution_time = time.time() - start_time
    print('Total runtime taken to the two table to form table2: %.6f sec' % (execution_time))

def feature_reduction():
    start_time = time.time()
    print("Inside feature reduction")
    df = pd.read_csv("final_table.csv")
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
    remove_corr_features(corr_feature_list, df_fileterd)
    execution_time = time.time() - start_time
    print('Total runtime taken to find correlation: %.6f sec' % (execution_time))

def remove_corr_features(corr_feature_list, df_fileterd):
    print("Correlated Features: ", corr_feature_list)
    features_to_remove  = [input("Enter the features to remove seperated by a comma without spaces: ")]
    if features_to_remove[0] == '':
        df_fileterd.to_csv("final_table.csv", index=False)
    else:
        for feature in features_to_remove:
            df_fileterd.drop(feature, inplace=True, axis=1)
            df_fileterd.to_csv("final_table.csv", index=False)


construct_df()
find_paths()
entity_based_matrix_construction()
aggregate_predicate_features()
merge_predicates_and_entities()
feature_reduction()
remove_corr_features()