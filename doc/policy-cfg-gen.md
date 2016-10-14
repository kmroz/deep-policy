# DeepSea policy.cfg Generation #

## Goal ##

To provide an interactive tool allowing admins to generate an initial policy.cfg
file used by Salt/DeepSea to deploy a SES cluster.

## Pre-Reqs ##

1. A running cluster with:
    - 1 _salt-master_ admin node
    - N _salt-minion_ nodes
2. __DeepSea__ installed
3. Orchestration __Stage 0__ and __Stage 1__ have been successfully invoked

## Cluster SLS/YAML File Layout (example) ##

- Available Nodes
    - `/srv/pillar/ceph/proposals/cluster-ceph/*.sls`
- Common Configurations
    - `/srv/pillar/ceph/proposals/config/stack/default/global.yml`
    - `/srv/pillar/ceph/stack/default/global.yml`
    - `/srv/pillar/ceph/stack/default/ceph/ceph_conf.yml`
- Available Storage HW
    - `/srv/pillar/ceph/proposals/1Disk20GB-1/cluster/*.sls`
    - `/srv/pillar/ceph/proposals/1Disk20GB-1/stack/default/ceph/minions/*.yml`
- Available Roles
    - `/srv/pillar/ceph/proposals/role-{X}/cluster/*.sls`
    - `/srv/pillar/ceph/proposals/role-mon/stack/default/ceph/minions/*.yml`

## policy.cfg ##

