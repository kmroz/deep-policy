################################################################################
# dspw_lib.py
# ------------
#
# DeepSea Profile Wizard (dspw) library.
################################################################################

import sys
import glob

class Node(str):
    '''
    Syntactic candy for a Node. It's really just a string.
    '''


class Role(object):
    '''
    Roles contain a number of Nodes.
    '''
    def __init__(self):
        self.available_nodes = []  # Available Nodes to add to this Role.
        self.nodes = []            # Nodes which have been added to the Role.


class AdminRole(Role): pass
class IGWRole(Role): pass
class IGWClientRole(Role): pass
class MasterRole(Role): pass
class MDSRole(Role): pass
class MDSClientRole(Role): pass
class MDSNFSRole(Role): pass
class MonRole(Role): pass
class RGWRole(Role): pass
class RGWClientRole(Role): pass
class RGWNFSRole(Role): pass
class StorageRole(Role): pass # TODO: Will be empty. Storage Nodes will need to link to hw profile dir.


# A mapping of Role names to actual Classes. Used during Role discovery to instantiate
# Cluster:[roles]
role_map = { "role-admin"       : AdminRole,
             "role-igw"         : IGWRole,
             "role-igw-client"  : IGWClientRole,
             "role-master"      : MasterRole,
             "role-mds"         : MDSRole,
             "role-mds-client"  : MDSClientRole,
             "role-mds-nfs"     : MDSNFSRole,
             "role-mon"         : MonRole,
             "role-rgw"         : RGWRole,
             "role-rgw-client"  : RGWClientRole,
             "role-rgw-nfs"     : RGWNFSRole,
             "role-storage"     : StorageRole
}


class Cluster(object):
    '''
    A Cluster contains a number of usable Nodes as well as a number of Roles.
    '''

    def __init__(self, proposal_dir="/srv/pillar/ceph/proposals/"):
        self.proposal_dir = proposal_dir  # Proposal directory containing SLS and YAML files
        self.cluster_sls_dir = proposal_dir + "/cluster-ceph/cluster/"
        self.available_nodes = []         # Available Nodes to add to the Cluster
        self.nodes = []                   # Nodes added to the Cluster
        self.roles = []                   # Potential Roles in the Cluster

    def discover_nodes(self):
        '''
        Discover list of available Nodes that can be added to this Cluster.
        '''
        cluster_sls_files = glob.glob(self.cluster_sls_dir + "*.sls")

        # Wipe self.available_nodes first.
        self.available_nodes = []

        for f in cluster_sls_files:
            # From something like "/srv/pillar/ceph/proposals/cluster-ceph/cluster/node-1.foo.bar.sls"
            # we extract "node-1.foo.bar" and create our Node
            self.available_nodes.append(Node(f.split('/')[-1].split('.sls')[0]))

        # For ease of viewing, let's sort the list alphabetically
        self.available_nodes.sort()

    def add_node(self, Node):
        '''
        Add a Node to this Cluster. Checks the list of available nodes.
        '''
        if Node in self.available_nodes:
            self.nodes.append(Node)
            self.nodes.sort()
            self.available_nodes.remove(Node)
        else:
            # We are trying to add a Node that is not listed as available. Let the caller
            # handle the exception.
            raise ValueError("{} is not an available node in this cluster.")

    def remove_node(self, Node):
        '''
        Remove a Node from the cluster, and reposition it in the available list.
        TODO: When removing a Node, will need to remove it from any Roles as well.
        '''
        if Node in self.nodes:
            self.nodes.remove(Node)
            self.available_nodes.append(Node)
            self.available_nodes.sort()
        else:
            # Attempt to remove a Node from the cluster that was not added.
            raise ValueError("{} has not been added to this cluster.")

    def discover_roles(self):
        '''
        Discover available Roles that can be added to this Cluster.
        '''
        cluster_role_dirs = glob.glob(self.proposal_dir + "role-*")
        cluster_role_names = []

        for d in cluster_role_dirs:
            # Populate self.roles with appropriate Role objects based on name.
            cluster_role_names.append(d.split('/')[-1].split('.sls')[0])

        cluster_role_names.sort()
        # Wipe self.roles first.
        self.roles = []

        for r in cluster_role_names:
            # Instantiate our list of Roles based on Role names found in the Cluster.
            try:
                self.roles.append(role_map[r]())
            except KeyError:
                print "Role {} is not supported by this script. " \
                    "To use {} in the cluster, add it manually to your policy.cfg".format(r, r)
