################################################################################
# test_dspw_lib.py
# ----------------
#
# Basic test cases for DeepSea Profile Wizard (dspw). Please note that these
# tests are meant to be run with the provided 'test-cluster' Salt proposals.
################################################################################

import sys
import glob
import dspw_lib as dspwl

test_cluster_proposal_path="./test-cluster/srv/pillar/ceph/proposals"

def test_node_creation():
    '''
    Nodes are just strings.
    '''
    node_name = "Node One"
    n1 = dspwl.Node(node_name)
    assert n1 == node_name

def test_available_node_discovery():
    '''
    Test that we've discovered the correct number of Nodes. Each SLS file should
    signify a Node.
    '''
    c = dspwl.Cluster(test_cluster_proposal_path)
    cluster_sls_files = glob.glob(c.cluster_sls_dir + "/*.sls")

    assert len(c.available_nodes) == len(cluster_sls_files)

def test_discovered_node_names():
    '''
    A Node name should match the SLS filename depicting that Node.
    '''
    c = dspwl.Cluster(test_cluster_proposal_path)
    cluster_sls_files = glob.glob(c.cluster_sls_dir + "/*.sls")

    # Needs to be sorted, as our Cluster:discover_nodes() provides a sorted Node list.
    cluster_sls_files.sort()
    for i in range(len(cluster_sls_files)):
        assert c.available_nodes[i] == cluster_sls_files[i].split('/')[-1].split('.sls')[0]

def test_add_node():
    '''
    Test addition of Node to the cluster.
    '''
    c = dspwl.Cluster(test_cluster_proposal_path)
    cluster_sls_files = glob.glob(c.cluster_sls_dir + "/*.sls")

    n = c.available_nodes[0]

    try:
        c.add_node(n)
    except ValueError:
        pass

    assert c.nodes[0] == n and n not in c.available_nodes

def test_add_unavailable_node():
    '''
    Test error handling when adding a Node that is not available to the cluster.
    '''
    c = dspwl.Cluster(test_cluster_proposal_path)
    cluster_sls_files = glob.glob(c.cluster_sls_dir + "/*.sls")

    try:
        c.add_node("NonExistentNode")
    except ValueError:
        pass

    assert len(c.nodes) == 0

def test_remove_node():
    '''
    Test Node removal.
    '''
    c = dspwl.Cluster(test_cluster_proposal_path)
    cluster_sls_files = glob.glob(c.cluster_sls_dir + "/*.sls")

    n = c.available_nodes[0]
    c.add_node(n)

    try:
        c.remove_node(n)
    except ValueError:
        pass

    assert n in c.available_nodes and n not in c.nodes

def test_remove_unavailable_node():
    '''
    Test error handling of invalid Node removal.
    '''
    c = dspwl.Cluster(test_cluster_proposal_path)
    cluster_sls_files = glob.glob(c.cluster_sls_dir + "/*.sls")

    n = c.available_nodes[0]
    c.add_node(n)
    l = len(c.nodes)

    try:
        c.remove_node("NonExistentNode")
    except ValueError:
        pass

    assert l == len(c.nodes)

def test_available_role_discovery():
    '''
    Test that we've discovered the correct number of Roles. Each role-x directory
    signifies a Role.
    '''
    c = dspwl.Cluster(test_cluster_proposal_path)
    cluster_role_dirs = glob.glob(c.proposal_dir + "/role-*")

    assert len(c.roles) == len(cluster_role_dirs)
