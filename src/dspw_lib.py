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

class NodeContainer(object):
    def __init__(self):
        self.available_nodes = []         # Available Nodes
        self.nodes = []                   # Nodes added

    def discover_nodes(self, path, extension):
        '''
        Discover list of available Nodes that can be added to this Container.
        Each Node is represented by an SLS file in a particular directory.
        '''
	node_sls_files = glob.glob(path + "/*." + extension)

	# Wipe available node list as we are discovering.
        self.available_nodes = []

	for f in node_sls_files:
            # From something like "/srv/pillar/ceph/proposals/cluster-ceph/cluster/node-1.foo.bar.sls"
            # we extract "node-1.foo.bar" and create our Node
            self.available_nodes.append(Node(f.split('/')[-1].split("." + extension)[0]))

        # For ease of viewing, let's sort the list alphabetically
        self.available_nodes.sort()

    def add_node(self, node):
        '''
        Add a Node to this Cluster. Checks the list of available nodes.
        '''
        if node in self.available_nodes:
            self.nodes.append(node)
            self.nodes.sort()
            self.available_nodes.remove(node)
        else:
            # We are trying to add a Node that is not listed as available. Let the caller
            # handle the exception.
	    raise ValueError("{} is not an available node in this cluster.".format(node))

    def remove_node(self, node):
        '''
        Remove a Node from the cluster, and reposition it in the available list.
        '''
        if node in self.nodes:
            self.nodes.remove(node)
            self.available_nodes.append(node)
            self.available_nodes.sort()
        else:
            # Attempt to remove a Node from the cluster that was not added.
	    raise ValueError("{} has not been added to this cluster.".format(node))


class Role(NodeContainer):
    '''
    Roles contain a number of Nodes.
    '''
    def __init__(self, role_dir):
	'''
	A Role is initialized with empty node lists. When a Node is added to a Cluster,
	the Cluster is responsible for invoking Node discovery on it's Roles.
	'''
        super(Role, self).__init__()
	self.role_dir = role_dir

    def discover_nodes(self, cluster_nodes):
	'''
	For a Role, only discover Nodes which are already added to the Cluster.
	'''
	# First, obtain all the Nodes possible for this Role.
	super(Role, self).discover_nodes(self.role_dir + "/cluster", "sls")
	# Strip away Nodes that are not in cluster_nodes.
	self.available_nodes = [n for n in self.available_nodes if n in cluster_nodes]


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


class Cluster(NodeContainer):
    '''
    A Cluster contains a number of usable Nodes as well as a number of Roles.
    '''

    def __init__(self, proposal_dir="/srv/pillar/ceph/proposals"):
        self.proposal_dir = proposal_dir  # Proposal directory containing SLS and YAML files
	self.cluster_sls_dir = proposal_dir + "/cluster-ceph/cluster"
        self.roles = []                   # Potential Roles in the Cluster
	super(Cluster, self).__init__()   # Will initialize node lists
	self.discover_nodes()
	self.discover_roles()

    def discover_nodes(self):
        super(Cluster, self).discover_nodes(self.cluster_sls_dir, "sls")

    def add_node(self, node):
	'''
	Part of adding a Node to the Cluster involves adding it to the list of available Nodes
	for a Role. Thus, on each Node addition to the cluster, rediscover Roles.
	'''
	super(Cluster, self).add_node(node)
	for r in self.roles:
	    r.discover_nodes(self.nodes)

    def remove_node(self, node):
	'''
	Part of removing a Node from the Cluster involves removing it from the list of available Nodes
	for a Role. Thus, on each Node removal from the cluster, rediscover Roles.
	'''
	super(Cluster, self).remove_node(node)
	for r in self.roles:
	    r.discover_nodes(self.nodes)

    def discover_roles(self):
        '''
	Discover available Roles that can be added to this Cluster. Roles start out pretty barren
	with empty node lists on discovery. When a Node is added to the Cluster, Node discovery for
	available Roles will be run to populate the Roles available Node list.
        '''
	cluster_roles = {}

	for d in glob.glob(self.proposal_dir + "/role-*"):
            # Populate self.roles with appropriate Role objects based on name.
	    cluster_roles[d.split('/')[-1].split('.sls')[0]] = d

        # Wipe self.roles first.
        self.roles = []

	for r,d in cluster_roles.items():
            # Instantiate our list of Roles based on Role names found in the Cluster.
            try:
		role = role_map[r](d)
		role.discover_nodes(self.nodes)
		self.roles.append(role)
            except KeyError:
                print "Role {} is not supported by this script. " \
                    "To use {} in the cluster, add it manually to your policy.cfg".format(r, r)
