import fnmatch
import json
import multiprocessing
import ntpath
import os
import sys
import time
import mog.graph_io as GraphIO


import networkx as nx

import mog.filter_functions as ff

data_sets = {}

filter_function_names = {'agd': 'Average Geodesic Distance',
                         'ecc': 'Eccentricity',
                         'pr_0_85': 'PageRank (alpha=0.85)',
                         'fv': 'Fiedler Vector',
                         'fv_norm': 'Fiedler Vector Normalized',
                         'den_0_5': 'Density 0.5',
                         'ev_1': 'Eigen Function (2nd)',
                         'ev_2': 'Eigen Function (3rd)',
                         'ev_3': 'Eigen Function (4th)',
                         'ev_4': 'Eigen Function (5th)',
                         'ev_5': 'Eigen Function (6th)',
                         'ev_norm_1': 'Eigen Function Normalized (2nd)',
                         'ev_norm_2': 'Eigen Function Normalized (3rd)',
                         'ev_norm_3': 'Eigen Function Normalized (4th)',
                         'ev_norm_4': 'Eigen Function Normalized (5th)',
                         'ev_norm_5': 'Eigen Function Normalized (6th)'}



# Generate AGD
def generate_agd(out_path, graph, weight):
    if not os.path.exists(out_path):
        print("   >> Generating AGD")
        start = time.time()
        data = ff.average_geodesic_distance(graph, _weight=weight)
        GraphIO.write_json_data(out_path, {'name': 'agd', 'process_time':(time.time()-start), 'data':data} )


# Generate eccentricity
def generate_ecc(out_path, graph):
    if not os.path.exists(out_path):
        print("   >> Generating Eccentricity")
        start = time.time()
        data = ff.eccentricity(graph)
        GraphIO.write_json_data(out_path, {'name': 'eccentricity', 'process_time':(time.time()-start),'data':data} )


# Generate pagerank
def generate_pr(out_path, graph, weight, alpha):
    if not os.path.exists(out_path):
        print("   >> Generating Pagerank")
        start = time.time()
        data = ff.pagerank(graph, weight, alpha)
        GraphIO.write_json_data(out_path, {'name': 'pagerank', 'alpha': alpha, 'process_time':(time.time()-start),'data':data} )


# Generate fiedler vector
def generate_fv(out_path, graph, weight, normalized):
    try:
        if not os.path.exists(out_path):
            print("   >> Generating Fiedler Vector")
            start = time.time()
            data = ff.fiedler_vector(graph, _weight=weight, _normalized=normalized)
            GraphIO.write_json_data(out_path, {'name': 'fiedler', 'normalized': normalized, 'process_time': (time.time() - start), 'data': data})
    except nx.exception.NetworkXError:
        print(">>> FAILED (fiedler vector): processing error. maybe graph not connected?")


# Generate density
def generate_den(out_path, graph, weight, eps):
    if not os.path.exists(out_path):
        print("   >> Generating Density")
        start = time.time()
        data = ff.density(graph, weight, eps)
        GraphIO.write_json_data(out_path, {'name': 'density', 'eps': eps, 'process_time': (time.time() - start),
                                   'data': data})


# Generate eigen functions
def generate_eig(out_path, graph, weight, which_eig, normalized):
    try:
        compute = False
        for ev in which_eig:
            ev_path = out_path.format(str(ev))
            if graph.number_of_nodes() > ev and not os.path.exists(ev_path): compute = True

        if compute:
            print("   >> Generating Eigen Functions")
            start = time.time()
            eig = ff.eigen_function(graph, _weight=weight, _normalized=normalized)
            end = time.time()
            for ev in which_eig:
                if graph.number_of_nodes() > ev:
                    ev_path = out_path.format(str(ev))
                    GraphIO.write_json_data(ev_path, {'name': 'eigen', 'eigen': ev, 'normalized': normalized,
                                               'process_time': (end - start),
                                               'data': eig[ev][1]})
    except TypeError:
        print(">>> FAILED (eigen): type error")


def process_graph(in_filename):
    print("Found Graph: " + in_filename)
    basename,ext = os.path.splitext(ntpath.basename(in_filename).lower())

    if ext not in ['.json','.graph','.tsv']:
        return

    if os.path.exists('data/small/'+basename+'.json'): return 'data/small/'+basename+'.json'
    if os.path.exists('data/medium/'+basename+'.json'): return 'data/medium/' + basename + '.json'
    if os.path.exists('data/large/'+basename+'.json'): return 'data/large/' + basename + '.json'
    if os.path.exists('data/very_large/'+basename+'.json'): return 'data/very_large/' + basename + '.json'

    if ext == ".json": data, graph = GraphIO.read_json_graph(in_filename)
    elif ext == ".graph": data, graph = GraphIO.read_graph_file(in_filename)
    elif ext == ".tsv": data, graph = GraphIO.read_tsv_graph_file(in_filename)
    else: return None

    gcc = max(nx.connected_components(graph), key=len)
    graph = graph.subgraph(gcc)

    if graph.number_of_nodes() < 100: out_filename = 'data/small/'+basename+'.json'
    elif graph.number_of_nodes() < 1000: out_filename = 'data/medium/'+basename+'.json'
    elif graph.number_of_nodes() < 5000: out_filename = 'data/large/'+basename+'.json'
    else:
        out_filename = 'data/very_large/' + basename + '.json'

    print("   >> Converting to " + in_filename)

    GraphIO.write_json_graph(out_filename, graph)
    return out_filename


