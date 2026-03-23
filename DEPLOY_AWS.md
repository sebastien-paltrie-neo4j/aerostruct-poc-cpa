# Deploying on AWS App Runner

Deploy **ah-tri-topo** on **AWS App Runner** from a GitHub repository.

---

## 1. Prerequisites

- An **AWS** account (App Runner + IAM permissions)
- **GitHub** repository containing this project (root: `backend/`, `frontend/`, `requirements.txt`, `apprunner.yaml`)
- **Neo4j** accessible from the internet (e.g. Aura). Credentials (URI, user, password) are provided via **SSM Parameter Store** — never hardcoded.

---

## 2. Create the App Runner service (AWS console)

### 2.1 Open App Runner

1. In the AWS console, go to **App Runner**.
2. Click **Create service**.

### 2.2 Repository (Source)

1. **Source**: choose **Source code repository**.
2. **Connect to GitHub**: authorise AWS to access your GitHub account (one-time step).
3. Select the **repository** and **branch** (e.g. `main`).
4. **Deployment trigger**: **Automatic** (deploys on every push to the branch).

### 2.3 Build (Configure build)

Choose **Use a configuration file stored in your source code repository**. The build, pre-run, start command, port, and SSM secrets are all read from **`apprunner.yaml`** at the repository root. Do not manually fill in the Build command or Start command fields.

### 2.4 Service

- **Service name**: e.g. `ah-tri-topo`
- **CPU / Memory**: e.g. 1 vCPU, 2 GB
- **Environment variables**: via SSM Parameter Store (`apprunner.yaml` → `run.secrets`).  
  Create the following parameters in **Systems Manager → Parameter Store** (same region/account as App Runner) before deploying:
  - `/ah-tri-topo/NEO4J_URI`
  - `/ah-tri-topo/NEO4J_USER`
  - `/ah-tri-topo/NEO4J_PASSWORD`

### 2.5 Security (role and permissions)

In the **Security** step ("Specify an Instance role and an AWS KMS encryption key"):

- **Instance role**: required (the app reads SSM parameters at runtime). Create a role with SSM read access → see § 2.5.1.
- **AWS KMS key**: leave as **Use an AWS-owned key** (default).
- **WAF**: leave disabled unless required.

#### 2.5.1 Create the IAM role for SSM access (Instance role)

1. **IAM** → **Roles** → **Create role**.
2. **Trusted entity type**: **Custom trust policy**. Paste the following trust relationship (from AWS docs):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": { "Service": "apprunner.amazonaws.com" },
         "Action": "sts:AssumeRole"
       }
     ]
   }
   ```
   → **Next**.
3. **Add permissions**: attach the managed policy **AmazonSSMReadOnlyAccess**.
4. Name the role (e.g. `apprunner-ah-tri-topo-ssm`) → **Create role**.
5. In App Runner, under **Security**, select this role in **Choose an Instance role**.

### 2.6 Create the service

Click **Create & deploy**. The first deployment may take a few minutes. Once complete, App Runner provides a URL such as:  
`https://xxxxx.region.awsapprunner.com`.

---

## 3. Verification

- Open the service URL: the Gantt page should load.
- Test **Load Baseline** with a valid root WorkOrder (Neo4j must be reachable from AWS).
