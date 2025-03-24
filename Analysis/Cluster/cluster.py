import numpy as np
from datetime import datetime, timedelta

import hdbscan
import json
import os


# Depreciated
def get_reference(ref_N: int, file_dir: str):
    with open(f"{file_dir}/reference_{ref_N}.json") as f:
        reference = json.load(f)

    # tmp = None
    # ref_dict = {}
    # for row in reference:
    #     key = list(row.keys())[0]
    #     file_value = row[key][-1]

    #     if tmp is not None and file_value != tmp:
    #         date_obj = datetime.strptime(key, "%Y%m%d") - timedelta(days=1)
    #         # ref_dict[date_obj] = tmp
    #         ref_dict[date_obj.strftime("%Y%m%d")] = tmp

    #     tmp = file_value
    date_list = [list(row.keys())[0] for row in reference]

    return date_list

def HDBSCAN(
        embeddings,
        metric: str = 'cosine',
        cluster_selection_method: str = "eom",
        min_cluster_size = None
    ):
    if not min_cluster_size:
        min_cluster_size = embeddings.shape[0] // 10
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric=metric,
        cluster_selection_method=cluster_selection_method
    )

    clusterer.fit(embeddings)
    labels = clusterer.labels_

    return labels

class HDBSCAN_cluster:
    def __init__(
            self,
            embedding_path: str,
            reference_path: str
        ):
        with open(reference_path, mode="r") as f:
            self.reference = json.load(f)
        self.embedding_path = embedding_path

    def get_date_list(self):
        date_list = [list(row.keys())[0] for row in self.reference]
        self.date_list = date_list
    
    def get_embeddingfile(self):
        self.embeddinglist = []
        file_list = [os.path.join(self.embedding_path, file) for file in os.listdir(self.embedding_path) if file.endswith(".json")]
        for file in file_list:
            with open(file, mode = "r") as f:
                jsonfile = json.load(f)
            self.embeddinglist.extend(jsonfile)

    def process_HDBSCAN(
            self,
            date: str,
            embedding_arr:list,
            ID_arr:list,
            link_arr:list,
            metric: str = 'cosine',
            cluster_selection_method: str = "eom",
            min_cluster_size = None
        ):
        labels = HDBSCAN(
            embedding_arr,
            metric = metric,
            cluster_selection_method=cluster_selection_method,
            min_cluster_size=min_cluster_size
        )
        Info_dict = {
            "Date": date,
            "Center_Link": []
        }
        for index, label in enumerate(labels):
            if label != -1:
                if f"Cluster_{label}" not in Info_dict.keys():
                    Info_dict[f"Cluster_{label}"] = [ID_arr[index]]
                else:
                    Info_dict[f"Cluster_{label}"].append(ID_arr[index])
            else:
                if "Noise" not in Info_dict.keys():
                    Info_dict["Noise"] = [ID_arr[index]]
                else:
                    Info_dict["Noise"].append(ID_arr[index])

        unique_label = sorted(list(set(labels)))
        if -1 in unique_label:
            u_label = unique_label[1:]
        else:
            u_label = unique_label

        for entity in u_label:
            ll = []
            link_list = []
            for index, label in enumerate(labels):
                if entity == label:
                    ll.append(embedding_arr[index])
                    link_list.append(link_arr[index])
            
            mean_vector = np.mean(np.array(ll), axis = 0)
            dist = np.linalg.norm(np.array(ll) - mean_vector, axis = 1)

            Info_dict["Center_Link"].append(link_list[np.argsort(dist)[0]])

        return Info_dict

    def process_by_date(
            self,
            metric: str = 'cosine',
            cluster_selection_method: str = "eom",
            min_cluster_size = None
        ):
        INFO_list = []
        for index, date in enumerate(self.date_list):
            IDs = self.reference[index]["IDs"]
            embedding_arr = []
            ID_arr = []
            link_arr = []
            for entity in self.embeddinglist:
                if entity["ID"] in IDs:
                    embedding_arr.append(entity["Embedding"])
                    link_arr.append(entity["Link"])
                    ID_arr.append(entity["ID"])

            embedding_arr = np.array(embedding_arr)
            link_arr = np.array(link_arr)
            ID_arr = np.array(ID_arr)

            Info_dict = self.process_HDBSCAN(
                date=date,
                embedding_arr=embedding_arr,
                ID_arr=ID_arr,
                link_arr=link_arr,
                metric=metric,
                cluster_selection_method=cluster_selection_method,
                min_cluster_size=min_cluster_size
            )
            INFO_list.append(Info_dict)

        return INFO_list


def run_HDBSCAN(
        embedding_path: str,
        reference_path: str,
        metric: str = "cosine",
        cluster_selection_method: str = "eom",
        min_cluster_size: int = None
    ):
    timeseries_clusterer=HDBSCAN_cluster(
        embedding_path=embedding_path,
        reference_path=reference_path
    )
    timeseries_clusterer.get_date_list()
    timeseries_clusterer.get_embeddingfile()

    INFO_list = timeseries_clusterer.process_by_date(
        metric=metric,
        cluster_selection_method=cluster_selection_method,
        min_cluster_size=min_cluster_size
    )

    return INFO_list