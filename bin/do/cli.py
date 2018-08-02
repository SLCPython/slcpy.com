#! /usr/bin/env python -u
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from distutils import spawn  # spawn.find_executable is used
from itertools import chain
try:
    # python 2
    from future_builtins import filter
except ImportError:
    # python 3
    pass


import logging
import os
import re
import subprocess
import sys

import click

logger = logging.getLogger(__name__)

# Define a default machine name global. First use DO_MACHINE_NAME, then
# DOCKER_MACHINE_NAME (defined by eval $(docker-machine env ...)), finally
# default to 'eventboard'.
DEFAULT_MACHINE_NAME = os.environ.get('DO_MACHINE_NAME')
if not DEFAULT_MACHINE_NAME:
    DEFAULT_MACHINE_NAME = os.environ.get('DOCKER_MACHINE_NAME', 'eventboard')

# use to allow -h for for help
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def get_container_id(name):
    logger.debug('get_container_id for {}'.format(name))

    name_id = _run_command('docker-compose ps -q {}'.format(name))
    logger.debug('get_container_id found {}'.format(name_id))

    name_id = name_id.strip()

    if '\n' in name_id:
        name_id = name_id.split('\n')[-1]

    return name_id.strip()


def docker_env_prefix(machine_name=DEFAULT_MACHINE_NAME):
    """
    Make a shell environment prefix with the information needed to manage the
    vm. This

    Args:
        machine_name (str): name of the machine. Default: default

    Returns:
        dict: A prefix line for a bash command
    """
    if os.environ.get('DOCKER_MACHINE_NAME'):
        return None

    env_stuff = _run_command(
        'docker-machine env {}'.format(machine_name),
        use_docker_env=False)
    logger.debug(env_stuff)

    env = os.environ
    for line in env_stuff.split('\n'):
        if not line.startswith('export'):
            continue

        line = line.replace('export', '').replace('"', '').strip()
        var, value = line.split('=')
        env[var] = value

    return env


def set_logging(ctx, param, level):
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise click.BadParameter('Invalid log level: {}'.format(level))

    logging.basicConfig(level=numeric_level)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    '--log',
    default='WARNING', help='Set the log level',
    expose_value=False,
    callback=set_logging,
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']))
@click.version_option('1.0.0')
@click.pass_context
def cli(ctx):
    pass


@cli.command()
def reload():
    """Restart all containers"""
    _run_command('docker-compose stop')
    _run_command('docker-compose up -d')


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('ARGS', nargs=-1, type=click.UNPROCESSED)
def migrate(args):
    """Migrate the Django app"""
    web_id = get_container_id('web')

    _run_command(
        'docker exec -it {} python manage.py migrate --noinput {}'.format(
            web_id, ' '.join(args)),
        interactive=True,
        unbuffered_print=True)


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('ARGS', nargs=-1, type=click.UNPROCESSED)
def makemigrate(args):
    """Make Django migrations"""

    web_id = get_container_id('web')

    _run_command(
        'docker exec -it {} python manage.py makemigrations --noinput '
        '{}'.format(web_id, ' '.join(args)),
        unbuffered_print=True)


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('ARGS', nargs=-1, type=click.UNPROCESSED)
def manage(args):
    """Run a Django manage command on the web container"""
    web_id = get_container_id('web')

    _run_command(
        'docker exec -it {} python manage.py {}'.format(
            web_id, ' '.join(args)),
        unbuffered_print=True)


@cli.command()
def initial_data():
    """Update the initial sql data"""
    # start with a fresh db image
    _run_command('docker-compose stop')
    _run_command('docker-compose rm -f db')
    _run_command('docker-compose build db')
    _run_command('docker-compose up -d')

    # migrate the fresh image
    _run_command('docker-compose run web python manage.py migrate')

    # now dump the data
    db_id = get_container_id('db')

    initial_sql = _run_command(
        'docker exec -it {} pg_dump -U eb'.format(db_id),
        unbuffered_print=True,
        interactive=True)

    with open('db/initial_eb.psql', 'w') as f:
        f.write(initial_sql)


@cli.command()
def schema_dump():
    """Dump the db database with pg_dump"""
    db_id = get_container_id('db')
    _run_command(
        'docker exec -it {} pg_dump -U eb -s eb > db_schema.sql'.format(db_id),
        unbuffered_print=False,
        interactive=False
    )

    needle = r"CREATE TABLE ([a-z_]* \([^;]*\);)|COMMENT ON TABLE ([a-z_]* IS '[a-z, ]*';)"  # noqa

    with open('db_schema.sql') as f:
        schema_sql = f.read()
        schema_results = re.findall(needle, schema_sql, re.M | re.I)

    _run_command('> db_schema.sql')
    click.echo('\n\n'.join(filter(None, chain.from_iterable(schema_results))))


