.. _cgroup-v2:

================
Control Group v2
================

:Date: October, 2015
:Author: Tejun Heo <tj@kernel.org>

This is the authoritative documentation on the design, interface and
conventions of cgroup v2.  It describes all userland-visible aspects
of cgroup including core and specific controller behaviors.  All
future changes must be reflected in this document.  Documentation for
v1 is available under :ref:`Documentation/admin-guide/cgroup-v1/index.rst <cgroup-v1>`.

.. CONTENTS

   1. Introduction
     1-1. Terminology
     1-2. What is cgroup?
   2. Basic Operations
     2-1. Mounting
     2-2. Organizing Processes and Threads
       2-2-1. Processes
       2-2-2. Threads
     2-3. [Un]populated Notification
     2-4. Controlling Controllers
       2-4-1. Enabling and Disabling
       2-4-2. Top-down Constraint
       2-4-3. No Internal Process Constraint
     2-5. Delegation
       2-5-1. Model of Delegation
       2-5-2. Delegation Containment
     2-6. Guidelines
       2-6-1. Organize Once and Control
       2-6-2. Avoid Name Collisions
   3. Resource Distribution Models
     3-1. Weights
     3-2. Limits
     3-3. Protections
     3-4. Allocations
   4. Interface Files
     4-1. Format
     4-2. Conventions
     4-3. Core Interface Files
   5. Controllers
     5-1. CPU
       5-1-1. CPU Interface Files
     5-2. Memory
       5-2-1. Memory Interface Files
       5-2-2. Usage Guidelines
       5-2-3. Memory Ownership
     5-3. IO
       5-3-1. IO Interface Files
       5-3-2. Writeback
       5-3-3. IO Latency
         5-3-3-1. How IO Latency Throttling Works
         5-3-3-2. IO Latency Interface Files
       5-3-4. IO Priority
     5-4. PID
       5-4-1. PID Interface Files
     5-5. Cpuset
       5.5-1. Cpuset Interface Files
     5-6. Device
     5-7. RDMA
       5-7-1. RDMA Interface Files
     5-8. HugeTLB
       5.8-1. HugeTLB Interface Files
     5-9. Misc
       5.9-1 Miscellaneous cgroup Interface Files
       5.9-2 Migration and Ownership
     5-10. Others
       5-10-1. perf_event
     5-N. Non-normative information
       5-N-1. CPU controller root cgroup process behaviour
       5-N-2. IO controller root cgroup process behaviour
   6. Namespace
     6-1. Basics
     6-2. The Root and Views
     6-3. Migration and setns(2)
     6-4. Interaction with Other Namespaces
   P. Information on Kernel Programming
     P-1. Filesystem Support for Writeback
   D. Deprecated v1 Core Features
   R. Issues with v1 and Rationales for v2
     R-1. Multiple Hierarchies
     R-2. Thread Granularity
     R-3. Competition Between Inner Nodes and Threads
     R-4. Other Interface Issues
     R-5. Controller Issues and Remedies
       R-5-1. Memory


Introduction
============

Terminology
-----------

"cgroup" stands for "control group" and is never capitalized.  The
singular form is used to designate the whole feature and also as a
qualifier as in "cgroup controllers".  When explicitly referring to
multiple individual control groups, the plural form "cgroups" is used.


What is cgroup?
---------------

cgroup is a mechanism to organize processes hierarchically and
distribute system resources along the hierarchy in a controlled and
configurable manner.

cgroup is largely composed of two parts - the core and controllers.
cgroup core is primarily responsible for hierarchically organizing
processes.  A cgroup controller is usually responsible for
distributing a specific type of system resource along the hierarchy
although there are utility controllers which serve purposes other than
resource distribution.

cgroups form a tree structure and every process in the system belongs
to one and only one cgroup.  All threads of a process belong to the
same cgroup.  On creation, all processes are put in the cgroup that
the parent process belongs to at the time.  A process can be migrated
to another cgroup.  Migration of a process doesn't affect already
existing descendant processes.

Following certain structural constraints, controllers may be enabled or
disabled selectively on a cgroup.  All controller behaviors are
hierarchical - if a controller is enabled on a cgroup, it affects all
processes which belong to the cgroups consisting the inclusive
sub-hierarchy of the cgroup.  When a controller is enabled on a nested
cgroup, it always restricts the resource distribution further.  The
restrictions set closer to the root in the hierarchy can not be
overridden from further away.


Basic Operations
================

Mounting
--------

Unlike v1, cgroup v2 has only single hierarchy.  The cgroup v2
hierarchy can be mounted with the following mount command::

  # mount -t cgroup2 none $MOUNT_POINT