def process_datafile(in_filename, max_time_per_file=1):
    print("Processing Graph: " + in_filename)

    ff_file_list = ["/agd.json", "/ecc.json", "/pr_0_85.json", "/fv.json", "/fv_norm.json", "/den_0_5.json"]
    ff_file_list.extend(["/ev_{}.json".format(x) for x in range(1, 6)])
    ff_file_list.extend(["/ev_norm_{}.json".format(x) for x in range(1, 6)])

    need_processing = False
    for f in ff_file_list:
        need_processing = need_processing or not os.path.exists(f)

    if not need_processing: return

    data, graph = GraphIO.read_json_graph(in_filename)

    out_dir = os.path.splitext(in_filename)[0]
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    procs = [multiprocessing.Process(target=generate_agd, args=(out_dir + "/agd.json", graph, 'value')),
             multiprocessing.Process(target=generate_ecc, args=(out_dir + "/ecc.json", graph)),
             multiprocessing.Process(target=generate_pr, args=(out_dir + "/pr_0_85.json", graph, 'value', 0.85)),
             multiprocessing.Process(target=generate_fv, args=(out_dir + "/fv.json", graph, 'value', False)),
             multiprocessing.Process(target=generate_fv, args=(out_dir + "/fv_norm.json", graph, 'value', True)),
             multiprocessing.Process(target=generate_den, args=(out_dir + "/den_0_5.json", graph, 'value', 0.5)),
             multiprocessing.Process(target=generate_eig, args=(out_dir + "/ev_{}.json", graph, 'value', range(1, 6), False)),
             multiprocessing.Process(target=generate_eig, args=(out_dir + "/ev_norm_{}.json", graph, 'value', range(1, 6), True))]

    # process the functions in parallel for max_time_per_file
    end_time = time.time() + max_time_per_file
    for p in procs: p.start()
    for p in procs:
        p.join(max(1, int(end_time - time.time())))
        if p.is_alive():
            p.terminate()
            p.join()


if not os.path.exists("data/small"): os.mkdir("data/small")
if not os.path.exists("data/medium"): os.mkdir("data/medium")
if not os.path.exists("data/large"): os.mkdir("data/large")
if not os.path.exists("data/very_large"): os.mkdir("data/very_large")


def generate_data(max_time_per_file=1):
    data_gen = []
    for d0 in os.listdir("data/source"):
        if os.path.isdir("data/source/" + d0):
            for d1 in os.listdir("data/source/" + d0):
                try:
                    if fnmatch.fnmatch(d1.lower(), "*.json"):
                        data_gen.append( process_graph("data/source/" + d0 + "/" + d1) )
                    if fnmatch.fnmatch(d1.lower(), "*.graph"):
                        data_gen.append( process_graph("data/source/" + d0 + "/" + d1) )
                    if fnmatch.fnmatch(d1.lower(), "*.tsv"):
                        data_gen.append( process_graph("data/source/" + d0 + "/" + d1) )
                except:
                    print("data/source/" + d0 + "/" + d1 + " failed with " + str(sys.exc_info()[0]))

    for file in data_gen:
        if file is None: continue
        try:
            process_datafile(file, max_time_per_file)
        except json.decoder.JSONDecodeError:
            print(">>> FAILED: json parse " + file)
        except TypeError:
            print(">>> FAILED: type error " + file)
        except nx.exception.NetworkXError:
            print(">>> FAILED: graph not connected error " + file)
        except:
            print(file + " failed with " + str(sys.exc_info()[0]))


def scan_datasets():
    #for d0 in os.listdir("data/"):
    for d0 in ['small','medium','large','very_large']:
        if os.path.isdir("data/" + d0):
            data_sets[d0] = {}
            for d1 in os.listdir("data/" + d0):
                if fnmatch.fnmatch(d1.lower(), "*.json"):
                    ff_dir = os.path.splitext("data/" + d0 + '/' + d1)[0]
                    data_sets[d0][d1] = {}
                    for ff in filter_function_names.keys():
                        if os.path.exists(ff_dir + "/" + ff + ".json"):
                            data_sets[d0][d1][ff] = filter_function_names[ff]
                    if len(data_sets[d0][d1]) == 0:
                        del data_sets[d0][d1]


if __name__ == '__main__':
    if len(sys.argv) > 1:
        generate_data(int(sys.argv[1]))
    else:
        generate_data(1)
