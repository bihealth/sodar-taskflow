from flask import Flask, request, Response
import logging
from logging.handlers import RotatingFileHandler
from multiprocessing import Process
import os
import sys

from apis import irods_utils, lock_api, omics_api
from config import settings
import flows


app = Flask('omics_taskflow')
app.config.from_envvar('OMICS_TASKFLOW_SETTINGS')

# Set up logging
app.logger.handlers = []
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s')

# Stdout handler
out_handler = logging.StreamHandler(stream=sys.stdout)
out_handler.setFormatter(formatter)
out_handler.setLevel(logging.getLevelName('DEBUG'))
app.logger.addHandler(out_handler)

# File handler
if settings.TASKFLOW_LOG_TO_FILE:
    file_handler = RotatingFileHandler(settings.TASKFLOW_LOG_PATH)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.getLevelName('INFO'))
    app.logger.addHandler(file_handler)

app.logger.setLevel(logging.getLevelName(settings.TASKFLOW_LOG_LEVEL))


@app.route('/submit', methods=['POST'])
def submit():
    ###################
    # Validate request
    ###################

    form_data = request.json
    app.logger.debug('Submit data: {}'.format(form_data))
    force_fail = form_data['force_fail'] \
        if 'force_fail' in form_data else False

    required_keys = [
        'project_uuid',
        'request_mode',
        'flow_name',
        'targets']

    for k in required_keys:
        if k not in form_data or form_data[k] == '':
            msg = 'Missing or invalid argument: "{}"'.format(k)
            app.logger.error(msg)
            return Response(msg, status=400)  # Bad request

    # Make sure we can support the named flow
    flow_cls = flows.get_flow(form_data['flow_name'])

    if not flow_cls:
        msg = 'Flow "{}" not supported'.format(form_data['flow_name'])
        app.logger.error(msg)
        return Response(msg, status=501)  # Not implemented

    #############
    # Init iRODS
    #############

    try:
        irods = irods_utils.init_irods()

    except Exception as ex:
        msg = 'Error initializing iRODS: {}'.format(ex)
        app.logger.error(msg)
        return Response(msg, status=500)

    ################
    # Init Omics API
    ################

    if 'omics_url' in form_data:
        omics_url = form_data['omics_url']

    else:
        omics_url = settings.TASKFLOW_OMICS_URL

    omics_tf = omics_api.OmicsAPI(omics_url)

    ##############
    # Create flow
    ##############

    flow = flow_cls(
        irods=irods,
        omics_api=omics_tf,
        project_uuid=form_data['project_uuid'],
        flow_name=form_data['flow_name'],
        flow_data=form_data['flow_data'],
        targets=form_data['targets'],
        request_mode=form_data['request_mode'],
        timeline_uuid=form_data['timeline_uuid'])

    try:
        flow.validate()

    except TypeError as ex:
        msg = 'Error validating flow: {}'.format(ex)
        app.logger.error(msg)
        irods_utils.close_irods(irods)
        return Response(msg, status=400)

    project_uuid = form_data['project_uuid']
    coordinator = None
    lock = None

    #####################
    # Build and run flow
    #####################

    def run_flow(
            flow, project_uuid, timeline_uuid, omics_api, force_fail,
            async=True):
        coordinator = None
        lock = None

        # Acquire lock if needed
        if flow.require_lock:
            # Acquire lock
            coordinator = lock_api.get_coordinator()

            if not coordinator:
                ex_str = 'Error retrieving lock coordinator'

            else:
                lock_id = project_uuid
                lock = coordinator.get_lock(bytes(lock_id, encoding='utf-8'))

                try:
                    lock_api.acquire(lock)

                except Exception as ex:
                    msg = 'Unable to acquire project lock'
                    app.logger.info(msg + ': ' + str(ex))
                    irods_utils.close_irods(irods)
                    return Response(msg, status=503)

        else:
            app.logger.info('Lock not required (flow.require_lock=False)')

        flow_result = None
        ex_str = None
        response = None

        # Build flow
        app.logger.info('--- Building flow "{}" ---'.format(flow.flow_name))

        try:
            flow.build(force_fail)

        except Exception as ex:
            msg = 'Error building flow'

            # TODO: HACK! generalize to report building problems in ODM!
            if async and 'zone_uuid' in flow.flow_data:
                # Set zone status in the Django site
                set_data = {
                    'zone_uuid': flow.flow_data['zone_uuid'],
                    'status': 'NOT CREATED' if
                    flow.flow_name == 'landing_zone_create' else 'FAILED',
                    'status_info': '{}: {}'.format(msg, ex)}
                omics_api.send_request(
                    'landingzones/taskflow/status/set', set_data)

                # Set timeline status
                omics_api.set_timeline_status(
                    event_uuid=timeline_uuid,
                    status_type='FAILED',
                    status_desc=msg)

                app.logger.error('{}: {}'.format(msg, ex))

            else:
                response = Response(
                    '{}: {}'.format(msg, ex), status=500)

        app.logger.info('--- Building flow OK ---')

        # Run flow
        if not ex_str:
            try:
                flow_result = flow.run()

            except Exception as ex:
                ex_str = str(ex)

        # Flow completion
        if flow_result:
            if async:
                omics_api.set_timeline_status(
                    event_uuid=timeline_uuid,
                    status_type='OK',
                    status_desc='Async submit OK')

            else:
                response = Response(str(flow_result), status=200)

        # Exception/failure
        else:
            if async:
                omics_api.set_timeline_status(
                    event_uuid=timeline_uuid,
                    status_type='FAILED',
                    status_desc='Error running async flow: ' +
                                (ex_str if ex_str else 'unknown error'))

            else:
                msg = 'Error running flow: ' + (ex_str if ex_str != ''
                    else 'unknown error')
                app.logger.error(msg)
                response = Response(msg, status=500)

        # Release lock if acquired
        if flow.require_lock and lock:
            lock_api.release(lock)
            coordinator.stop()

        irods_utils.close_irods(irods)
        return response

    # Run asynchronously
    if form_data['request_mode'] == 'async':
        p = Process(
            target=run_flow,
            args=(
                flow, project_uuid, form_data['timeline_uuid'], omics_tf,
                force_fail, True))
        p.start()
        return Response(str(True), status=200)

    # Run synchronously
    else:
        return run_flow(
            flow, project_uuid, form_data['timeline_uuid'], omics_tf,
            force_fail, False)


