import json
import os

from flask import Flask, request, send_from_directory
from flask import send_file

import mog.mapper as mapper
import data as data_mod
import mog.graph_io as GraphIO
import layout.initial_layout as layout
import networkx as nx

app = Flask(__name__)


def request_valid(dataset_req, datafile_req, filter_func_req):
    ds0 = request.args.get('dataset')
    ds1 = request.args.get('datafile')
    ff = request.args.get('filter_func')

    if dataset_req and ds0 not in data_mod.data_sets:
        return False

    if datafile_req and ds1 not in data_mod.data_sets[ds0]:
        return False

    if filter_func_req and ff not in data_mod.data_sets[ds0][ds1]:
        return False

    return True


def load_graph():
    ds0 = request.args.get('dataset')
    ds1 = request.args.get('datafile')
    return GraphIO.read_json_graph('data/' + ds0 + "/" + ds1)


def load_filter_function(dataset, datafile, filter_func, ranked=False):

    with open('data/' + dataset + "/" + os.path.splitext(datafile)[0] + "/" + filter_func + ".json") as json_file:
        ff_data = json.load(json_file)['data']

    if ranked:
        tmp = list(ff_data.keys())
        tmp.sort(key=(lambda e: ff_data[e]))
        for i in range(len(tmp)):
            ff_data[tmp[i]] = i / (len(tmp) - 1)
    else:
        val_max = ff_data[max(ff_data.keys(), key=(lambda k: ff_data[k]))]
        val_min = ff_data[min(ff_data.keys(), key=(lambda k: ff_data[k]))]
        if val_min == val_max: val_max += 1
        for (key, val) in ff_data.items():
            ff_data[key] = (float(val) - val_min) / (val_max - val_min)

    return ff_data


def get_cache_fn(cache_type, dataset, datafile, params):
    path = 'cache/' + dataset
    if not os.path.exists(path): os.mkdir(path)

    path += '/' + datafile
    if not os.path.exists(path): os.mkdir(path)

    path += '/' + cache_type

    pKeys = list(params.keys())
    pKeys.sort()
    for k in params.keys():
        path += "_" + str(params[k])
    return path + ".json"


def get_cache_filename():
    rank_filter = 'false' if request.args.get('rank_filter') is None else request.args.get('rank_filter')
    gcc_only = 'false' if request.args.get('gcc_only') is None else request.args.get('gcc_only')

    dir = 'cache/' + request.args.get('dataset')
    if not os.path.exists(dir): os.mkdir(dir)

    dir += '/' + request.args.get('datafile')
    if not os.path.exists(dir): os.mkdir(dir)

    return dir + '/mog_' + request.args.get('filter_func') + '_' + rank_filter + '_' \
           + request.args.get('coverN') + '_' + request.args.get('coverOverlap') + '_' \
           + request.args.get('component_method') + '_' + request.args.get('link_method') + '_' \
           + request.args.get('mapper_node_size_filter') + '_' + gcc_only + '.json'


def generate_mog(dataset, datafile, filter_func, cover_elem_count, cover_overlap, component_method, link_method, rank_filter):
    mog = mapper.MapperOnGraphs()

    mog_cf = get_cache_fn("mog", dataset, datafile, {
        'filter_func': filter_func,
        'coverN': cover_elem_count,
        'coverOverlap': cover_overlap,
        'component_method': component_method,
        'link_method': link_method,
        'rank_filter': 'false' if rank_filter is None else rank_filter
    })

    if os.path.exists(mog_cf):
        print("  >> " + datafile + " found in mog graph cache")
        mog.load_mog(mog_cf)
    else:
        # Load the graph and filter function
        graph_data, graph = GraphIO.read_json_graph('data/' + dataset + "/" + datafile)
        print(" >> Input Node Count: " + str(graph.number_of_nodes()))
        print(" >> Input Edge Count: " + str(graph.number_of_nodes()))

        values = load_filter_function(dataset,datafile,filter_func,rank_filter == 'true')

        # Construct the cover
        intervals = int(cover_elem_count)
        overlap = float(cover_overlap)
        cover = mapper.Cover(values, intervals, overlap)

        # Construct MOG
        mog.build_mog(graph, values, cover, component_method, link_method, verbose=graph.number_of_nodes() > 1000)

        if graph.number_of_nodes() > 5000:
            mog.strip_components_from_nodes()

        with open(mog_cf, 'w') as outfile:
            outfile.write(mog.to_json())

    return mog, mog_cf


@app.route('/')
def send_main():
    try:
        return send_file('static/index.html')
    except Exception as e:
        return str(e)


