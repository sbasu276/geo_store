from itertools import product
from utils import combinations, generate_placement_params
from constants.opt_consts import FUNC_HEURISTIC_MAP

def min_latency_abd(datacenters, group, params):
    """ Latency based greedy heuristic
    """
    dc_ids = [int(dc.id) for dc in datacenters]
    mincost = 999999
    min_get_cost = 0
    min_put_cost = 0
    read_lat = 0
    write_lat = 0
    selected_placement = None
    m_g = 0
    storage_cost, vm_cost = 0, 0
    for m, q1, q2 in params:
        # May pre-compute this. (though itertool is optimized)
        # Get possible combination of DCs (of size m) from the set of DCs
        possible_dcs = combinations(dc_ids, m)
        for dcs in possible_dcs:
            latency = 0
            _get_cost = 0
            _put_cost = 0
            combination = []
            for datacenter in datacenters:
                latency_list = [(d,datacenter.latencies[d]) for d in dcs]
                latency_list.sort(key=lambda x: x[1])
                # Get possible combination of DCs (of size q1 and q2) from the 
                # m-sized set of DCs.
                possible_quorum_dcs = []
                _iq1 = [l[0] for l in latency_list[:q1]]
                _iq2 = [l[0] for l in latency_list[:q2]]
                # Check if the selection meets latency constraints
                i = int(datacenter.id)
                latency += group.client_dist[i]*\
                            (max([datacenter.latencies[j] for j in _iq1])+\
                                max(datacenter.latencies[k] for k in _iq2))

                _get_cost += group.client_dist[i] * \
                                (sum([datacenters[i].network_cost for j in _iq1]) + \
                                    sum([datacenters[k].network_cost for k in _iq2]))
                _put_cost += group.client_dist[i] * \
                                (group.metadata_size*sum([datacenters[i].network_cost for j in _iq1]) + \
                                    group.object_size*sum([datacenters[k].network_cost for k in _iq2]))
                combination.append((latency, dcs, _iq1, _iq2))
            if latency < group.slo_read and latency < group.slo_write:
                get_cost = group.read_ratio*group.arrival_rate*group.object_size*_get_cost
                put_cost = group.read_ratio*group.arrival_rate*_put_cost
                _storage_cost = group.num_objects*\
                                sum([datacenters[i].details["storage_cost"] for i in dcs])*\
                                    group.object_size
                _vm_cost = sum([datacenters[i].details["price"] for i in dcs])
                if (get_cost+put_cost+_storage_cost+_vm_cost) < mincost:
                    mincost = get_cost+put_cost+_storage_cost+_vm_cost
                    storage_cost, vm_cost = _storage_cost, _vm_cost
                    min_get_cost, min_put_cost = get_cost, put_cost
                    selected_placement = combination
                    read_lat, write_lat = latency, latency
                    m_g = m
        
    # Calculate other costs
    if selected_placement is None:
        return None
    selected_dcs = selected_placement[0][1]
    iq1 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq2 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    # Generate iq1, iq2 
    for i, val in enumerate(selected_placement):
        for j in val[2]:
            iq1[i][j] = 1
        for j in val[3]:
            iq2[i][j] = 1
    return (selected_dcs, m_g, iq1, iq2, read_lat, write_lat, 
                min_get_cost, min_put_cost, storage_cost, vm_cost)


