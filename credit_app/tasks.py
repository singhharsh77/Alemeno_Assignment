import pandas as pd
from celery import shared_task
from .models import Customer, Loan

@shared_task
def ingest_data():
    cust_df = pd.read_csv('data/customer_data.csv')
    for _, row in cust_df.iterrows():
        Customer.objects.update_or_create(
            customer_id=row['Customer ID'],
            defaults={
                'first_name': row['First Name'], 'last_name': row['Last Name'],
                'age': row['Age'], 'phone_number': row['Phone Number'],
                'monthly_salary': row['Monthly Salary'], 'approved_limit': row['Approved Limit']
            }
        )
    
    loan_df = pd.read_csv('data/loan_data.csv')
    for _, row in loan_df.iterrows():
        cust = Customer.objects.get(customer_id=row['Customer ID'])
        Loan.objects.update_or_create(
            loan_id=row['Loan ID'],
            defaults={
                'customer': cust, 'loan_amount': row['Loan Amount'],
                'tenure': row['Tenure'], 'interest_rate': row['Interest Rate'],
                'monthly_repayment': row['Monthly payment'],
                'emis_paid_on_time': row['EMIs paid on Time'],
                'start_date': row['Date of Approval'], 'end_date': row['End Date']
            }
        )
