"""Project locking API"""

import time
from tooz import coordination
import uuid

from config import settings


LOCK_ENABLED = settings.TASKFLOW_LOCK_ENABLED
LOCK_RETRY_COUNT = settings.TASKFLOW_LOCK_RETRY_COUNT
LOCK_RETRY_INTERVAL = settings.TASKFLOW_LOCK_RETRY_INTERVAL
REDIS_URL = settings.TASKFLOW_REDIS_URL


def get_coordinator():
    """Return a Tooz coordinator object"""
    host_id = 'omics_taskflow_{}'.format(uuid.uuid4())

    coordinator = coordination.get_coordinator(
        backend_url=REDIS_URL,
        member_id=bytes(host_id, encoding='utf-8'),
        socket_keepalive=True)

    if coordinator:
        coordinator.start(start_heart=True)
        return coordinator

    return None


def acquire(
        lock,
        retry_count=LOCK_RETRY_COUNT,
        retry_interval=LOCK_RETRY_INTERVAL):
    """
    Acquire project lock
    :param lock: Tooz lock object
    :param retry_count: Times to retry if unsuccessful (int)
    :param retry_interval: Time in seconds to keep retrying (int)
    :returns: Boolean
    """
    if not LOCK_ENABLED:
        return True

    acquired = lock.acquire(blocking=False)

    if acquired:
        print_status(lock, unlock=False, failed=False)
        return True

    if retry_count > 0:
        for i in range(0, retry_count):
            acquired = lock.acquire(blocking=False)

            if acquired:
                print_status(lock, unlock=False, failed=False)
                return True

            time.sleep(retry_interval)

    print_status(lock, unlock=False, failed=True)
    raise LockAcquireException('Unable to acquire project lock')


def release(lock):
    """
    :param lock: Tooz lock object
    """
    if not LOCK_ENABLED:
        return True

    released = lock.release()

    if released:
        print_status(lock, unlock=True, failed=False)
        return True

    print_status(lock, unlock=True, failed=True)
    return False


class LockAcquireException(Exception):
    """Project lock acquiring exception"""


def print_status(lock, unlock=False, failed=False):
    print('{} {}: {}'.format(
        'Unlock' if unlock else 'Lock',
        'FAILED' if failed else 'OK',
        str(lock.name).split('\'')[3]))