cgroup2 filesystem has the magic number 0x63677270 ("cgrp").  All
controllers which support v2 and are not bound to a v1 hierarchy are
automatically bound to the v2 hierarchy and show up at the root.
Controllers which are not in active use in the v2 hierarchy can be
bound to other hierarchies.  This allows mixing v2 hierarchy with the
legacy v1 multiple hierarchies in a fully backward compatible way.

A controller can be moved across hierarchies only after the controller
is no longer referenced in its current hierarchy.  Because per-cgroup
controller states are destroyed asynchronously and controllers may
have lingering references, a controller may not show up immediately on
the v2 hierarchy after the final umount of the previous hierarchy.
Similarly, a controller should be fully disabled to be moved out of
the unified hierarchy and it may take some time for the disabled
controller to become available for other hierarchies; furthermore, due
to inter-controller dependencies, other controllers may need to be
disabled too.

While useful for development and manual configurations, moving
controllers dynamically between the v2 and other hierarchies is
strongly discouraged for production use.  It is recommended to decide
the hierarchies and controller associations before starting using the
controllers after system boot.

During transition to v2, system management software might still
automount the v1 cgroup filesystem and so hijack all controllers
during boot, before manual intervention is possible. To make testing
and experimenting easier, the kernel parameter cgroup_no_v1= allows
disabling controllers in v1 and make them always available in v2.

cgroup v2 currently supports the following mount options.

  nsdelegate
	Consider cgroup namespaces as delegation boundaries.  This
	option is system wide and can only be set on mount or modified
	through remount from the init namespace.  The mount option is
	ignored on non-init namespace mounts.  Please refer to the
	Delegation section for details.

  favordynmods
        Reduce the latencies of dynamic cgroup modifications such as
        task migrations and controller on/offs at the cost of making
        hot path operations such as forks and exits more expensive.
        The static usage pattern of creating a cgroup, enabling
        controllers, and then seeding it with CLONE_INTO_CGROUP is
        not affected by this option.

  memory_localevents
        Only populate memory.events with data for the current cgroup,
        and not any subtrees. This is legacy behaviour, the default
        behaviour without this option is to include subtree counts.
        This option is system wide and can only be set on mount or
        modified through remount from the init namespace. The mount
        option is ignored on non-init namespace mounts.

  memory_recursiveprot
        Recursively apply memory.min and memory.low protection to
        entire subtrees, without requiring explicit downward
        propagation into leaf cgroups.  This allows protecting entire
        subtrees from one another, while retaining free competition
        within those subtrees.  This should have been the default
        behavior but is a mount-option to avoid regressing setups
        relying on the original semantics (e.g. specifying bogusly
        high 'bypass' protection values at higher tree levels).

  memory_hugetlb_accounting
        Count HugeTLB memory usage towards the cgroup's overall
        memory usage for the memory controller (for the purpose of
        statistics reporting and memory protetion). This is a new
        behavior that could regress existing setups, so it must be
        explicitly opted in with this mount option.

        A few caveats to keep in mind:

        * There is no HugeTLB pool management involved in the memory
          controller. The pre-allocated pool does not belong to anyone.
          Specifically, when a new HugeTLB folio is allocated to
          the pool, it is not accounted for from the perspective of
          the memory controller. It is only charged to a cgroup when it is
          actually used (for e.g at page fault time). Host memory
          overcommit management has to consider this when configuring
          hard limits. In general, HugeTLB pool management should be
          done via other mechanisms (such as the HugeTLB controller).
        * Failure to charge a HugeTLB folio to the memory controller
          results in SIGBUS. This could happen even if the HugeTLB pool
          still has pages available (but the cgroup limit is hit and
          reclaim attempt fails).
        * Charging HugeTLB memory towards the memory controller affects
          memory protection and reclaim dynamics. Any userspace tuning
          (of low, min limits for e.g) needs to take this into account.
        * HugeTLB pages utilized while this option is not selected
          will not be tracked by the memory controller (even if cgroup
          v2 is remounted later).

  pids_localevents
        The option restores v1-like behavior of pids.events:max, that is only
        local (inside cgroup proper) fork failures are counted. Without this
        option pids.events.max represents any pids.max enforcemnt across
        cgroup's subtree.



Organizing Processes and Threads
--------------------------------

Processes
~~~~~~~~~

Initially, only the root cgroup exists to which all processes belong.
A child cgroup can be created by creating a sub-directory::

  # mkdir $CGROUP_NAME

