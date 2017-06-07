from flask import Flask, request, Response
import os

from apis import irods_utils, lock_api, omics_api
from config import settings
import flows


IRODS_URL = settings.TASKFLOW_IRODS_HOST
IRODS_PORT = settings.TASKFLOW_IRODS_PORT
IRODS_ZONE = settings.TASKFLOW_IRODS_ZONE
IRODS_USER = settings.TASKFLOW_IRODS_USER
IRODS_PASS = settings.TASKFLOW_IRODS_PASS

app = Flask(__name__)
app.config.from_envvar('OMICS_TASKFLOW_SETTINGS')


@app.route('/submit', methods=['POST'])
def submit():
    ###################
    # Validate request
    ###################

    form_data = request.json
    # print('SUBMIT DATA: {}'.format(form_data))
    force_fail = form_data['force_fail'] \
        if 'force_fail' in form_data else False

    required_keys = [
        'project_pk',
        'request_mode',
        'flow_name',
        'targets']

    for k in required_keys:
        if k not in form_data or form_data[k] == '':
            return Response(
                'Missing or invalid argument: "{}"'.format(k),
                status=400)  # Bad request

    # We don't support async yet
    if form_data['request_mode'] == 'async':
        return Response('Async mode not supported yet', status=501)

    # Make sure we can support the named flow
    flow_cls = flows.get_flow(form_data['flow_name'])

    if not flow_cls:
        return Response('Flow not supported', status=501)  # Not implemented

    project_pk = form_data['project_pk']

    ##############
    # Set Up lock
    ##############

    # Get project lock or return failure if we can't
    coordinator = lock_api.get_coordinator()

    if not coordinator:
        return Response('Error retrieving lock coordinator', 500)

    # TODO: TBD: Lock title
    lock_id = 'project{}'.format(project_pk)
    lock = coordinator.get_lock(bytes(lock_id, encoding='utf-8'))

    try:
        lock_api.acquire(lock)

    except Exception as ex:
        return Response(str(ex), status=500)

    # Release lock, stop coordinator and return
    def return_after_lock(response_body, status):
        lock_api.release(lock)
        coordinator.stop()
        return Response(str(response_body), status)

    #############
    # Init iRODS
    #############

    try:
        irods = irods_utils.init_irods()

    except Exception as ex:
        return return_after_lock(
            'Error initializing iRODS: {}'.format(ex), 500)

    ################
    # Init Omics API
    ################

    if 'omics_url' in form_data:
        omics_url = form_data['omics_url']

    else:
        omics_url = settings.TASKFLOW_OMICS_URL

    ######################
    # Create and run flow
    ######################

    flow = flow_cls(
        irods=irods,
        omics_api=omics_api.OmicsAPI(omics_url),
        project_pk=form_data['project_pk'],
        flow_name=form_data['flow_name'],
        flow_data=form_data['flow_data'],
        targets=form_data['targets'])

    try:
        flow.validate()

    except TypeError as ex:
        return return_after_lock(
            'Error validating flow: {}'.format(ex), 400)

    try:
        flow.build(force_fail)

    except Exception as ex:
        return return_after_lock(
            'Error building flow: {}'.format(ex), 500)

    # TODO: If async, send OK response, store handle, run flow in Process

    try:
        flow_result = flow.run()

    except Exception as ex:
        return return_after_lock(
            'Error running flow: {}'.format(ex), 500)

    return return_after_lock(
        flow_result, 200)


@app.route('/cleanup', methods=['GET'])
def cleanup():
    try:
        print('--- Cleanup started ---')
        irods = irods_utils.init_irods()
        irods_utils.cleanup_irods(irods)
        print('--- Cleanup done ---')

    except Exception as ex:
        return Response('Error during cleanup: {}'.format(ex), status=500)

    return Response('OK', status=200)


# DEBUG
@app.route('/hello', methods=['GET'])
def hello():
    return Response('Hello world from omics_taskflow!', status=200)


if __name__ == '__main__':
    print('settings={}'.format(os.getenv('OMICS_TASKFLOW_SETTINGS')))
    app.run(
        use_reloader=False)


def validate_kwargs(kwargs_dict, required_keys):
    """Base validation function for kwargs"""
    # TODO: Could also do e.g. proper json schema validation
    for k in required_keys:
        if k not in kwargs_dict or kwargs_dict[k] == '':
            raise TypeError('Missing or invalid argument: "{}"'.format(k))
