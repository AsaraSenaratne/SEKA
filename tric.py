import pandas as pd
import random

def pre_process_csv():
    df=pd.read_csv("kinship.csv")
    percentage_of_anomalies = int(input("Enter the percentage of anomalies required: "))
    count_of_anomalies = int((len(df.index)*percentage_of_anomalies)/100)
    count_of_anomalies_from_each = int(count_of_anomalies/7)
    random_numbers = random.sample(range(len(df.index)), count_of_anomalies)
    print("Count of anomalies: ", count_of_anomalies)
    print("Number of rows in the dataframe: ", len(df.index))
    print("Random numbers: ",random_numbers)
    change_entity_s(df,random_numbers,count_of_anomalies_from_each)

def change_entity_s(df, random_numbers, count_of_anomalies_from_each):
    print("")
    print("Changing the subject entity..................")
    count = 1
    for random_position in random_numbers:
        print("")
        if count > count_of_anomalies_from_each:
            break
        else:
            record = df.loc[[random_position]]
            old_value = list(record['subject'])
            print(record)
            below_row = df.loc[[random_position+1]]
            print(below_row)
            new_value = list(below_row['subject'])
            record['subject'] = record['subject'].replace([old_value[0]], new_value[0])
            print("-------------------------")
            print(record)
            df.loc[random_position, 'subject'] = new_value[0]
            count=count+1
            random_numbers.remove(random_position)
    if len(random_numbers):
        change_entity_o(random_numbers, df, count_of_anomalies_from_each)

def change_entity_o(random_numbers, df, count_of_anomalies_from_each):
    print("")
    print("Changing the object entity..................")
    count = 1
    for random_position in random_numbers:
        print("")
        if count > count_of_anomalies_from_each:
            break
        else:
            record = df.loc[[random_position]]
            old_value = list(record['object'])
            print(record)
            below_row = df.loc[[random_position + 1]]
            print(below_row)
            new_value = list(below_row['object'])
            record['object'] = record['object'].replace([old_value[0]], new_value)
            print("-------------------------")
            print(record)
            df.loc[random_position, 'object'] = new_value
            count = count + 1
            random_numbers.remove(random_position)
    if len(random_numbers):
        change_entity_p(random_numbers, df, count_of_anomalies_from_each)

def change_entity_p(random_numbers, df, count_of_anomalies_from_each):
    print("")
    print("Changing the predicate entity..................")
    count = 1
    for random_position in random_numbers:
        print("")
        if count > count_of_anomalies_from_each:
            break
        else:
            record = df.loc[[random_position]]
            old_value = list(record['predicate'])
            print(record)
            below_row = df.loc[[random_position + 1]]
            print(below_row)
            new_value = list(below_row['predicate'])
            record['predicate'] = record['predicate'].replace([old_value[0]], new_value[0])
            print("-------------------------")
            print(record)
            df.loc[random_position, 'predicate'] = new_value[0]
            count = count + 1
            random_numbers.remove(random_position)
    df.to_csv("a.csv", index=False)
    if len(random_numbers):
        add_new_triplets(random_numbers, df)


def add_new_triplets(random_numbers, df):
    print(random_numbers)
    print("")
    print("Adding new triplets..................")
    for random_position in random_numbers:
        print("")
        record = df.loc[[random_position]]
        print(record)
        old_subject_value = list(record['subject'])
        old_object_value = list(record['object'])
        old_predicate_value = list(record['predicate'])

        i = 1
        while True:
            if (random_position + i) > len(df)-1:
                i = i - 2
                below_row = df.loc[[random_position - i]]
                print(below_row)
                new_predicate_value = list(below_row['predicate'])
                i=i+1
                if new_predicate_value != old_predicate_value:
                    break
            else:
                below_row = df.loc[[random_position + i]]
                print(below_row)
                new_predicate_value = list(below_row['predicate'])
                i = i + 1
                if new_predicate_value != old_predicate_value:
                    break
                else:
                    i=i+1

        i = 2
        while True:
            if (random_position + i) > len(df)-1:
                i = i - 2
                below_2row = df.loc[[random_position - i]]
                print(below_2row)
                new_subject_value = list(below_2row['subject'])
                if new_subject_value != old_subject_value:
                    break
            else:
                below_2row = df.loc[[random_position + i]]
                print(below_2row)
                new_subject_value = list(below_2row['subject'])
                if new_subject_value != old_subject_value:
                    break
                else:
                    i=i+1

        i = 3
        while True:
            if (random_position + i) > len(df)-1:
                i=i-2
                below_3row = df.loc[[random_position - i]]
                print(below_3row)
                new_object_value = list(below_3row['object'])
                if new_object_value != old_object_value:
                    break
            else:
                below_3row = df.loc[[random_position + i]]
                print(below_3row)
                new_object_value = list(below_3row['object'])
                if new_object_value != old_object_value:
                    break
                else:
                    i=i+1

        record['subject'] = record['subject'].replace([old_subject_value[0]], new_subject_value[0])
        record['predicate'] = record['predicate'].replace([old_predicate_value[0]], new_predicate_value[0])
        record['object'] = record['object'].replace([old_object_value[0]], new_object_value[0])
        print("-------------------------")
        print(record)


        df.loc[random_position, 'subject'] = new_subject_value[0]
        df.loc[random_position, 'predicate'] = new_predicate_value[0]
        df.loc[random_position, 'object'] = new_object_value[0]


pre_process_csv()