A given cgroup may have multiple child cgroups forming a tree
structure.  Each cgroup has a read-writable interface file
"cgroup.procs".  When read, it lists the PIDs of all processes which
belong to the cgroup one-per-line.  The PIDs are not ordered and the
same PID may show up more than once if the process got moved to
another cgroup and then back or the PID got recycled while reading.

A process can be migrated into a cgroup by writing its PID to the
target cgroup's "cgroup.procs" file.  Only one process can be migrated
on a single write(2) call.  If a process is composed of multiple
threads, writing the PID of any thread migrates all threads of the
process.

When a process forks a child process, the new process is born into the
cgroup that the forking process belongs to at the time of the
operation.  After exit, a process stays associated with the cgroup
that it belonged to at the time of exit until it's reaped; however, a
zombie process does not appear in "cgroup.procs" and thus can't be
moved to another cgroup.

A cgroup which doesn't have any children or live processes can be
destroyed by removing the directory.  Note that a cgroup which doesn't
have any children and is associated only with zombie processes is
considered empty and can be removed::

  # rmdir $CGROUP_NAME

"/proc/$PID/cgroup" lists a process's cgroup membership.  If legacy
cgroup is in use in the system, this file may contain multiple lines,
one for each hierarchy.  The entry for cgroup v2 is always in the
format "0::$PATH"::

  # cat /proc/842/cgroup
  ...
  0::/test-cgroup/test-cgroup-nested

If the process becomes a zombie and the cgroup it was associated with
is removed subsequently, " (deleted)" is appended to the path::

  # cat /proc/842/cgroup
  ...
  0::/test-cgroup/test-cgroup-nested (deleted)


Threads
~~~~~~~

cgroup v2 supports thread granularity for a subset of controllers to
support use cases requiring hierarchical resource distribution across
the threads of a group of processes.  By default, all threads of a
process belong to the same cgroup, which also serves as the resource
domain to host resource consumptions which are not specific to a
process or thread.  The thread mode allows threads to be spread across
a subtree while still maintaining the common resource domain for them.

Controllers which support thread mode are called threaded controllers.
The ones which don't are called domain controllers.

Marking a cgroup threaded makes it join the resource domain of its
parent as a threaded cgroup.  The parent may be another threaded
cgroup whose resource domain is further up in the hierarchy.  The
root of a threaded subtree, that is, the nearest ancestor which is not
threaded, is called threaded domain or thread root interchangeably and
serves as the resource domain for the entire subtree.

Inside a threaded subtree, threads of a process can be put in
different cgroups and are not subject to the no internal process
constraint - threaded controllers can be enabled on non-leaf cgroups
whether they have threads in them or not.

As the threaded domain cgroup hosts all the domain resource
consumptions of the subtree, it is considered to have internal
resource consumptions whether there are processes in it or not and
can't have populated child cgroups which aren't threaded.  Because the
root cgroup is not subject to no internal process constraint, it can
serve both as a threaded domain and a parent to domain cgroups.

The current operation mode or type of the cgroup is shown in the
"cgroup.type" file which indicates whether the cgroup is a normal
domain, a domain which is serving as the domain of a threaded subtree,
or a threaded cgroup.

On creation, a cgroup is always a domain cgroup and can be made
threaded by writing "threaded" to the "cgroup.type" file.  The
operation is single direction::

  # echo threaded > cgroup.type

Once threaded, the cgroup can't be made a domain again.  To enable
the thread mode, the following conditions must be met.

- As the cgroup will join the parent's resource domain.  The parent
  must either be a valid (threaded) domain or a threaded cgroup.

- When the parent is an unthreaded domain, it must not have any domain
  controllers enabled or populated domain children.  The root is
  exempt from this requirement.

Topology-wise, a cgroup can be in an invalid state.  Please consider
the following topology::

  A (threaded domain) - B (threaded) - C (domain, just created)

C is created as a domain but isn't connected to a parent which can
host child domains.  C can't be used until it is turned into a
threaded cgroup.  "cgroup.type" file will report "domain (invalid)" in
these cases.  Operations which fail due to invalid topology use
EOPNOTSUPP as the errno.

A domain cgroup is turned into a threaded domain when one of its child
cgroup becomes threaded or threaded controllers are enabled in the
"cgroup.subtree_control" file while there are processes in the cgroup.
A threaded domain reverts to a normal domain when the conditions
clear.

When read, "cgroup.threads" contains the list of the thread IDs of all
threads in the cgroup.  Except that the operations are per-thread
instead of per-process, "cgroup.threads" has the same format and
behaves the same way as "cgroup.procs".  While "cgroup.threads" can be
written to in any cgroup, as it can only move threads inside the same
threaded domain, its operations are confined inside each threaded
subtree.