def min_latency_cas(datacenters, group, params):
    """ Latency based heuristic
    """
    dc_ids = [int(dc.id) for dc in datacenters]
    mincost = 999999
    min_get_cost = 0
    min_put_cost = 0
    read_lat = 0
    write_lat = 0
    selected_placement = None
    M, K = 0, 0
    storage_cost, vm_cost = 0, 0
    for m_g, k_g, q1, q2, q3, q4 in params:
        # May pre-compute this. (though itertool is optimized)
        # Get possible combination of DCs (of size m) from the set of DCs
        possible_dcs = combinations(dc_ids, m_g)
        for dcs in possible_dcs:
            get_lat = 0
            put_lat = 0
            _get_cost = 0
            _put_cost = 0
            combination = []
            for datacenter in datacenters:
                # Get possible combination of DCs (of size q1 and q2) from the 
                # m-sized set of DCs.
                latency_list = [(d,datacenter.latencies[d]) for d in dcs]
                latency_list.sort(key=lambda x: x[1])
                _iq1 = [l[0] for l in latency_list[:q1]]
                _iq2 = [l[0] for l in latency_list[:q2]]
                _iq3 = [l[0] for l in latency_list[:q3]]
                _iq4 = [l[0] for l in latency_list[:q4]]
                # Check if the selection meets latency constraints
                i = int(datacenter.id)
                get_lat += group.client_dist[i] * \
                            (max([datacenter.latencies[j] for j in _iq1]) + \
                                max([datacenter.latencies[k] for k in _iq4]))
                put_lat += group.client_dist[i] * \
                            (max([datacenter.latencies[j] for j in _iq1]) + \
                                max([datacenter.latencies[k] for k in _iq2]) + \
                                    max([datacenter.latencies[m] for m in _iq3]))
                _get_cost += group.client_dist[i] * \
                                (group.metadata_size*sum([datacenters[i].network_cost for j in _iq1]) + \
                                    (group.object_size/k_g)*sum([datacenters[k].network_cost for k in _iq4]))
                _put_cost += group.client_dist[i] * \
                                (group.metadata_size*(sum([datacenters[i].network_cost for j in _iq1]) + \
                                                        sum([datacenters[i].network_cost for k in _iq3])) + \
                                    (group.object_size/k_g)*sum([datacenters[m].network_cost for m in _iq2]))

                combination.append((get_lat, put_lat, dcs, _iq1, _iq2, _iq3, _iq4))
            if get_lat < group.slo_read and put_lat < group.slo_write:
                get_cost = group.read_ratio*group.arrival_rate*_get_cost
                put_cost = group.read_ratio*group.arrival_rate*_put_cost
                _storage_cost = group.num_objects*sum([datacenters[i].details["storage_cost"] \
                                                        for i in dcs])*(group.object_size/K)
                _vm_cost = sum([datacenters[i].details["price"] for i in dcs])
                if (get_cost+put_cost+_storage_cost+_vm_cost) < mincost:
                    mincost = get_cost+put_cost+_storage_cost+_vm_cost
                    min_get_cost, min_put_cost = get_cost, put_cost
                    storage_cost, vm_cost = _storage_cost, _vm_cost
                    read_lat, write_lat = get_lat, put_lat
                    selected_placement = combination
                    M, K = m_g, k_g
    # Calculate other costs
    if selected_placement is None:
        return None
    selected_dcs = selected_placement[0][2]
    iq1 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq2 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq3 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq4 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    for i, val in enumerate(selected_placement):
        for j in val[3]:
            iq1[i][j] = 1
        for j in val[4]:
            iq2[i][j] = 1
        for j in val[5]:
            iq3[i][j] = 1
        for j in val[6]:
            iq4[i][j] = 1
    return (M, K, selected_dcs, iq1, iq2, iq3, iq4, read_lat, write_lat, \
                min_get_cost, min_put_cost, storage_cost, vm_cost)

def min_cost_abd(datacenters, group, params):
    """ Network cost based greedy heuristic
    """
    dc_ids = [int(dc.id) for dc in datacenters]
    mincost = 999999
    min_get_cost = 0
    min_put_cost = 0
    read_lat = 0
    write_lat = 0
    selected_placement = None
    m_g = 0
    storage_cost, vm_cost = 0, 0
    cost_dc_list = [(i, d.network_cost) for i, d in enumerate(datacenters)]
    cost_dc_list.sort(key=lambda x: x[1])
    for m, q1, q2 in params:
        # May pre-compute this. (though itertool is optimized)
        # Get possible combination of DCs (of size m) from the set of DCs
        possible_dcs = combinations(dc_ids, m)
        for dcs in possible_dcs:
            latency = 0
            _get_cost = 0
            _put_cost = 0
            combination = []
            cost_list = [elem for elem in cost_dc_list if elem[0] in dcs]
            for datacenter in datacenters:
                # Get possible combination of DCs (of size q1 and q2) from the 
                # m-sized set of DCs.
                _iq1 = [l[0] for l in cost_list[:q1]]
                _iq2 = [l[0] for l in cost_list[:q2]]
                # Check if the selection meets latency constraints
                i = int(datacenter.id)
                latency += group.client_dist[i]*\
                            (max([datacenter.latencies[j] for j in _iq1])+\
                                max(datacenter.latencies[k] for k in _iq2))

                _get_cost += group.client_dist[i] * \
                                (sum([datacenters[i].network_cost for j in _iq1]) + \
                                    sum([datacenters[k].network_cost for k in _iq2]))
                _put_cost += group.client_dist[i] * \
                                (group.metadata_size*sum([datacenters[i].network_cost for j in _iq1]) + \
                                    group.object_size*sum([datacenters[k].network_cost for k in _iq2]))
                combination.append((latency, dcs, _iq1, _iq2))
            if latency < group.slo_read and latency < group.slo_write:
                get_cost = group.read_ratio*group.arrival_rate*group.object_size*_get_cost
                put_cost = group.read_ratio*group.arrival_rate*_put_cost
                _storage_cost = group.num_objects*\
                                sum([datacenters[i].details["storage_cost"] for i in dcs])*\
                                    group.object_size
                _vm_cost = sum([datacenters[i].details["price"] for i in dcs])
                if (get_cost+put_cost+_storage_cost+_vm_cost) < mincost:
                    mincost = get_cost+put_cost+_storage_cost+_vm_cost
                    storage_cost, vm_cost = _storage_cost, _vm_cost
                    min_get_cost, min_put_cost = get_cost, put_cost
                    selected_placement = combination
                    read_lat, write_lat = latency, latency
                    m_g = m
    # Calculate other costs
    if selected_placement is None:
        return None
    selected_dcs = selected_placement[0][1]
    storage_cost = group.num_objects*sum([datacenters[i].details["storage_cost"] \
                                            for i in selected_dcs])*group.object_size
    vm_cost = sum([datacenters[i].details["price"] for i in selected_dcs])
    iq1 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq2 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    # Generate iq1, iq2 
    for i, val in enumerate(selected_placement):
        for j in val[2]:
            iq1[i][j] = 1
        for j in val[3]:
            iq2[i][j] = 1
    return (m_g, selected_dcs, iq1, iq2, read_lat, write_lat, 
                min_get_cost, min_put_cost, storage_cost, vm_cost)

