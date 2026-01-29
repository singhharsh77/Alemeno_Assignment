import pandas as pd
from celery import shared_task
from .models import Customer, Loan
import os

@shared_task
def ingest_customer_data():
    file_path = 'customer_data.xlsx'
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    df = pd.read_excel(file_path)
    df = df.drop_duplicates(subset=['Customer ID'])
    
    customers_to_create = []
    for _, row in df.iterrows():
        # Check if customer exists to avoid duplication if run multiple times
        c_id = row['Customer ID']
        if not Customer.objects.filter(customer_id=c_id).exists():
            customers_to_create.append(
                Customer(
                    customer_id=c_id,
                    first_name=row['First Name'],
                    last_name=row['Last Name'],
                    phone_number=str(row['Phone Number']),
                    monthly_salary=row['Monthly Salary'],
                    approved_limit=row['Approved Limit'],
                    current_debt=0, # Not present in actual file
                    age=row.get('Age', 0)
                )
            )
    
    if customers_to_create:
        Customer.objects.bulk_create(customers_to_create)
        print(f"Successfully ingested {len(customers_to_create)} customers.")
    else:
        print("No new customers to ingest.")
    
    # Always reset the sequence to ensure it's correct even if no new customers were added
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT setval(pg_get_serial_sequence('core_customer', 'customer_id'), coalesce(max(customer_id), 1), max(customer_id) IS NOT null) FROM core_customer;")

@shared_task
def ingest_loan_data():
    file_path = 'loan_data.xlsx'
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    df = pd.read_excel(file_path)
    df = df.drop_duplicates(subset=['Loan ID'])
    
    loans_to_create = []
    for _, row in df.iterrows():
        try:
            customer = Customer.objects.get(customer_id=row['Customer ID'])
            
            # Check if loan exists
            l_id = row['Loan ID']
            if not Loan.objects.filter(loan_id=l_id).exists():
                loans_to_create.append(
                    Loan(
                        loan_id=l_id,
                        customer=customer,
                        loan_amount=row['Loan Amount'],
                        tenure=row['Tenure'],
                        interest_rate=row['Interest Rate'],
                        monthly_repayment=row['Monthly payment'],
                        emis_paid_on_time=row['EMIs paid on Time'],
                        start_date=row['Date of Approval'],
                        end_date=row['End Date']
                    )
                )
        except Customer.DoesNotExist:
            print(f"Customer ID {row['Customer ID']} not found for loan {row['Loan ID']}.")
        except Exception as e:
            print(f"Error processing loan {row['Loan ID']}: {e}")

    if loans_to_create:
        Loan.objects.bulk_create(loans_to_create)
        print(f"Successfully ingested {len(loans_to_create)} loans.")
    else:
        print("No new loans to ingest.")

    # Always reset the sequence
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT setval(pg_get_serial_sequence('core_loan', 'loan_id'), coalesce(max(loan_id), 1), max(loan_id) IS NOT null) FROM core_loan;")
