#!/usr/bin/env python
import argparse
import os
import subprocess

from catalog_validation.ci.utils import get_ci_development_directory
from catalog_validation.exceptions import CatalogDoesNotExist, KubernetesSetupException
from catalog_validation.git_utils import get_changed_apps
from catalog_validation.k8s.utils import KUBECONFIG_FILE
from catalog_validation.setup_kubernetes import setup_kubernetes_cluster


def deploy_charts(catalog_path, base_branch):

    affected_items = []
    print('[\033[94mINFO\x1B[0m]\tDetermining changed catalog items')
    try:
        affected_items = get_changed_apps(catalog_path, base_branch)
    except CatalogDoesNotExist:
        print(f'[\033[91mFAILED\x1B[0m]\tSpecified {catalog_path!r} path does not exist')
        exit(1)
    except subprocess.CalledProcessError as e:
        print(f'[\033[91mFAILED\x1B[0m]\tFailed to determine changed catalog items: {e}')
        exit(1)

    if not affected_items:
        print('[\033[92mOK\x1B[0m]\tNo changed catalog items detected')
        exit(0)

    affected_items = [(train, app) for train in affected_items for app in affected_items[train]]
    affected_items_str = ', '.join(f'{train}.{app}' for train, app in affected_items)
    print(
        f'[\033[94mINFO\x1B[0m]\tChanged catalog items detected: {affected_items_str}'
    )
    # Now we wil setup kubernetes cluster
    print('[\033[94mINFO\x1B[0m]\tSetting up kubernetes cluster')
    try:
        setup_kubernetes_cluster()
    except (subprocess.CalledProcessError, KubernetesSetupException) as e:
        print(f'[\033[91mFAILED\x1B[0m]\tFailed to setup kubernetes cluster: {e}')
        exit(1)

    # We should have kubernetes running as desired now
    # We expect helm to already be installed in the environment
    dev_dir = get_ci_development_directory(catalog_path)
    failures = []
    env = dict(os.environ, KUBECONFIG=KUBECONFIG_FILE)
    for index, catalog_item in enumerate(affected_items):
        formatted_item_name = '.'.join(catalog_item)
        train, app = catalog_item
        print(f'[\033[94mINFO\x1B[0m]\tInstalling {formatted_item_name}')
        chart_path = os.path.join(dev_dir, train, app)
        chart_release_name = f'{app}-{index}'
        cp = subprocess.Popen(
            [
                'helm', 'install', chart_release_name, chart_path, '-n',
                chart_release_name, '--create-namespace', '--wait',
                '-f', os.path.join(chart_path, 'test_values.yaml'), '--debug', '--timeout', '600s'
            ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        try:
            stderr = cp.communicate(timeout=600)[1]
        except subprocess.TimeoutExpired:
            failures.append(f'Failed to install {formatted_item_name!r} chart release as it timed out')
            continue
        else:
            if cp.returncode:
                failures.append(f'Failed to install chart release {formatted_item_name}: {stderr.decode()}')
                continue

        print(f'[\033[94mINFO\x1B[0m]\tTesting {formatted_item_name}')
        # We have deployed the chart release, now let's test it
        cp = subprocess.Popen(
            ['helm', 'test', chart_release_name, '-n', chart_release_name, '--debug'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
        )
        try:
            err = cp.communicate(timeout=600)[0]
        except subprocess.TimeoutExpired:
            failures.append(f'Failed to test {formatted_item_name!r} chart release as it timed out')
        else:
            if cp.returncode:
                failures.append(f'Helm test failed for {formatted_item_name}: {err.decode(errors="ignore")}')

        print(f'[\033[94mINFO\x1B[0m]\tRemoving {formatted_item_name}')
        # We have deployed and tested the chart release, now let's remove it
        # This prevents resource consumption issues when testing lots of releases
        cp = subprocess.Popen(
            ['helm', 'uninstall', chart_release_name, '-n', chart_release_name, '--debug'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
        )
        try:
            cp.communicate(timeout=600)
        except subprocess.TimeoutExpired:
            failures.append(f'Failed to uninstall {formatted_item_name!r} chart release as it timed out')
        else:
            if cp.returncode:
                failures.append(f'Helm Uninstall failed for {formatted_item_name}')

    if not failures:
        print('[\033[92mOK\x1B[0m]\tTests passed successfully')
        exit(0)

    print('[\033[91mFAILED\x1B[0m]\tFollowing errors were encountered while testing catalog items:')
    for index, failure in enumerate(failures):
        print(f'[\033[91m{index}\x1B[0m]\t{failure}')

    exit(1)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help', dest='action')

    parser_setup = subparsers.add_parser(
        'deploy', help='Validate TrueNAS catalog items by deploying them in kubernetes cluster'
    )
    parser_setup.add_argument('--path', help='Specify path of TrueNAS catalog', required=True)
    parser_setup.add_argument(
        '--base_branch', help='Specify base branch to find changed catalog items', default='master'
    )

    args = parser.parse_args()
    if args.action == 'deploy':
        deploy_charts(args.path, args.base_branch)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