def min_cost_cas(datacenters, group, params):
    """ Network cost based heuristic
    """
    dc_ids = [int(dc.id) for dc in datacenters]
    mincost = 999999
    min_get_cost = 0
    min_put_cost = 0
    read_lat = 0
    write_lat = 0
    selected_placement = None
    cost_dc_list = [(i, d.network_cost) for i, d in enumerate(datacenters)]
    cost_dc_list.sort(key=lambda x: x[1])
    M, K = 0, 0
    storage_cost, vm_cost = 0, 0
    for m_g, k_g, q1, q2, q3, q4 in params:
        # May pre-compute this. (though itertool is optimized)
        # Get possible combination of DCs (of size m) from the set of DCs
        possible_dcs = combinations(dc_ids, m_g)
        for dcs in possible_dcs:
            get_lat = 0
            put_lat = 0
            combination = []
            _get_cost = 0
            _put_cost = 0
            cost_list = [elem for elem in cost_dc_list if elem[0] in dcs]
            for datacenter in datacenters:
                # Get possible combination of DCs (of size q1 and q2) from the 
                # m-sized set of DCs.
                _iq1 = [l[0] for l in cost_list[:q1]]
                _iq2 = [l[0] for l in cost_list[:q2]]
                _iq3 = [l[0] for l in cost_list[:q3]]
                _iq4 = [l[0] for l in cost_list[:q4]]
                # Check if the selection meets latency constraints
                i = int(datacenter.id)
                get_lat += group.client_dist[i] * \
                            (max([datacenter.latencies[j] for j in _iq1]) + \
                                max([datacenter.latencies[k] for k in _iq4]))
                put_lat += group.client_dist[i] * \
                            (max([datacenter.latencies[j] for j in _iq1]) + \
                                max([datacenter.latencies[k] for k in _iq2]) + \
                                    max([datacenter.latencies[m] for m in _iq3]))
                _get_cost += group.client_dist[i] * \
                                (group.metadata_size*sum([datacenters[i].network_cost for j in _iq1]) + \
                                    (group.object_size/k_g)*sum([datacenters[k].network_cost for k in _iq4]))
                _put_cost += group.client_dist[i] * \
                                (group.metadata_size*(sum([datacenters[i].network_cost for j in _iq1]) + \
                                                        sum([datacenters[i].network_cost for k in _iq3])) + \
                                    (group.object_size/k_g)*sum([datacenters[m].network_cost for m in _iq2]))

                combination.append((get_lat, put_lat, dcs, _iq1, _iq2, _iq3, _iq4))
            if get_lat < group.slo_read and put_lat < group.slo_write:
                get_cost = group.read_ratio*group.arrival_rate*_get_cost
                put_cost = group.read_ratio*group.arrival_rate*_put_cost
                _storage_cost = group.num_objects*sum([datacenters[i].details["storage_cost"] \
                                                        for i in dcs])*(group.object_size/K)
                _vm_cost = sum([datacenters[i].details["price"] for i in dcs])
                if (get_cost+put_cost+_storage_cost+_vm_cost) < mincost:
                    mincost = get_cost+put_cost+_storage_cost+_vm_cost
                    min_get_cost, min_put_cost = get_cost, put_cost
                    storage_cost, vm_cost = _storage_cost, _vm_cost
                    read_lat, write_lat = get_lat, put_lat
                    selected_placement = combination
                    M, K = m_g, k_g
    # Calculate other costs
    if selected_placement is None:
        return None
    selected_dcs = selected_placement[0][2]
    iq1 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq2 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq3 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq4 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    # Generate iq1, iq2 
    for i, val in enumerate(selected_placement):
        for j in val[3]:
            iq1[i][j] = 1
        for j in val[4]:
            iq2[i][j] = 1
        for j in val[5]:
            iq3[i][j] = 1
        for j in val[6]:
            iq4[i][j] = 1
    return (M, K, selected_dcs, iq1, iq2, iq3, iq4, read_lat, write_lat, \
                min_get_cost, min_put_cost, storage_cost, vm_cost)

