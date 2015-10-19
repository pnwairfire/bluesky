#
# hysplit_utils.py
#
# Generic hysplit utility module created mostly for testability
#
# @todo: refactor this as a class

_bluesky_version_ = "3.5.1"

import math


__all__ = [
    'create_fire_sets', 'create_fire_tranches'
    ]

def create_fire_sets(filteredFires):
    """Creates sets of fires, grouping by location

    A single fire location may show up multiple times if it lasted multiple days,
    since there's one FireLocationData per location per day.  We don't want to
    split up any location into multiple tranches, so we'll group FireLocationData
    objects by location id and then tranche the location fire sets.

    @todo: make sure fire locations from any particular event don't get split up into
      multiple HYSPLIT runs ???  (use filteredFires[N]['metadata']['sf_event_guid']) ?
    """

    filtered_fires_dict = {e: [] for e in set([f.id for f in filteredFires])}
    for f in filteredFires:
        filtered_fires_dict[f.id].append(f)
    return  filtered_fires_dict.values()

def create_fire_tranches(filtered_fire_sets, num_processes, logger=None):
    """Creates tranches of FireLocationData, each tranche to be processed by its
    own HYSPLIT process.

    @todo: More sophisticated tranching (ex. taking into account acreage, location, etc.).
    """

    n_sets = len(filtered_fire_sets)
    num_processes = min(n_sets, num_processes)  # just to be sure
    min_n_fire_sets_per_process = n_sets / num_processes
    extra_fire_cutoff = n_sets % num_processes

    if logger:
        logger.info("Running %d HYSPLIT49 Dispersion model processes "
            "on %d fires (i.e. events)" % (num_processes, n_sets))
        logger.info(" - %d processes with %d fires" % (
            num_processes - extra_fire_cutoff, min_n_fire_sets_per_process))
        if extra_fire_cutoff > 0:
            logger.info(" - %d processes with %d fires" % (
                extra_fire_cutoff, min_n_fire_sets_per_process+1))

    idx = 0
    fire_tranches = []
    for nproc in xrange(num_processes):
        s = idx
        idx += min_n_fire_sets_per_process
        if nproc < extra_fire_cutoff:
            idx += 1
        fire_sets = filtered_fire_sets[s:idx]
        if logger:
            logger.debug("Process %d:  %d fire sets" % (nproc, len(fire_sets)))
        fires = reduce(lambda x,y: x + y, fire_sets)
        fire_tranches.append(fires)
    return fire_tranches

def compute_num_processes(num_fire_sets, **config):
    """Determines number of HYSPLIT tranches given the number of fires sets
    and various tranching related config variables.

    Args:
     - num_fire_sets -- number of sets of fires, each set represeting a fire over
       possibly multiple days

    Config options:
     - num_processes -- if specified and greater than 0, this value is returned
     - num_fires_per_process -- if num_processes isn't specified and this value
       is (and is greater than 0), then the num_processes is set to the min value
       such that not process has more than num_fires_per_process fires (unless
       num_processes_max, below, is specified)
     - num_processes_max -- max number of processes; only comes into play if
       num_processes isn't specified but num_fires_per_process is, and
       num_fires_per_process is greater than num_processes_max
    """
    if 1 <= config.get('num_processes', 0):
        num_processes = min(num_fire_sets, config['num_processes'])
    elif 1 <= config.get('num_fires_per_process', 0):
        num_processes = math.ceil(float(num_fire_sets) / config['num_fires_per_process'])
        if 1 <= config.get('num_processes_max', 0):
            num_processes = min(num_processes, config['num_processes_max'])
    else:
        num_processes = 1

    return int(num_processes)