@cli.command()
def build_api_docs():
    """Build api.yaml from docs/api-swagger/"""
    _build_api_docs()


def _build_api_docs():
    web_id = get_container_id('web')

    _run_command(
        'docker exec -it {} /vagrant/scripts/do/build_api_docs.sh'.format(
            web_id),
        interactive=True)


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('ARGS', nargs=-1, type=click.UNPROCESSED)
def test(args):
    """Run tests"""
    if not os.path.exists('api.yaml'):
        _build_api_docs()

    args = ('--settings=eventboard.settings.testpg', ) + args

    web_id = get_container_id('web')

    _run_command(
        'docker exec -it {} /vagrant/scripts/runtests {}'.format(
            web_id, ' '.join(args)),
        interactive=True)


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('ARGS', nargs=-1, type=click.UNPROCESSED)
def collectstatic(args):
    """Collect the static files"""
    if not args:
        args = ('--noinput', '-l')

    if '--noinput' not in args:
        args += ('--noinput',)

    _run_command('git submodule update --init')

    web_id = get_container_id('web')

    bower_cmd = 'bower install --config.interactive=false'

    if spawn.find_executable('bower'):
        subprocess.call(bower_cmd.split(" "))
    else:
        _run_command(
            'docker exec -it {} scripts/do/remote_bower_install.sh'.format(
                web_id),
            unbuffered_print=True)

    _run_command(
        'docker exec -it {} python manage.py collectstatic {}'.format(
            web_id, ' '.join(args)),
        unbuffered_print=True)


@cli.command()
@click.argument('path', type=click.STRING, nargs=1)
def script(path):
    """Run python script in path"""
    web_id = get_container_id('web')
    _run_command(
        'docker exec -it {} python {}'.format(web_id, path), interactive=True)


@cli.command()
@click.argument('CONTAINER', default='web', type=click.STRING, nargs=1)
def bash(container):
    """Start a bash shell on CONTAINER. Default: web"""
    container_id = get_container_id(container)

    _run_command(
        'docker exec -it {} /bin/bash --login'.format(container_id),
        interactive=True)


@cli.command()
def shell():
    """Start the Django shell on the web container"""
    web_id = get_container_id('web')

    _run_command(
        'docker exec -it {} python manage.py shell'.format(web_id),
        interactive=True)


@cli.command()
def psql():
    """Start the postgres shell on the db container"""
    db_id = get_container_id('db')

    _run_command(
        'docker exec -it {} psql -U eb -d eb'.format(db_id),
        interactive=True)


@cli.command()
def influx():
    """Start the influx shell on the influx metrics worker"""
    influx_id = get_container_id('influxdb-metrics')

    _run_command(
        'docker exec -it {} influx -precision rfc3339'.format(influx_id),
        interactive=True)


@cli.command()
def debug():
    """Start an interactive runserver for debugging"""
    _run_command(
        'docker-compose stop web')
    _run_command(
        'docker-compose run web python manage.py runserver 0.0.0.0:8503',
        interactive=True)
    _run_command(
        'docker-compose start web')


@cli.command()
@click.argument('MACHINE_NAME', default=DEFAULT_MACHINE_NAME,
                type=click.STRING, nargs=1)
def machine_status(machine_name):
    """DEPRECATED: Shoes status of a docker machine"""
    logger.warning(
        DeprecationWarning("docker-machine has been deprecated").message)
    return _run_command(
        'docker-machine status {}'.format(machine_name).split(' '),
        use_docker_env=False)


@cli.command()
@click.argument('MACHINE_NAME', default=DEFAULT_MACHINE_NAME,
                type=click.STRING, nargs=1)
def start(machine_name):
    """Start the machine and all containers"""
    logger.warning(
        DeprecationWarning("docker-machine has been deprecated").message)
    _run_command('docker-machine start {}'.format(machine_name),
                 use_docker_env=False)
    _run_command('docker-compose up -d')


@cli.command()
@click.argument('MACHINE_NAME', default=DEFAULT_MACHINE_NAME,
                type=click.STRING, nargs=1)