def brute_force_abd(datacenters, group, params):
    """ Find placement for ABD using brute force
    """
    dc_ids = [int(dc.id) for dc in datacenters]
    mincost = 999999
    min_get_cost = 0
    min_put_cost = 0
    read_lat = 0
    write_lat = 0
    selected_placement = None
    m_g = 0
    for m, q1, q2 in params:
        # May pre-compute this. (though itertool is optimized)
        # Get possible combination of DCs (of size m) from the set of DCs
        possible_dcs = combinations(dc_ids, m)
        for dcs in possible_dcs:
            # Get possible combination of DCs (of size q1 and q2) from the 
            # m-sized set of DCs.
            possible_quorum_dcs = []
            possible_quorum_dcs.append(combinations(dcs, q1))
            possible_quorum_dcs.append(combinations(dcs, q2))
            # Check if the selection meets latency constraints
            d = []
            for dc in datacenters:
                col = []
                for _iq1 in possible_quorum_dcs[0]: 
                    #_iq1 stores indices of non-zero iq1 variables
                    for _iq2 in possible_quorum_dcs[1]:
                        lat = group.client_dist[int(dc.id)] * \
                                (max([dc.latencies[j] for j in _iq1]) + \
                                    max([dc.latencies[k] for k in _iq2]))
                        col.append((lat, dcs, _iq1, _iq2))
                d.append(col)
            print(len(d), len(d[0])) 
            for comb in product(*d):
                lat = 0
                _get_cost = 0
                _put_cost = 0
                for i, val in enumerate(comb):
                    lat += val[0]
                    _iq1 = val[2]
                    _iq2 = val[3]
                    _get_cost += group.client_dist[i] * \
                                    (sum([datacenters[i].network_cost for j in _iq1]) + \
                                        sum([datacenters[k].network_cost for k in _iq2]))
                    _put_cost += group.client_dist[i] * \
                                    (group.metadata_size*sum([datacenters[i].network_cost for j in _iq1]) + \
                                        group.object_size*sum([datacenters[k].network_cost for k in _iq2]))
                if lat < group.slo_read and lat < group.slo_write:
                    # Calculate cost
                    get_cost = group.read_ratio*group.arrival_rate*group.object_size*_get_cost
                    put_cost = group.read_ratio*group.arrival_rate*_put_cost
                    if (get_cost+put_cost) < mincost:
                        mincost = get_cost+put_cost
                        min_get_cost = get_cost
                        min_put_cost = put_cost
                        selected_placement = comb
                        read_lat = lat
                        write_lat = lat
                        m_g = m
    # Calculate other costs
    selected_dcs = selected_placement[0][1]
    storage_cost = group.num_objects*sum([datacenters[i].details["storage_cost"] \
                                            for i in selected_dcs])*group.object_size
    vm_cost = sum([datacenters[i].details["price"] for i in selected_dcs])
    iq1 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq2 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    # Generate iq1, iq2 
    for i, val in enumerate(selected_placement):
        for j in val[2]:
            iq1[i][j] = 1
        for j in val[3]:
            iq2[i][j] = 1
    return (m_g, selected_dcs, iq1, iq2, read_lat, write_lat, 
                min_get_cost, min_put_cost, storage_cost, vm_cost)
    

