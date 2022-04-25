#!/usr/bin/env python
import argparse
import os
import subprocess

from catalog_validation.exceptions import CatalogDoesNotExist, KubernetesSetupException
from catalog_validation.git_utils import get_affected_catalog_items_with_versions
from catalog_validation.k8s.utils import KUBECONFIG_FILE
from catalog_validation.setup_kubernetes import setup_kubernetes_cluster


def deploy_charts(catalog_path, base_branch):

    affected_items = []
    print('[\033[94mINFO\x1B[0m]\tDetermining changed catalog items')
    try:
        affected_items = get_affected_catalog_items_with_versions(catalog_path, base_branch)
    except CatalogDoesNotExist:
        print(f'[\033[91mFAILED\x1B[0m]\tSpecified {catalog_path!r} path does not exist')
        exit(1)
    except subprocess.CalledProcessError as e:
        print(f'[\033[91mFAILED\x1B[0m]\tFailed to determine changed catalog items: {e}')
        exit(1)

    if not affected_items:
        print('[\033[92mOK\x1B[0m]\tNo changed catalog items detected')
        exit(0)

    print(
        f'[\033[94mINFO\x1B[0m]\tChanged catalog items detected: {",".join(".".join(item) for item in affected_items)}'
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
    failures = []
    env = dict(os.environ, KUBECONFIG=KUBECONFIG_FILE)
    for index, catalog_item in enumerate(affected_items):
        print(f'[\033[94mINFO\x1B[0m]\tInstalling {".".join(catalog_item)}')
        chart_path = os.path.join(catalog_path, catalog_item.train, catalog_item.item, catalog_item.version)
        chart_release_name = f'{catalog_item.item}-{index}'
        cp = subprocess.Popen(
            [
                'helm', 'install', chart_release_name, chart_path, '-n',
                chart_release_name, '--create-namespace', '--wait',
                '-f', os.path.join(chart_path, 'test_values.yaml'), '--debug', '--timeout', '600s'
            ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        stderr = cp.communicate(timeout=300)[1]
        if cp.returncode:
            failures.append(f'Failed to install chart release {".".join(catalog_item)}: {stderr.decode()}')
            continue

        print(f'[\033[94mINFO\x1B[0m]\tTesting {".".join(catalog_item)}')
        # We have deployed the chart release, now let's test it
        cp = subprocess.Popen(
            ['helm', 'test', chart_release_name, '-n', chart_release_name, '--debug'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
        )
        err = cp.communicate(timeout=300)[0]
        if cp.returncode:
            failures.append(f'Helm test failed for {".".join(catalog_item)}: {err.decode(errors="ignore")}')

        print(f'[\033[94mINFO\x1B[0m]\tRemoving {".".join(catalog_item)}')
        # We have deployed and tested the chart release, now let's remove it
        # This prevents resource consumption issues when testing lots of releases
        cp = subprocess.Popen(
            ['helm', 'uninstall', chart_release_name, '-n', chart_release_name, '--debug'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
        )
        cp.communicate(timeout=300)
        if cp.returncode:
            failures.append(f'Helm Uninstall failed for {".".join(catalog_item)}')

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