@app.route('/cleanup', methods=['GET'])
def cleanup():
    if settings.TASKFLOW_ALLOW_IRODS_CLEANUP:
        try:
            app.logger.info('--- Cleanup started ---')
            irods = irods_utils.init_irods()
            irods_utils.cleanup_irods(irods)
            app.logger.info('--- Cleanup done ---')
            irods_utils.close_irods(irods)

        except Exception as ex:
            return Response('Error during cleanup: {}'.format(ex), status=500)

        return Response('OK', status=200)

    return Response('iRODS cleanup not allowed', status=403)


# DEBUG
@app.route('/hello', methods=['GET'])
def hello():
    app.logger.debug('Hello world request received')
    return Response('Hello world from omics_taskflow!', status=200)


if __name__ == '__main__':
    app.logger.info('settings={}'.format(os.getenv('OMICS_TASKFLOW_SETTINGS')))
    app_kwargs = {'processes': 4} if settings.DEBUG else {}
    app.run('0.0.0.0', 5005, **app_kwargs)


def validate_kwargs(kwargs_dict, required_keys):
    """Base validation function for kwargs"""
    # TODO: Could also do e.g. proper json schema validation
    for k in required_keys:
        if k not in kwargs_dict or kwargs_dict[k] == '':
            raise TypeError('Missing or invalid argument: "{}"'.format(k))