@app.route('/<path:path>')
def send_very_large(path):
    try:
        return send_from_directory('static', path)
    except Exception as e:
        return str(e)


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/datasets', methods=['GET', 'POST'])
def get_datasets():
    return json.dumps(data_mod.data_sets)


@app.route('/graph', methods=['GET', 'POST'])
def get_graph():
    # Check that the request is valid
    if not request_valid(True, True, False):
        return "{}"

    filename = get_cache_fn("graph_layout", request.args.get('dataset'), request.args.get('datafile'), {})
    if os.path.exists(filename):
        print("  >> " + request.args.get('datafile') + " found in graph layout cache")
    else:
        graph_data, graph = GraphIO.read_json_graph('data/' + request.args.get('dataset') + "/" + request.args.get('datafile'))
        layout.initialize_radial_layout(graph)

        with open(filename, 'w') as outfile:
            json.dump( nx.node_link_data(graph), outfile)

    return send_file(filename)


@app.route('/graph_layout', methods=['GET', 'POST'])
def cache_graph():
    filename = get_cache_fn("graph_layout", request.args.get('dataset'), request.args.get('datafile'), {})
    with open(filename, 'w') as outfile:
        json.dump(request.json, outfile)
    return "{}"


@app.route('/filter_function', methods=['GET', 'POST'])
def get_filter_function():
    # Check that the request is valid
    if not request_valid(True, True, True):
        return "{}"

    ds0 = request.args.get('dataset')
    ds1 = request.args.get('datafile')
    ff = request.args.get('filter_func')
    return json.dumps(load_filter_function(ds0,ds1,ff,request.args.get('rank_filter') == 'true'))


@app.route('/mog', methods=['GET', 'POST'])
def get_mog():
    # Check that the request is valid
    if not request_valid(True, True, True):
        return "{}"

    mog_layout_cf = get_cache_fn("mog_layout", request.args.get('dataset'), request.args.get('datafile'), {
        'filter_func': request.args.get('filter_func'),
        'coverN': request.args.get('coverN'),
        'coverOverlap': request.args.get('coverOverlap'),
        'component_method': request.args.get('component_method'),
        'link_method': request.args.get('link_method'),
        'mapper_node_size_filter': request.args.get('mapper_node_size_filter'),
        'rank_filter': 'false' if request.args.get('rank_filter') is None else request.args.get('rank_filter'),
        'gcc_only': 'false' if request.args.get('gcc_only') is None else request.args.get('gcc_only')
    })

    if os.path.exists(mog_layout_cf):
        print("  >> " + request.args.get('datafile') + " found in mog layout cache")
        return send_file(mog_layout_cf)

    mog, mog_cf = generate_mog( request.args.get('dataset'), request.args.get('datafile'), request.args.get('filter_func'),
        request.args.get('coverN'), request.args.get('coverOverlap'), request.args.get('component_method'),
         request.args.get('link_method'), request.args.get('rank_filter') )

    print(" >> MOG Node Count: " + str(mog.number_of_nodes()))
    print(" >> MOG Edge Count: " + str(mog.number_of_nodes()))
    print(" >> MOG Compute Time: " + str(mog.compute_time()) + " seconds")

    node_size_filter = int(request.args.get('mapper_node_size_filter'))
    if node_size_filter > 0:
        mog.filter_node_size(node_size_filter)

    gcc_only = request.args.get('gcc_only') == 'true'
    if gcc_only:
        mog.extract_greatest_connect_component()

    return mog.to_json()


@app.route('/mog_layout', methods=['GET', 'POST'])
def cache_mog():
    filename = get_cache_fn("mog_layout", request.args.get('dataset'), request.args.get('datafile'), {
        'filter_func': request.args.get('filter_func'),
        'coverN': request.args.get('coverN'),
        'coverOverlap': request.args.get('coverOverlap'),
        'component_method': request.args.get('component_method'),
        'link_method': request.args.get('link_method'),
        'mapper_node_size_filter': request.args.get('mapper_node_size_filter'),
        'rank_filter': 'false' if request.args.get('rank_filter') is None else request.args.get('rank_filter'),
        'gcc_only': 'false' if request.args.get('gcc_only') is None else request.args.get('gcc_only')
    })
    with open(filename, 'w') as outfile:
        json.dump(request.json, outfile)

    return "{}"


if __name__ == '__main__':
    if not os.path.exists("cache"):
        os.mkdir("cache")
    data_mod.scan_datasets()
    app.run(host='0.0.0.0', port=5000)
