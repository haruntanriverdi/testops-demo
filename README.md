# testops-demo

Selenium test suite that verifies QA job listings on a careers website, containerized and deployed on AWS EKS.

## overview

Two pods running on Kubernetes:

- **test-controller** — pytest + selenium (RemoteWebDriver). Runs as a Job, exits when done.
- **chrome-node** — selenium/standalone-chrome:4.27. Scalable from 1 to 5 replicas.

```
EC2 (t2.micro)
  └── kubectl / deploy.py
        └── EKS Cluster
              ├── test-controller (Job)  ──▶  chrome-node:4444 (Service)
              └── chrome-node (Deployment, 1-5 replicas)
```

## how test controller sends tests to chrome node

The test-controller pod doesn't run a browser itself. It uses Selenium's `RemoteWebDriver` to send test commands to a Chrome instance running in a separate pod.

On startup, the test-controller reads the `SELENIUM_HUB` environment variable (set to `http://chrome-node:4444` in the K8s manifest). The pytest fixture in `conftest.py` creates a `webdriver.Remote(command_executor=selenium_hub)` session. From that point, every Selenium call (open page, click, find element, etc.) is sent as an HTTP request to the Chrome node's WebDriver API on port 4444. Chrome executes the action and returns the result.

The test-controller only contains the test logic and page objects — the actual browser execution happens entirely on the chrome-node pod.

## inter-pod communication

Pods in Kubernetes get dynamic IPs that change on every restart. To avoid hardcoding IPs, a **Service** object is created for chrome-node (`k8s/chrome-node.yaml`). The Service has a stable DNS name: `chrome-node`.

When the test-controller makes a request to `http://chrome-node:4444`, Kubernetes DNS resolves `chrome-node` to the Service's ClusterIP (`10.100.x.x`). The Service then forwards the traffic to one of the chrome-node pods on port 4444.

This means:
- test-controller never needs to know chrome-node's actual pod IP
- If a chrome-node pod restarts and gets a new IP, the Service handles it
- Scaling chrome-node replicas up/down is transparent to test-controller

## test scenario

1. Open careers page
2. Navigate to open positions
3. Filter: Istanbul, Turkiye + Quality Assurance
4. Assert each job has correct title, department, location
5. Click first job, verify lever.co redirect

## project structure

```
pages/               # page objects (POM pattern)
  base_page.py
  careers_page.py
  open_positions_page.py
  lever_page.py
tests/
  conftest.py        # webdriver fixture (local or remote)
  test_qa_jobs.py
k8s/
  chrome-node.yaml   # deployment + service
  test-controller.yaml  # job
deploy.py            # orchestrates k8s deployment
Dockerfile           # test-controller image
Dockerfile.chrome    # chrome node image
docker-compose.yml   # local dev (ARM compatible)
```

## deploying locally

### option 1: docker-compose

```bash
docker-compose up --build
```

Uses `seleniarm/standalone-chromium` for Apple Silicon. For x86 machines swap with `selenium/standalone-chrome`.

### option 2: minikube

```bash
minikube start
eval $(minikube docker-env)
docker build -t testops/test-controller .
# update test-controller.yaml image to testops/test-controller:latest
# and set imagePullPolicy: Never
kubectl apply -f k8s/chrome-node.yaml
kubectl apply -f k8s/test-controller.yaml
kubectl logs -f -l app=test-controller
```

## deploying to AWS EKS

### prerequisites

EC2 instance (t2.micro) with: aws-cli, docker, kubectl, eksctl, python3

### 1. create EKS cluster

```bash
eksctl create cluster \
  --name testops \
  --region eu-north-1 \
  --node-type t3.small \
  --nodes 2 --nodes-min 1 --nodes-max 4
```

### 2. push test-controller image to ECR

```bash
aws ecr create-repository --repository-name testops/test-controller --region eu-north-1

aws ecr get-login-password --region eu-north-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-north-1.amazonaws.com

docker build --platform linux/amd64 -t testops/test-controller .
docker tag testops/test-controller:latest <account-id>.dkr.ecr.eu-north-1.amazonaws.com/testops/test-controller:latest
docker push <account-id>.dkr.ecr.eu-north-1.amazonaws.com/testops/test-controller:latest
```

### 3. run tests

```bash
python3 deploy.py --node-count=2
```

deploy.py handles the full lifecycle:
1. Creates chrome-node Deployment + Service
2. Scales to requested node count (1-5)
3. Waits for pods to be ready
4. Submits test-controller Job
5. Waits for completion
6. Collects logs from both pods
7. Cleans up all resources

## tech

python 3.13, selenium 4.40, pytest 9.0, docker, kubernetes (EKS), AWS (EC2, ECR)