def brute_force_cas(datacenters, group, params):
    """ Find placement for CAS using brute force
    """
    dc_ids = [int(dc.id) for dc in datacenters]
    mincost = 999999
    min_get_cost = 0
    min_put_cost = 0
    read_lat = 0
    write_lat = 0
    selected_placement = None
    M, K = 0, 0
    for param in params:
        # May pre-compute this. (though itertool is optimized)
        # Get possible combination of DCs (of size m) from the set of DCs
        m_g = param[0]
        k_g = param[1]
        q_sizes = param[2:]
        possible_dcs = combinations(dc_ids, m_g)
        for dcs in possible_dcs:
            # Get possible combination of DCs (of size q1 and q2) from the 
            # m-sized set of DCs.
            possible_quorum_dcs = []
            for size in q_sizes:
                possible_quorum_dcs.append(combinations(dcs, size))
            # Check if the selection meets latency constraints
            d = []
            for dc in datacenters:
                col = []
                for _iq1 in possible_quorum_dcs[0]: 
                    #_iq1 stores indices of non-zero iq1 variables
                    for _iq2 in possible_quorum_dcs[1]:
                        for _iq3 in possible_quorum_dcs[2]:
                            for _iq4 in possible_quorum_dcs[3]:
                                get_lat = group.client_dist[int(dc.id)] * \
                                            (max([dc.latencies[j] for j in _iq1]) + \
                                                max([dc.latencies[k] for k in _iq4]))
                                put_lat = group.client_dist[int(dc.id)] * \
                                            (max([dc.latencies[j] for j in _iq1]) + \
                                                max([dc.latencies[k] for k in _iq2]) + \
                                                    max([dc.latencies[m] for m in _iq3]))
                                col.append((get_lat, put_lat, dcs, _iq1, _iq2, _iq3, _iq4))
                d.append(col)
            print(len(d), len(d[0])) 
            for comb in product(*d):
                get_lat = 0
                put_lat = 0
                _get_cost = 0
                _put_cost = 0
                for i, val in enumerate(comb):
                    get_lat += val[0]
                    put_lat += val[1]
                    _iq1 = val[3]
                    _iq2 = val[4]
                    _iq3 = val[5]
                    _iq4 = val[6]
                    _get_cost += group.client_dist[i] * \
                                    (group.metadata_size*sum([datacenters[i].network_cost for j in _iq1]) + \
                                        (group.object_size/k_g)*sum([datacenters[k].network_cost for k in _iq4]))
                    _put_cost += group.client_dist[i] * \
                                    (group.metadata_size*(sum([datacenters[i].network_cost for j in _iq1]) + \
                                                            sum([datacenters[i].network_cost for k in _iq3])) + \
                                        (group.object_size/k_g)*sum([datacenters[m].network_cost for m in _iq2]))
                if get_lat < group.slo_read and put_lat < group.slo_write:
                    # Calculate cost
                    get_cost = group.read_ratio*group.arrival_rate*_get_cost
                    put_cost = group.read_ratio*group.arrival_rate*_put_cost
                    if (get_cost+put_cost) < mincost:
                        mincost = get_cost+put_cost
                        min_get_cost, min_put_cost = get_cost, put_cost
                        read_lat, write_lat = get_lat, put_lat
                        selected_placement = comb
                        M, K = m_g, k_g
    # Calculate other costs
    selected_dcs = selected_placement[0][2]
    storage_cost = group.num_objects*sum([datacenters[i].details["storage_cost"] \
                                            for i in selected_dcs])*group.object_size/K
    vm_cost = sum([datacenters[i].details["price"] for i in selected_dcs])
    iq1 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq2 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq3 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    iq4 = [[0]*len(dc_ids) for _ in range(len(dc_ids))]
    # Generate iq1, iq2 
    for i, val in enumerate(selected_placement):
        for j in val[3]:
            iq1[i][j] = 1
        for j in val[4]:
            iq2[i][j] = 1
        for j in val[5]:
            iq3[i][j] = 1
        for j in val[6]:
            iq4[i][j] = 1
    return (selected_dcs, iq1, iq2, iq3, iq4, M, K, read_lat, write_lat, \
                min_get_cost, min_put_cost, storage_cost, vm_cost)


def get_placement(obj, heuristic):
    N = len(obj.datacenters)
    G = len(obj.groups)
    # Iterate over groups and find placements for each group
    for group in obj.groups:
        protocol = obj.protocol
        f = group.availability_target
        # Generate possible param tuples (quorum sizes, code dimension, length)
        # that conforms to the constraints.
        params = generate_placement_params(N, f, protocol)
        ret = eval(FUNC_HEURISTIC_MAP[protocol][heuristic])(obj.datacenters, group, params)
        print(ret)
        #TODO encapsulate results into objects and dump to out file