- location: /srv/pillar/ceph/proposals/policy.cfg

        # Cluster assignment
        cluster-ceph/cluster/*.sls
        # Hardware Profile
        1Disk20GB-1/cluster/*.sls
        1Disk20GB-1/stack/default/ceph/minions/*.yml
        # Common configuration
        config/stack/default/global.yml
        config/stack/default/ceph/cluster.yml
        # Role assignment
        role-master/cluster/salttest-1.lan.sls
        role-admin/cluster/*.sls
        role-rgw/cluster/salttest-1.lan.sls
        role-mon/cluster/salttest-[1234].lan.sls
        role-mon/stack/default/ceph/minions/salttest-[1234].lan.yml

### policy.cfg Sections ###

- Cluster assignment
    - Specifies nodes (represented by SLS files) that are part of the cluster
    - SLS files located in: `/srv/pillar/ceph/proposals/cluster-ceph/cluster/`
    - SLS files populated by __Stage 1__
    - Accepts globs
    - Sample `/srv/pillar/ceph/proposals/cluster-ceph/cluster/salttest-1.lan.sls`

            cluster: ceph

- Hardware Profile
    - Storage node hardware profiles
        - Available storage disk layout on a node/chassis
    - `/srv/pillar/ceph/proposals/1Disk20GB-1`
        - `cluster/`
            - Defines node SLS files that can be added to this profile
            - Sample `/srv/pillar/ceph/proposals/1Disk20GB-1/cluster/salttest-1.lan.sls`

                    roles:
                    - storage

        - `stack/default/ceph/minions/`
            - Defines node YAML files that specify OSD layout
            - Sample `/srv/pillar/ceph/proposals/1Disk20GB-1/stack/default/ceph/minions/salttest-1.lan.yml`

                    storage:
                      data+journals: []
                      osds:
                      - /dev/vdb

- Common configuration
    - Various generated configuration options that can be overridden
    - `/srv/pillar/ceph/stack/global.yml` overrides
    `/srv/pillar/ceph/proposals/config/stack/default/global.yml` for example

- Role assignment
    - Specifies roles for the various nodes
    - `/srv/pillar/ceph/proposals/role-X/cluster` contain node SLS files specifying
    a particular role for a node


## Design ##

    --------------------------------------------------------------------------------------
    | Cluster |                                                                          |
    |----------                                                                          |
    |                                                                                    |
    |    [available_nodes]: String                                                       |
    |    [nodes]: String                                                                 |
    |                                                                                    |
    |    -------------------   -------------------                                       |
    |    | Role |          |   | Role |          |                                       |
    |    |-------          |   |-------          |                                       |
    |    |                 |...|                 |                                       |
    |    | [nodes]: String |   | [nodes]: String |                                       |
    |    |------------------   |------------------                                       |
    |                                                                                    |
    |                                                                                    |
    |                                                                                    |
    |-------------------------------------------------------------------------------------
    

After some thought, a Role-based treatment of data simplifies the Node to just a string.
Also, most of the User interaction will be the act of adding/removing Nodes to and from Roles.
Roles can be thought of as Node containers. The Cluster is a container for Roles (with knowledge
of which Nodes are included).

Node addition to a cluster is nothing more than appending a name to [Cluster:nodes]. On a Node
removal from the Cluster, all Roles will need to be searched for that Node and the
Node will need to be removed. While not great, Role verification (ie. enough Mons?
enough OSDs?) will be very inexpensive.  Adding and removing Nodes
from a Role is no more expensive than manipulating the array of Nodes (strings).

For Node numbers > Role numbers, asking the User the question: "which Nodes to add to Role-X?"
is more efficient than asking the inverse for each Node. Also, there is a relatively small
number of Roles so it won't be too painful for smaller clusters either.

If on the other hand Nodes contained Roles, a Node removal from the Cluster would be easy,
but Role validation would be more expensive (Node traversal). Also, adding/removing Nodes to
and from a Role would require Node traversal.

Likely the User will add the Nodes to the Cluster once, but may continue to change the number
of Nodes in various Roles.

The Cluster manages both Nodes and Roles.

### Data Model ###

- __Node__
    - id: hostname/salt minion name (unique)

- __Role__
    - nodes: [List of Node's belonging to this Role]
    - _Subclasses_
        - AdminRole
        - IGWRole
        - IGWClientRole
        - MasterRole
        - MDSRole
        - MDSClientRole
        - MDSNFSRole
        - MonRole
        - RGWRole
        - RGWClientRole
        - RGWNFSRole
        - StorageRole

- __Cluster__
    - available\_nodes: [list of available _Nodes_ ]
    - nodes: [list of _Nodes_ belonging to the cluster]
    - roles: [list of _Roles_ used by the cluster]
        - _Roles_ with an empty _Nodes_ list are considered to __not__ be included in
        the cluster

- __PolicyWriter__
    - output_file: filename to write policy.cfg (/srv/pillar/ceph/proposals/policy.cfg)

### Operations ###

- __Discover available Nodes__
    - Populate [Cluster:available_nodes] node list from
    /srv/pillar/ceph/proposals/cluster-ceph/cluster/*.sls
    - Empty list, error and bail out
- __Query User which Nodes to add to Cluster__
    - Should populate [Cluster:nodes] list
    - If no nodes added, re-prompt/bail out
- __Add Node to Cluster__
    - Move Node from [Cluster:available_nodes] to [Cluster:nodes]
- __Remove Node from Cluster__
    - Move Node from [Cluster:nodes] to [Cluster:avaiable_nodes]
- __Populate available Roles__
    - Should populate all availalble roles [Cluster:roles] list from
    /svr/pillar/ceph/proposals/role-*
    - [Cluster:available_roles] not needed as we will add all Roles to the [Cluster:nodes] list
        - Roles which are actually utilized are once which are __not__ empty
    - If no roles found, error and bail out
    - if role-X is not known, error and bail out
    - May want to veryify if potential Nodes are found within the Roles directory before adding
    the Role to the list
- __Query User which Nodes to add to which Roles__
    - For each Role, query which available Nodes to add
        - For avaialble Node numbers > number of available Roles, this is a more efficient question
    - A Role with no available Nodes should be skipped
- __Assign Node to Role__
    - For a given Role, append Node to [Role:nodes]
- __Remove Role from Node__
    - For a given Role, remove Node from [Role:nodes]
- __Role validation__
    - For each Role in [Cluster
- __Write out policy.cfg__
    - Given a Cluster
        - Write out Nodes included in the Cluster (ie. [Cluster:nodes])
        - Write out common info section
        - For each Role (StorageRole === 1Disk10GB-1 for example)
            - Write out each Node included in the Role
