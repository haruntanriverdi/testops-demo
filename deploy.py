#!/usr/bin/env python3

import argparse
import time
import logging
import yaml
from kubernetes import client, config, utils

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)


def load_config():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def apply_yaml_file(filepath):
    k8s_client = client.ApiClient()
    utils.create_from_yaml(k8s_client, filepath, verbose=False)
    log.info(f"Applied: {filepath}")


def scale_chrome_nodes(apps_api, count):
    count = max(1, min(5, count))
    apps_api.patch_namespaced_deployment(
        name="chrome-node",
        namespace="default",
        body={"spec": {"replicas": count}}
    )
    log.info(f"Scaled chrome-node to {count} replica(s)")


def wait_pods_ready(core_api, label, expected, timeout=120):
    log.info(f"Waiting for {expected} pod(s) with label '{label}'...")

    elapsed = 0
    interval = 5

    while elapsed < timeout:
        pods = core_api.list_namespaced_pod(
            namespace="default",
            label_selector=label
        )
        ready = 0
        for pod in pods.items:
            if pod.status.phase == "Running":
                containers = pod.status.container_statuses or []
                if all(c.ready for c in containers):
                    ready += 1

        log.info(f"  [{ready}/{expected} ready]")

        if ready >= expected:
            log.info("All pods ready")
            return True

        time.sleep(interval)
        elapsed += interval

    raise TimeoutError(f"Pods not ready after {timeout}s")


def get_pod_logs(core_api, label):
    pods = core_api.list_namespaced_pod(
        namespace="default",
        label_selector=label
    )
    for pod in pods.items:
        name = pod.metadata.name
        try:
            logs = core_api.read_namespaced_pod_log(
                name=name,
                namespace="default",
                tail_lines=100
            )
            log.info(f"--- Logs from {name} ---")
            print(logs)
        except client.exceptions.ApiException as e:
            log.warning(f"Could not read logs from {name}: {e.reason}")


def cleanup_old_job(batch_api):
    try:
        batch_api.delete_namespaced_job(
            name="test-controller",
            namespace="default",
            body=client.V1DeleteOptions(propagation_policy="Foreground")
        )
        log.info("Cleaned up old test-controller job")
        time.sleep(5)
    except client.exceptions.ApiException:
        pass


def wait_test_complete(core_api, timeout=300):
    log.info("Waiting for test-controller to finish...")

    elapsed = 0
    interval = 10

    while elapsed < timeout:
        pods = core_api.list_namespaced_pod(
            namespace="default",
            label_selector="app=test-controller"
        )
        for pod in pods.items:
            phase = pod.status.phase
            if phase == "Succeeded":
                log.info("Test controller finished successfully")
                return True
            elif phase == "Failed":
                log.error("Test controller failed")
                return False

        time.sleep(interval)
        elapsed += interval

    raise TimeoutError(f"Test controller did not finish within {timeout}s")


def main():
    parser = argparse.ArgumentParser(description="Deploy and run Selenium tests on K8s")
    parser.add_argument("--node-count", type=int, default=1, help="Chrome node count (1-5)")
    args = parser.parse_args()

    load_config()
    apps_api = client.AppsV1Api()
    core_api = client.CoreV1Api()
    batch_api = client.BatchV1Api()

    # deploy chrome node
    log.info("Deploying Chrome Node...")
    try:
        apply_yaml_file("k8s/chrome-node.yaml")
    except utils.FailToCreateError:
        log.info("Chrome Node already exists, scaling...")
        scale_chrome_nodes(apps_api, args.node_count)

    scale_chrome_nodes(apps_api, args.node_count)
    wait_pods_ready(core_api, "app=chrome-node", args.node_count)

    log.info("Waiting for Selenium to initialize...")
    time.sleep(10)

    # deploy test controller job
    log.info("Deploying Test Controller...")
    cleanup_old_job(batch_api)
    apply_yaml_file("k8s/test-controller.yaml")
    wait_test_complete(core_api)

    # collect logs
    log.info("Collecting results...")
    get_pod_logs(core_api, "app=test-controller")
    get_pod_logs(core_api, "app=chrome-node")

    # cleanup
    log.info("Cleaning up resources...")
    cleanup_old_job(batch_api)
    try:
        apps_api.delete_namespaced_deployment(name="chrome-node", namespace="default")
        core_api.delete_namespaced_service(name="chrome-node", namespace="default")
        log.info("Deleted chrome-node deployment and service")
    except client.exceptions.ApiException as e:
        log.warning(f"Cleanup failed: {e.reason}")

    log.info("Done")


if __name__ == "__main__":
    main()
