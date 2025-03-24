from argparse import ArgumentParser
from Analysis.Cluster.cluster import *

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-r', '--reference_index', type=int, required=True)
    parser.add_argument('-d', '--embedding_directory', type=str, required=True)
    parser.add_argument('-m', '--metric', choices=['cosine', 'euclidean'], required=True)
    parser.add_argument('e', '--')
    return parser
