from taskflow import engines
from taskflow.patterns import linear_flow as lf


class BaseLinearFlow:
    """Base class for linear flows used for task queues"""
    def __init__(
            self, irods, omics_api, project_pk, flow_name, flow_data, targets):
        self.irods = irods
        self.omics_api = omics_api      # TODO: Dynamic support for more APIs?
        self.project_pk = project_pk
        self.flow_name = flow_name
        self.flow_data = flow_data
        self.targets = targets
        self.required_fields = []   # For validation
        self.flow = lf.Flow(flow_name)

    def validate(self):
        """Function for validating flow parameters. Returns True/False based on
        validation success. Add required kwargs in the flow implementation and
        call this. Can be extended with further validation."""
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
        the flow was rolled back."""
        if verbose:
            print('--- Running flow "{}" ---'.format(
                self.flow.name))

        engine = engines.load(self.flow, engine='serial')
        ex_str = 'Unknown exception'

        try:
            engine.run()

        except Exception as ex:
            ex_str = str(ex)

            if verbose:
                print('Exception: {}'.format(ex))

            return str(ex)

        result = True if (
            engine.statistics['incomplete'] == 0 and
            engine.statistics['discarded_failures'] == 0) else ex_str

        if verbose:
            print('--- Flow finished: {} ({} completed, {} incomplete, '
                  '{} discarded) ---'.format(
                    'OK' if result is True else 'ROLLBACK',
                    engine.statistics['completed'],
                    engine.statistics['incomplete'],
                    engine.statistics['discarded_failures']))

        return result
