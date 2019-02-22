ABD = 'abd'
CAS = 'cas'
BRUTE_FORCE = 'brute_force'
MIN_COST = 'min_cost'
MIN_LATENCY = 'min_latency'

GROUP = "Group"
DATACENTER = "DataCenter"

GEN_ABD = 'gen_abd_params'
GEN_CAS = 'gen_cas_params'

PLACEMENT_ABD = 'PlacementAbd'
PLACEMENT_CAS = 'PlacementCas'

GEN_PARAM_FUNC = {
    ABD: GEN_ABD,
    CAS: GEN_CAS
}

PLACEMENT_CLASS_MAPPER = {
    ABD: PLACEMENT_ABD,
    CAS: PLACEMENT_CAS
}

FUNC_HEURISTIC_MAP = {
    ABD: {
        MIN_COST: MIN_COST+'_'+ABD,
        MIN_LATENCY: MIN_LATENCY+'_'+ABD,
        BRUTE_FORCE: BRUTE_FORCE+'_'+ABD
    },

    CAS: {
        MIN_COST: MIN_COST+'_'+CAS,
        MIN_LATENCY: MIN_LATENCY+'_'+CAS,
        BRUTE_FORCE: BRUTE_FORCE+'_'+CAS
    }
}
