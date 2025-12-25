# ☁️ Free Cloud Hosting Plan

This guide outlines how to host the **Copilot AI Customer Service Platform** completely for **FREE** using generous "Always Free" tiers from major cloud providers.

We propose two architectures:
1.  **The "Power User" Stack (Oracle Cloud)** - Best for full control and performance.
2.  **The "Serverless" Hybrid (Hugging Face + Supabase)** - Best for ease of use and AI features.

---

## 🏆 Option 1: The "Power User" Stack (Recommended)

**Provider:** [Oracle Cloud Infrastructure (OCI)](https://www.oracle.com/cloud/free/)

Oracle offers the most generous free tier in the industry, capable of running our entire `docker-compose` stack on a single powerful virtual machine.

### The Free Resources
- **Compute:** 4x ARM Ampere A1 Compute Instances (up to **4 OCPUs** and **24 GB RAM**).
- **Storage:** 200 GB Block Volume.
- **Network:** 10 TB outbound data transfer per month.

### Deployment Steps
1.  **Sign Up:** Create an Oracle Cloud Free Tier account.
2.  **Create VM:** Launch a new instance using the **Canonical Ubuntu** image and select the **Ampere** shape (VM.Standard.A1.Flex). Assign 4 OCPUs and 24GB RAM.
3.  **Setup Docker:** SSH into your new VM and install Docker:
    ```bash
    sudo apt update
    sudo apt install docker.io docker-compose -y
    sudo usermod -aG docker $USER
    ```
4.  **Clone & Run:**
    ```bash
    git clone https://github.com/A-Elfiiky/chat_agent_multi_llm_platform.git
    cd chat_agent_multi_llm_platform
    cp .env.example .env
    # Edit .env with your keys
    docker-compose up -d --build
    ```
5.  **Expose Ports:** In the Oracle Cloud Console, go to "Virtual Cloud Network" > "Security Lists" and allow Inbound Traffic on ports `8000`, `8001`, `8002`, and `3000`.

---

## 🚀 Option 2: The "Serverless" Hybrid

This approach splits the application into specialized managed services.

### 1. Frontend Hosting
*   **Provider:** [GitHub Pages](https://pages.github.com/) or [Vercel](https://vercel.com/)
*   **Cost:** Free
*   **Setup:**
    *   Push the `clients/web-widget` folder to a new repo or configure GitHub Pages to serve from `/docs` or a specific branch.
    *   Update the widget configuration to point to your backend URL.

### 2. Backend API Hosting
*   **Provider:** [Hugging Face Spaces](https://huggingface.co/spaces)
*   **Cost:** Free (2 vCPU, 16GB RAM)
*   **Setup:**
    *   Create a new **Docker Space** on Hugging Face.
    *   Connect it to your GitHub repository.
    *   Hugging Face will build and run your Docker container automatically.
    *   *Note:* You may need to combine the services into a single container or use multiple Spaces.

### 3. Database (Conversation Memory)
*   **Provider:** [Supabase](https://supabase.com/)
*   **Cost:** Free (500MB Database)
*   **Setup:**
    *   Create a project.
    *   Get the **PostgreSQL Connection String**.
    *   Update your `.env` to use Postgres instead of SQLite (requires code update in `conversation_memory.py`).

### 4. Vector Storage (RAG Index)
*   **Provider:** [Qdrant Cloud](https://qdrant.tech/)
*   **Cost:** Free (1GB Cluster)
*   **Setup:**
    *   Create a free cluster.
    *   Get the API Key and URL.
    *   Update `rag_client.py` to use the Qdrant client instead of local FAISS.

---

## 📊 Comparison

| Feature | Oracle Cloud (Option 1) | Hybrid Serverless (Option 2) |
| :--- | :--- | :--- |
| **Effort** | Medium (Linux Admin) | Low (Managed Services) |
| **Performance** | ⭐⭐⭐⭐⭐ (Dedicated VM) | ⭐⭐⭐ (Shared Resources) |
| **Scalability** | Vertical (up to 24GB RAM) | Horizontal (Auto-scaling) |
| **Persistence** | Local Disk / Docker Volumes | Managed Cloud DBs |
| **Cost** | **$0.00** | **$0.00** |

## 💡 Recommendation
Start with **Option 1 (Oracle Cloud)**. It allows you to run the project *exactly as it is* without modifying the code to support external databases or vector stores immediately.