The threaded domain cgroup serves as the resource domain for the whole
subtree, and, while the threads can be scattered across the subtree,
all the processes are considered to be in the threaded domain cgroup.
"cgroup.procs" in a threaded domain cgroup contains the PIDs of all
processes in the subtree and is not readable in the subtree proper.
However, "cgroup.procs" can be written to from anywhere in the subtree
to migrate all threads of the matching process to the cgroup.

Only threaded controllers can be enabled in a threaded subtree.  When
a threaded controller is enabled inside a threaded subtree, it only
accounts for and controls resource consumptions associated with the
threads in the cgroup and its descendants.  All consumptions which
aren't tied to a specific thread belong to the threaded domain cgroup.

Because a threaded subtree is exempt from no internal process
constraint, a threaded controller must be able to handle competition
between threads in a non-leaf cgroup and its child cgroups.  Each
threaded controller defines how such competitions are handled.

Currently, the following controllers are threaded and can be enabled
in a threaded cgroup::

- cpu
- cpuset
- perf_event
- pids

[Un]populated Notification
--------------------------

Each non-root cgroup has a "cgroup.events" file which contains
"populated" field indicating whether the cgroup's sub-hierarchy has
live processes in it.  Its value is 0 if there is no live process in
the cgroup and its descendants; otherwise, 1.  poll and [id]notify
events are triggered when the value changes.  This can be used, for
example, to start a clean-up operation after all processes of a given
sub-hierarchy have exited.  The populated state updates and
notifications are recursive.  Consider the following sub-hierarchy
where the numbers in the parentheses represent the numbers of processes
in each cgroup::

  A(4) - B(0) - C(1)
              \ D(0)

A, B and C's "populated" fields would be 1 while D's 0.  After the one
process in C exits, B and C's "populated" fields would flip to "0" and
file modified events will be generated on the "cgroup.events" files of
both cgroups.


Controlling Controllers
-----------------------

Enabling and Disabling
~~~~~~~~~~~~~~~~~~~~~~

Each cgroup has a "cgroup.controllers" file which lists all
controllers available for the cgroup to enable::

  # cat cgroup.controllers
  cpu io memory

No controller is enabled by default.  Controllers can be enabled and
disabled by writing to the "cgroup.subtree_control" file::

  # echo "+cpu +memory -io" > cgroup.subtree_control

Only controllers which are listed in "cgroup.controllers" can be
enabled.  When multiple operations are specified as above, either they
all succeed or fail.  If multiple operations on the same controller
are specified, the last one is effective.

Enabling a controller in a cgroup indicates that the distribution of
the target resource across its immediate children will be controlled.
Consider the following sub-hierarchy.  The enabled controllers are
listed in parentheses::

  A(cpu,memory) - B(memory) - C()
                            \ D()

As A has "cpu" and "memory" enabled, A will control the distribution
of CPU cycles and memory to its children, in this case, B.  As B has
"memory" enabled but not "CPU", C and D will compete freely on CPU
cycles but their division of memory available to B will be controlled.

As a controller regulates the distribution of the target resource to
the cgroup's children, enabling it creates the controller's interface
files in the child cgroups.  In the above example, enabling "cpu" on B
would create the "cpu." prefixed controller interface files in C and
D.  Likewise, disabling "memory" from B would remove the "memory."
prefixed controller interface files from C and D.  This means that the
controller interface files - anything which doesn't start with
"cgroup." are owned by the parent rather than the cgroup itself.


Top-down Constraint
~~~~~~~~~~~~~~~~~~~

Resources are distributed top-down and a cgroup can further distribute
a resource only if the resource has been distributed to it from the
parent.  This means that all non-root "cgroup.subtree_control" files
can only contain controllers which are enabled in the parent's
"cgroup.subtree_control" file.  A controller can be enabled only if
the parent has the controller enabled and a controller can't be
disabled if one or more children have it enabled.


No Internal Process Constraint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Non-root cgroups can distribute domain resources to their children
only when they don't have any processes of their own.  In other words,
only domain cgroups which don't contain any processes can have domain
controllers enabled in their "cgroup.subtree_control" files.

This guarantees that, when a domain controller is looking at the part
of the hierarchy which has it enabled, processes are always only on
the leaves.  This rules out situations where child cgroups compete
against internal processes of the parent.

The root cgroup is exempt from this restriction.  Root contains
processes and anonymous resource consumption which can't be associated
with any other cgroups and requires special treatment from most
controllers.  How resource consumption in the root cgroup is governed
is up to each controller (for more information on this topic please
refer to the Non-normative information section in the Controllers
chapter).

