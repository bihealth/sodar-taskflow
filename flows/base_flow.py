from apis import lock_api
from taskflow import engines
from taskflow.patterns import linear_flow as lf

from tasks.base_task import ForceFailException

from config import settings


class BaseLinearFlow:
    """Base class for linear flows used for task queues"""
    def __init__(
            self, irods, omics_api, project_pk, flow_name, flow_data, targets,
            timeline_pk=None, request_mode='sync'):
        self.irods = irods
        self.omics_api = omics_api      # TODO: Dynamic support for more APIs?
        self.project_pk = project_pk
        self.flow_name = flow_name
        self.flow_data = flow_data
        self.targets = targets
        self.required_fields = []       # For validation
        self.timeline_pk = timeline_pk
        self.request_mode = request_mode
        self.supported_modes = [
            'sync',
            # 'async'                   # Support only sync by default
        ]
        self.flow = lf.Flow(flow_name)

    def validate(self):
        """Function for validating flow parameters. Returns True/False based on
        validation success. Add required kwargs in the flow implementation and
        call this. Can be extended with further validation."""
        if self.request_mode not in self.supported_modes:
            raise TypeError('Request mode "{}" not supported'.format(
                self.request_mode))

        for k in self.required_fields:
            if k not in self.flow_data or self.flow_data[k] == '':
                raise TypeError('Missing or invalid argument: "{}"'.format(k))
        return True

    def add_task(self, task):
        """Add task into the flow, if in current targets."""
        if task.target in self.targets:
            self.flow.add(task)

    def build(self, force_fail=False):
        """Build linear flow to be executed for one project. Override this in
        the flow implementation."""
        # TODO: Add tasks to self.flow here with self.flow.add()
        # TODO: Add force_fail=force_fail to last add() for testing rollback
        raise NotImplementedError('Function build() not implemented!')

    def run(self, verbose=True):
        """Run the flow. Returns True or False depending on success. If False,
        the flow was rolled back. Also handle project locking and unlocking."""

        if verbose:
            print('--- Running flow "{}" ---'.format(
                self.flow.name))

        engine = engines.load(self.flow, engine='serial')

        try:
            engine.run()

        except ForceFailException:
            return False

        except Exception as ex:
            if verbose:
                print('Exception: {}'.format(ex))

            raise ex

        result = True if (
            engine.statistics['incomplete'] == 0 and
            engine.statistics['discarded_failures'] == 0) else False

        if verbose:
            print(
                '--- Flow finished: {} ({} completed, {} incomplete, '
                '{} discarded) ---'.format(
                    'OK' if result is True else 'ROLLBACK',
                    engine.statistics['completed'],
                    engine.statistics['incomplete'],
                    engine.statistics['discarded_failures']))

        return result
