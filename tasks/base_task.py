from taskflow import task

from config import settings

class BaseTask(task.Task):
    """Common base task"""
    def __init__(
            self, name, force_fail=False, verbose=True, inject=None, *args,
            **kwargs):
        super(BaseTask, self).__init__(name, inject=inject)
        self.name = name
        self.target = None  # TODO: Set this when inheriting task
        self.force_fail = force_fail
        self.verbose = verbose
        self.data_modified = False
        self.initial_data = {}   # TODO: Better way to do this?

    def execute(self, *args, **kwargs):
        # Raise Exception for testing revert()
        # NOTE: This doesn't work if done in pre_execute() or post_execute()
        # TODO: Is there a built-in way in taskflow for doing this?
        if self.force_fail:
            raise Exception(settings.TASKFLOW_FORCE_FAIL_STRING)

    def post_execute(self, *args, **kwargs):
        if self.verbose:
            print('{}: {}'.format(
                'force_fail' if self.force_fail else 'Executed',
                self.name))  # DEBUG

    def post_revert(self, *args, **kwargs):
        if self.verbose:
            print('Reverted: {}'.format(self.name))  # DEBUG