def start_machine(machine_name):
    """DEPRECATED: start the machine if it isn't already running"""
    logger.warning(
        DeprecationWarning("docker-machine has been deprecated").message)
    output = _run_command(
        'docker-machine status {}'.format(machine_name),
        use_docker_env=False)
    logger.debug('Machine is {}'.format(output))
    if 'Stopped' in output:
        logger.debug('Starting {}'.format(machine_name))
        _run_command('docker-machine start {}'.format(machine_name),
                     use_docker_env=False)


@cli.command()
@click.argument('MACHINE_NAME', default=DEFAULT_MACHINE_NAME,
                type=click.STRING, nargs=1)
def stop(machine_name):
    """DEPRECATED: Stop the machine and all containers"""
    logger.warning(
        DeprecationWarning("docker-machine has been deprecated").message)
    try:
        _run_command('docker-machine stop {}'.format(machine_name),
                     use_docker_env=False)
    except subprocess.CalledProcessError as e:
        logger.debug(e)


@cli.command()
@click.option('--machine-name', default=DEFAULT_MACHINE_NAME,
              type=click.STRING, nargs=1)
@click.option('--driver', '-d', default='virtualbox', type=click.STRING,
              nargs=1)
@click.option('--cpu-count', '-c', default=1, type=click.INT, nargs=1)
@click.option('--memory', '-m', default=2048, type=click.INT, nargs=1)
def rebuild_vm(machine_name, driver, cpu_count, memory):
    """DEPRECATED: Rebuild docker machine and all containers.
    Supported drivers are: virtualbox, vmwarefusion"""
    logger.warning(
        DeprecationWarning("docker-machine has been deprecated").message)

    _run_command('docker-machine rm -f {}'.format(machine_name),
                 use_docker_env=False)

    create_cmd = 'docker-machine create --driver {}'.format(driver)

    if "vmwarefusion" in driver:
        create_cmd += ' --vmwarefusion-cpu-count {} '\
                      '--vmwarefusion-memory-size {}'.format(cpu_count, memory)
    elif "virtualbox" in driver:
        create_cmd += ' --virtualbox-cpu-count {} ' \
                      '--virtualbox-memory {}'.format(cpu_count, memory)

    create_cmd += ' {}'.format(machine_name)
    _run_command(create_cmd,
                 use_docker_env=False, unbuffered_print=True)

    _run_command('docker-compose build', unbuffered_print=True)


@cli.command()
@click.argument('CONTAINER_NAME', default='all', nargs=1)
def rebuild(container_name):
    """Rebuild $CONTAINER_NAME. If $CONTAINER_NAME isn't specified then all
    containers are rebuilt.

    Note: This command is only useful if you've been playing around with the
    images"""
    if container_name != 'all':
        container_id = get_container_id(container_name)
    else:
        container_id = '$(docker ps -a -q)'

    _run_command(('docker rm -f {}'.format(container_id)))

    if container_name != 'all':
        _run_command('docker-compose build'.format(container_name),
                     unbuffered_print=True)
    else:
        _run_command('docker-compose build', unbuffered_print=True)


def _run_command(cmd, interactive=False, use_docker_env=False,
                 unbuffered_print=False):
    """
    Executes a given shell command

    Args:
        cmd (str): The command to execute
        interact (bool): If True hand the controlling terminal over to the
            subprocess. Useful when user input is needed for the command
        use_docker_env (bool): Prefix the commands with the output of
            ``docker-machine env <machine name>``.

    Returns:
        str: Output of the command
    """
    logger.debug(cmd)
    env = None
    if use_docker_env:
        env = docker_env_prefix()

    create_slcpy_network()

    if interactive:
        try:
            import pexpect
        except ImportError:
            sys.stderr.write('Missing pexpect requirement. pip install '
                             'pexpect')
            sys.exit(1)
        sys.stdout.write('Running interactive command...\n')

        cmd = cmd.split(' ')
        pexpect.spawn(cmd[0], list(cmd[1:]), env=env).interact()
    else:
        import subprocess

        try:
            p = subprocess.Popen(
                cmd.strip(),
                shell=True,
                bufsize=0,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                env=env)

            if unbuffered_print:
                while p.poll() is None:
                    for l in p.stdout.readline():
                        click.echo(l, nl=False)
            else:
                p.wait()
                return p.stdout.read().decode("utf8")

        except subprocess.CalledProcessError:
            sys.exit(1)


def create_slcpy_network():
    try:
        # Quietly try to create the network
        p = subprocess.Popen(
            'docker network create slcpy',
            shell=True,
            bufsize=0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        p.wait()
        return

    except subprocess.CalledProcessError:
        sys.exit(1)


if __name__ == '__main__':
    cli()
