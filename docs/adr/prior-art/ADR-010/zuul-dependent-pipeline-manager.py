# Copyright 2024 Acme Gating, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from zuul import model
from zuul.lib.logutil import get_annotated_logger
from zuul.manager.shared import SharedQueuePipelineManager


class DependentPipelineManager(SharedQueuePipelineManager):
    """PipelineManager for handling interrelated Changes.

    The DependentPipelineManager puts Changes that share a Pipeline
    into a shared :py:class:`~zuul.model.ChangeQueue`. It then processes them
    using the Optimistic Branch Prediction logic with Nearest Non-Failing Item
    reparenting algorithm for handling errors.
    """
    changes_merge = True
    type = 'dependent'

    def __init__(self, *args, **kwargs):
        super(DependentPipelineManager, self).__init__(*args, **kwargs)

    def constructChangeQueue(self, queue_name):
        p = self.pipeline
        return model.ChangeQueue.new(
            self.current_context,
            manager=self,
            window=p.window,
            window_floor=p.window_floor,
            window_ceiling=p.window_ceiling,
            window_increase_type=p.window_increase_type,
            window_increase_factor=p.window_increase_factor,
            window_decrease_type=p.window_decrease_type,
            window_decrease_factor=p.window_decrease_factor,
            name=queue_name)

    def getNodePriority(self, item, change):
        return item.queue.queue.index(item)

    def areChangesReadyToBeEnqueued(self, changes, event,
                                    warnings=None, debug=False):
        log = get_annotated_logger(self.log, event)
        for change in changes:
            source = change.project.source
            can_merge = source.canMerge(change, self.getSubmitAllowNeeds(),
                                        event=event)
            if not can_merge:
                msg = (
                    f"Change {change._id()} "
                    f"in project {change.project} "
                    "can not be merged"
                )
                if isinstance(can_merge, model.FalseWithReason):
                    msg += f" due to: {can_merge}"
                log.debug("  " + msg)
                if debug and warnings is not None:
                    warnings.append(msg)
                return False
        return True

    def getNonMergeableCycleChanges(self, item):
        """Return changes in the cycle that do not fulfill
        the pipeline's ready criteria."""
        changes = []
        for change in item.changes:
            source = change.project.source
            if not source.canMerge(
                change,
                self.getSubmitAllowNeeds(),
                event=item.event,
                allow_refresh=True,
            ):
                log = get_annotated_logger(self.log, item.event)
                log.debug("Change %s can no longer be merged", change)
                changes.append(change)
        return changes

    def enqueueChangesBehind(self, change, event, quiet, ignore_requirements,
                             change_queue, history=None,
                             dependency_graph=None):
        log = get_annotated_logger(self.log, event)
        history = history if history is not None else []

        log.debug("Checking for changes needing %s:" % change)
        if not isinstance(change, model.Change):
            log.debug("  %s does not support dependencies" % type(change))
            return

        # for project in change_queue, project.source get changes, then dedup.
        projects = [self.tenant.getProject(pcn)[1] for pcn, _ in
                    change_queue.project_branches]
        sources = {p.source for p in projects}

        needed_by_changes = self.resolveChangeReferences(
            change.getNeededByChanges())
        log.debug("  Previously known following changes: %s",
                  needed_by_changes)
        seen = set(needed_by_changes)
        for source in sources:
            log.debug("  Checking source: %s", source)
            relevant_projects = [p for p in projects if p.source == source]
            for c in source.getChangesDependingOn(change,
                                                  relevant_projects,
                                                  self.tenant):
                if c not in seen:
                    seen.add(c)
                    needed_by_changes.append(c)

        log.debug("  Updated following changes: %s", needed_by_changes)

        to_enqueue = []
        change_dependencies = dependency_graph.get(change, [])
        for other_change in needed_by_changes:
            if other_change in change_dependencies:
                # Only consider the change if it is not part of a cycle, as
                # cycle changes will otherwise be partially enqueued without
                # any error handling
                self.log.debug(
                    "    Skipping change %s due to dependency cycle",
                    other_change
                )
                continue

            with self.getChangeQueue(other_change,
                                     event) as other_change_queue:
                if other_change_queue != change_queue:
                    log.debug("  Change %s in project %s can not be "
                              "enqueued in the target queue %s" %
                              (other_change, other_change.project,
                               change_queue))
                    continue
            source = other_change.project.source
            if source.canMerge(other_change, self.getSubmitAllowNeeds(),
                               event=event):
                log.debug("  Change %s needs %s and is ready to merge",
                          other_change, change)
                to_enqueue.append(other_change)

        if not to_enqueue:
            log.debug("  No changes need %s" % change)

        for other_change in to_enqueue:
            self.addChange(other_change, event, quiet=quiet,
                           ignore_requirements=ignore_requirements,
                           change_queue=change_queue, history=history,
                           dependency_graph=dependency_graph)

    def enqueueChangesAhead(self, changes, event, quiet, ignore_requirements,
                            change_queue, history=None, dependency_graph=None,
                            warnings=None, debug=False):
        log = get_annotated_logger(self.log, event)

        history = history if history is not None else []
        for change in changes:
            if hasattr(change, 'number'):
                history.append(change)
            else:
                # Don't enqueue dependencies ahead of a non-change ref.
                return True

        abort, needed_changes = self.getMissingNeededChanges(
            changes, change_queue, event,
            dependency_graph=dependency_graph,
            warnings=warnings, debug=debug)
        if abort:
            return False

        if not needed_changes:
            return True
        log.debug("  Changes %s must be merged ahead of %s",
                  needed_changes, change)
        for needed_change in needed_changes:
            # If the change is already in the history, but the change also has
            # a git level dependency, we need to enqueue it before the current
            # change.
            if (needed_change not in history or
                    needed_change.cache_key in change.git_needs_changes):
                r = self.addChange(needed_change, event, quiet=quiet,
                                   ignore_requirements=ignore_requirements,
                                   change_queue=change_queue, history=history,
                                   dependency_graph=dependency_graph,
                                   warnings=warnings, debug=debug)
                if not r:
                    return False
        return True

    def getMissingNeededChanges(self, changes, change_queue, event,
                                dependency_graph=None, warnings=None,
                                item=None, debug=False):
        log = get_annotated_logger(self.log, event)
        changes_needed = []
        abort = False

        # Return true if okay to proceed enqueing this change,
        # false if the change should not be enqueued.
        for change in changes:
            log.debug("Checking for changes needed by %s:" % change)
            if not isinstance(change, model.Change):
                log.debug("  %s does not support dependencies", type(change))
                continue
            needed_changes = dependency_graph.get(change)
            if not needed_changes:
                log.debug("  No changes needed")
                continue
            # Ignore supplied change_queue
            with self.getChangeQueue(change, event) as change_queue:
                for needed_change in needed_changes:
                    log.debug("  Change %s needs change %s:" % (
                        change, needed_change))
                    if needed_change.is_merged:
                        log.debug("  Needed change is merged")
                        continue
                    with self.getChangeQueue(needed_change,
                                             event) as needed_change_queue:
                        if needed_change_queue != change_queue:
                            msg = ("Change %s in project %s does not "
                                   "share a change queue with %s "
                                   "in project %s" %
                                   (needed_change._id(),
                                    needed_change.project,
                                    change.number,
                                    change.project))
                            log.debug("  " + msg)
                            if warnings is not None:
                                warnings.append(msg)
                            changes_needed.append(needed_change)
                            abort = True
                    if not needed_change.is_current_patchset:
                        msg = (
                            f"Needed change {needed_change._id()} "
                            f"in project {needed_change.project} is not "
                            "the current patchset"
                        )
                        log.debug("  " + msg)
                        changes_needed.append(needed_change)
                        if debug and warnings is not None:
                            warnings.append(msg)
                        abort = True
                    if needed_change in changes:
                        log.debug("  Needed change is in cycle")
                        continue
                    if self.isChangeAlreadyInQueue(
                            needed_change, change_queue, event, item):
                        log.debug("  Needed change is already "
                                  "ahead in the queue")
                        continue
                    can_merge = needed_change.project.source.canMerge(
                        needed_change, self.getSubmitAllowNeeds(),
                        event=event)
                    if can_merge:
                        msg = (
                            f"Change {needed_change._id()} "
                            f"in project {needed_change.project} is needed "
                        )
                        log.debug("  " + msg)
                        if needed_change not in changes_needed:
                            changes_needed.append(needed_change)
                        continue
                    else:
                        # The needed change can't be merged.
                        msg = (
                            f"Change {needed_change._id()} "
                            f"in project {needed_change.project} is needed "
                            "but can not be merged"
                        )
                        if isinstance(can_merge, model.FalseWithReason):
                            msg += f" due to: {can_merge}"
                        log.debug("  " + msg)
                        if debug and warnings is not None:
                            warnings.append(msg)
                        changes_needed.append(needed_change)
                        abort = True
        return abort, changes_needed

    def getFailingDependentItems(self, item):
        failing_items = set()
        for change in item.changes:
            if not isinstance(change, model.Change):
                continue
            needs_changes = change.getNeedsChanges(
                self.useDependenciesByTopic(change.project))
            if not needs_changes:
                continue
            for needed_change in self.resolveChangeReferences(needs_changes):
                needed_item = self.getItemForChange(needed_change)
                if not needed_item:
                    continue
                if needed_item is item:
                    continue
                if needed_item.current_build_set.failing_reasons:
                    failing_items.add(needed_item)
        return failing_items

    def dequeueItem(self, item, quiet=False):
        super(DependentPipelineManager, self).dequeueItem(item, quiet)
        # If this was a dynamic queue from a speculative change,
        # remove the queue (if empty)
        if item.queue.dynamic:
            if not item.queue.queue:
                self.state.removeQueue(item.queue)
