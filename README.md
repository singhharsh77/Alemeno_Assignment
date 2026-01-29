# 🏦 Credit Approval System

A robust backend system for processing credit applications, calculating creditworthiness, and managing loans. Built with **Django**, **Django Rest Framework (DRF)**, **Celery**, **Redis**, and **PostgreSQL**, fully containerized with **Docker**.

---

## 🚀 Tech Stack

-   **Backend**: Python, Django, Django Rest Framework
-   **Database**: PostgreSQL
-   **Async Tasks**: Celery, Redis
-   **Containerization**: Docker, Docker Compose
-   **Data Processing**: Pandas, OpenPyXL

---

## 🛠️ Setup & Installation

The entire application is containerized for easy setup.

### Prerequisites

-   Docker & Docker Compose installed on your machine.

### Steps to Run

1.  **Clone the Repository**
    ```bash
    git clone <repository_url>
    cd Alemeno_Assignment
    ```

2.  **Start Services**
    Run the following command to build and start the containers (Web, Worker, DB, Redis):
    ```bash
    docker-compose up --build
    ```

3.  **Data Ingestion (Crucial Step)**
    Once the containers are running, you need to trigger the ingestion of `customer_data.xlsx` and `loan_data.xlsx`.
    *Note: This is handled seamlessly via a background task or management command.*
    
    To manually trigger ingestion via the Django management command (if exposed) or simply rely on the background worker if configured to run on startup.
    
    *(In this implementation, you can assume data is ingested upon startup or via specific celery triggers)*.

4.  **Access the API**
    The server will be running at `http://localhost:8000`.

---

## 📡 API Endpoints

### 1. Register Customer
-   **Endpoint**: `/register`
-   **Method**: `POST`
-   **Description**: Registers a new customer and calculates their approved credit limit.
-   **Payload**:
    ```json
    {
      "first_name": "John",
      "last_name": "Doe",
      "age": 30,
      "monthly_income": 50000,
      "phone_number": 9876543210
    }
    ```

### 2. Check Loan Eligibility
-   **Endpoint**: `/check-eligibility`
-   **Method**: `POST`
-   **Description**: Checks if a customer is eligible for a loan based on credit score logic.
-   **Logic**:
    -   Calculates a credit score based on past loan history.
    -   Validates against approved credit limit.
    -   Checks debt-to-income ratio.

### 3. Create Loan
-   **Endpoint**: `/create-loan`
-   **Method**: `POST`
-   **Description**: Processes a loan application. If eligible, creates a Loan record.

### 4. View Loan Details
-   **Endpoint**: `/view-loan/{loan_id}`
-   **Method**: `GET`
-   **Description**: Fetch details of a specific loan.

### 5. View Customer Loans
-   **Endpoint**: `/view-loans/{customer_id}`
-   **Method**: `GET`
-   **Description**: List all current loans for a specific customer.

---

## 🧠 Key Features & Implementation Details

### 1. Background Data Ingestion
-   **Challenge**: Efficiently processing large Excel files (`customer_data.xlsx`, `loan_data.xlsx`) without blocking the main thread.
-   **Solution**: Leveraged **Celery workers** to handle ingestion asynchronously. This prevents timeout issues and keeps the web server responsive.

### 2. Credit Scoring Algorithm
-   **Challenge**: Implementing specific business rules for credit scoring based on historic data.
-   **Logic Implemented**:
    -   **Score Calculation**: Based on total loans, current loan details, and payment history.
    -   **Approval Tiers**:
        -   Score > 50: Approved immediately.
        -   50 > Score > 30: Approved with higher interest (>12%).
        -   30 > Score > 10: Approved with much higher interest (>16%).
        -   Score < 10: Rejected.
    -   **Safety Checks**: Loans are rejected if the total EMI exceeds 50% of monthly income.

### 3. Dockerized Environment
-   **Challenge**: Ensuring consistency across different development environments.
-   **Solution**: Created a `docker-compose.yml` to orchestrate:
    -   `web`: Django application (Gunicorn/Runserver).
    -   `worker`: Celery worker for async tasks.
    -   `db`: PostgreSQL database.
    -   `redis`: Message broker for Celery.

---

## 🚧 Challenges Faced

1.  **Async Configuration**: Setting up Celery with Redis requires careful configuration of network hosts within Docker (using service names `redis` instead of `localhost`).
2.  **Data Consistency**: Ensuring `customer_data` and `loan_data` map correctly during ingestion, especially calculating the `approved_limit` dynamically if it wasn't provided or needed adjustment.
3.  **Complex Business Logic**: Translating the textual requirements for the credit scoring system into precise Python logic, covering edge cases like "rounding to the nearest lakh" and interest rate corrections.

### Built By Harsh Singh | haharshsingh57@gmail.com