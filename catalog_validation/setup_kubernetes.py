import subprocess
import time

from .exceptions import KubernetesSetupException
from .k8s.api_client import api_client


def setup_kubernetes_cluster():
    subprocess.run('curl -sfL https://get.k3s.io | sh -', shell=True, check=True, timeout=300)
    # This call returns after starting k3s, however we will wait and ensure it is properly setup ( there are no
    # taints etc ) before actually trying to deploy resources
    count = 0
    while True:
        cp = subprocess.run(['systemctl', 'is-active', '--quiet', 'k3s'])
        if cp.returncode == 0:
            break
        if count > 2:
            raise KubernetesSetupException('Failed to start K3s')

        count += 1
        time.sleep(30)

    # Now k3s should report itself as running
    with api_client() as core_api:
        # Let's give it some more time to make sure that the node is not tainted and are actually usable
        count = 0
        while True:
            if count > 4:
                raise KubernetesSetupException('Failed to configure k3s node')

            nodes = core_api.list_node().items
            if not nodes or nodes[0].spec.taints:
                count += 1
                time.sleep(30 * count)
            else:
                break