Note that the restriction doesn't get in the way if there is no
enabled controller in the cgroup's "cgroup.subtree_control".  This is
important as otherwise it wouldn't be possible to create children of a
populated cgroup.  To control resource distribution of a cgroup, the
cgroup must create children and transfer all its processes to the
children before enabling controllers in its "cgroup.subtree_control"
file.


Delegation
----------

Model of Delegation
~~~~~~~~~~~~~~~~~~~

A cgroup can be delegated in two ways.  First, to a less privileged
user by granting write access of the directory and its "cgroup.procs",
"cgroup.threads" and "cgroup.subtree_control" files to the user.
Second, if the "nsdelegate" mount option is set, automatically to a
cgroup namespace on namespace creation.

Because the resource control interface files in a given directory
control the distribution of the parent's resources, the delegatee
shouldn't be allowed to write to them.  For the first method, this is
achieved by not granting access to these files.  For the second, files
outside the namespace should be hidden from the delegatee by the means
of at least mount namespacing, and the kernel rejects writes to all
files on a namespace root from inside the cgroup namespace, except for
those files listed in "/sys/kernel/cgroup/delegate" (including
"cgroup.procs", "cgroup.threads", "cgroup.subtree_control", etc.).

The end results are equivalent for both delegation types.  Once
delegated, the user can build sub-hierarchy under the directory,
organize processes inside it as it sees fit and further distribute the
resources it received from the parent.  The limits and other settings
of all resource controllers are hierarchical and regardless of what
happens in the delegated sub-hierarchy, nothing can escape the
resource restrictions imposed by the parent.

Currently, cgroup doesn't impose any restrictions on the number of
cgroups in or nesting depth of a delegated sub-hierarchy; however,
this may be limited explicitly in the future.


Delegation Containment
~~~~~~~~~~~~~~~~~~~~~~

A delegated sub-hierarchy is contained in the sense that processes
can't be moved into or out of the sub-hierarchy by the delegatee.

For delegations to a less privileged user, this is achieved by
requiring the following conditions for a process with a non-root euid
to migrate a target process into a cgroup by writing its PID to the
"cgroup.procs" file.

- The writer must have write access to the "cgroup.procs" file.

- The writer must have write access to the "cgroup.procs" file of the
  common ancestor of the source and destination cgroups.

The above two constraints ensure that while a delegatee may migrate
processes around freely in the delegated sub-hierarchy it can't pull
in from or push out to outside the sub-hierarchy.

For an example, let's assume cgroups C0 and C1 have been delegated to
user U0 who created C00, C01 under C0 and C10 under C1 as follows and
all processes under C0 and C1 belong to U0::

  ~~~~~~~~~~~~~ - C0 - C00
  ~ cgroup    ~      \ C01
  ~ hierarchy ~
  ~~~~~~~~~~~~~ - C1 - C10

Let's also say U0 wants to write the PID of a process which is
currently in C10 into "C00/cgroup.procs".  U0 has write access to the
file; however, the common ancestor of the source cgroup C10 and the
destination cgroup C00 is above the points of delegation and U0 would
not have write access to its "cgroup.procs" files and thus the write
will be denied with -EACCES.

For delegations to namespaces, containment is achieved by requiring
that both the source and destination cgroups are reachable from the
namespace of the process which is attempting the migration.  If either
is not reachable, the migration is rejected with -ENOENT.


Guidelines
----------

Organize Once and Control
~~~~~~~~~~~~~~~~~~~~~~~~~

Migrating a process across cgroups is a relatively expensive operation
and stateful resources such as memory are not moved together with the
process.  This is an explicit design decision as there often exist
inherent trade-offs between migration and various hot paths in terms
of synchronization cost.

As such, migrating processes across cgroups frequently as a means to
apply different resource restrictions is discouraged.  A workload
should be assigned to a cgroup according to the system's logical and
resource structure once on start-up.  Dynamic adjustments to resource
distribution can be made by changing controller configuration through
the interface files.


Avoid Name Collisions
~~~~~~~~~~~~~~~~~~~~~

Interface files for a cgroup and its children cgroups occupy the same
directory and it is possible to create children cgroups which collide
with interface files.

All cgroup core interface files are prefixed with "cgroup." and each
controller's interface files are prefixed with the controller name and
a dot.  A controller's name is composed of lower case alphabets and
'_'s but never begins with an '_' so it can be used as the prefix
character for collision avoidance.  Also, interface file names won't
start or end with terms which are often used in categorizing workloads
such as job, service, slice, unit or workload.

cgroup doesn't do anything to prevent name collisions and it's the
user's responsibility to avoid them.
