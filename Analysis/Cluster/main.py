from argparse import ArgumentParser
from Analysis.Cluster.cluster import *

import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-r', '--reference_directory', type=int, required=False)
    parser.add_argument('-d', '--embedding_directory', type=str, required=False)
    parser.add_argument('-m', '--metric', choices=['cosine', 'euclidean'], required=False, default='euclidean')
    parser.add_argument('-c', '--cluster_selection_method', choices=["eom", "leaf"], required=False, default="eom")
    parser.add_argument('-s', '--min_cluster_size', type=int, required=False)

    return parser

def main():
    args = create_parser().parse_args()

    reference_dir = args.reference_directory
    if not reference_dir:
        reference_dir = "./Analysis/Cluster/reference_1.json"
    embedding_dir = args.embedding_directory
    if not embedding_dir:
        embedding_dir = "./Data/News/Embeddings"

    metric = args.metric
    cluster_selection_method = args.cluster_selection_method
    min_cluster_size = args.min_cluster_size

    run_HDBSCAN(
        embedding_path=embedding_dir,
        reference_path=reference_dir,
        metric=metric,
        cluster_selection_method=cluster_selection_method,
        min_cluster_size=min_cluster_size
    )

if __name__ == "__main__":
    main()