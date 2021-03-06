import logging
from taskflow import engines
from taskflow.patterns import linear_flow as lf

from tasks.base_task import ForceFailException


logger = logging.getLogger('sodar_taskflow')


class BaseLinearFlow:
    """Base class for linear flows used for task queues"""

    def __init__(
        self,
        irods,
        sodar_api,
        project_uuid,
        flow_name,
        flow_data,
        targets,
        timeline_uuid=None,
        request_mode='sync',
    ):
        self.irods = irods
        self.sodar_api = sodar_api  # TODO: Dynamic support for more APIs?
        self.project_uuid = project_uuid
        self.flow_name = flow_name
        self.flow_data = flow_data
        self.targets = targets
        self.required_fields = []  # For validation
        self.timeline_uuid = timeline_uuid
        self.request_mode = request_mode
        self.supported_modes = [
            'sync',
            # 'async'                   # Support only sync by default
        ]
        self.require_lock = True  # Always require project lock by default
        self.flow = lf.Flow(flow_name)

    def validate(self):
        """
        Function for validating flow parameters. Returns True/False based on
        validation success. Add required kwargs in the flow implementation and
        call this. Can be extended with further validation.
        """
        if self.request_mode not in self.supported_modes:
            raise TypeError(
                'Request mode "{}" not supported'.format(self.request_mode)
            )
        for k in self.required_fields:
            if k not in self.flow_data or self.flow_data[k] == '':
                raise TypeError('Missing or invalid argument: "{}"'.format(k))
        return True

    def add_task(self, task):
        """Add task into the flow, if in current targets."""
        if task.target in self.targets:
            self.flow.add(task)

    def build(self, force_fail=False):
        """
        Build linear flow to be executed for one project. Override this in
        the flow implementation.
        """
        # TODO: Add tasks to self.flow here with self.flow.add()
        # TODO: Add force_fail=force_fail to last add() for testing rollback
        msg = 'Function build() not implemented!'
        logger.error(msg)
        raise NotImplementedError(msg)

    def run(self, verbose=True):
        """
        Run the flow. Returns True or False depending on success. If False,
        the flow was rolled back. Also handle project locking and unlocking.
        """
        if verbose:
            logger.info('--- Running flow "{}" ---'.format(self.flow.name))
        engine = engines.load(self.flow, engine='serial')
        try:
            engine.run()
        except ForceFailException:
            return False
        except Exception as ex:
            logger.error('Exception: {}'.format(ex))
            raise ex
        result = (
            True
            if (
                engine.statistics['incomplete'] == 0
                and engine.statistics['discarded_failures'] == 0
            )
            else False
        )
        if verbose:
            logger.info(
                '--- Flow finished: {} ({} completed, {} incomplete, '
                '{} discarded) ---'.format(
                    'OK' if result is True else 'ROLLBACK',
                    engine.statistics['completed'],
                    engine.statistics['incomplete'],
                    engine.statistics['discarded_failures'],
                )
            )
        return result
