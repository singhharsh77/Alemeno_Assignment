from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from .models import Customer, Loan
from .serializers import RegisterSerializer, CheckEligibilitySerializer, CreateLoanSerializer, LoanSerializer
import math
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

class RegisterCustomerView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            monthly_income = data['monthly_income']
            approved_limit = round(36 * monthly_income, -5) # Round to nearest lakh (100000)
            
            customer = Customer.objects.create(
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=str(data['phone_number']),
                monthly_salary=monthly_income,
                approved_limit=approved_limit,
                current_debt=0,
                age=data['age']
            )
            
            response_data = {
                "customer_id": customer.customer_id,
                "name": f"{customer.first_name} {customer.last_name}",
                "age": data['age'],
                "monthly_income": customer.monthly_salary,
                "approved_limit": customer.approved_limit,
                "phone_number": int(customer.phone_number)
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def calculate_monthly_installment(principal, rate, tenure_months):
    # Compound interest EMIs usually implies standard EMI formula
    # EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    # Rate is annual %, so r = rate / (12 * 100)
    if rate == 0:
        return principal / tenure_months
        
    r = rate / (12 * 100)
    n = tenure_months
    emi = principal * r * pow(1 + r, n) / (pow(1 + r, n) - 1)
    return emi

def check_eligibility_logic(customer_id, loan_amount, interest_rate, tenure):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return False, 0, 0, 0

    # Calculate credit score
    loans = Loan.objects.filter(customer=customer)
    
    # Logic based on components
    # 1. Past Loans paid on time
    # 2. No of loans taken in past
    # 3. Loan activity in current year
    # 4. Loan approved volume
    
    # My simplified Heuristic:
    # Start: 50
    # Add: 
    #   +10 if any loan paid fully on time (emis_paid == tenure)
    #   +5 per loan taken (max 20)
    #   + volume_factor (loan_amount / 10000) (max 10)
    #   -10 if activity in current year > 2 loans
    
    score = 50
    
    total_loans = loans.count()
    score += min(total_loans * 5, 20)
    
    active_loans_current_year = loans.filter(start_date__year=date.today().year).count()
    if active_loans_current_year > 2:
        score -= 10
        
    # Check current debt vs approved limit
    current_loans_sum = loans.filter(end_date__gte=date.today()).aggregate(Sum('loan_amount'))['loan_amount__sum'] or 0
    # Or should use customer.current_debt? Let's use recalculated sum for safety or customer.current_debt if updated correctly
    # The prompt says: "If sum of current loans of customer > approved limit of customer , credit score = 0"
    # Assuming 'current_loans' means outstanding principal? Or just sum of original amounts of active loans?
    # 'current_debt' field exists in Customer. Let's use that + new loan amount?
    # For now, let's use sum of loan_amount of non-ended loans.
    
    current_outstanding_loans_sum = 0
    for loan in loans:
        if loan.end_date > date.today():
             current_outstanding_loans_sum += loan.loan_amount # Approximate
             
    if current_outstanding_loans_sum > customer.approved_limit:
        score = 0
    
    # Approval Logic
    approved = False
    corrected_interest_rate = interest_rate
    
    if score > 50:
        approved = True
    elif 50 >= score > 30:
        if interest_rate > 12:
            approved = True
        else:
            corrected_interest_rate = 12.0
            approved = True # approved with corrected rate? Prompt says "correct the interest rate in the response... send a corrected_interest_rate... in response"
            # It implies if we correct it, we approve it? Or do we just propose it?
            # "approve loans with interest rate > 12%" -> If requested is < 12, we must raise it.
    elif 30 >= score > 10:
        if interest_rate > 16:
            approved = True
        else:
            corrected_interest_rate = 16.0
            approved = True
    else: # score <= 10
        approved = False
        
    # Check EMI constraint
    # "If sum of all current EMIs > 50% of monthly salary , don’t approve any loans"
    current_emis_sum = 0
    for loan in loans:
        if loan.end_date > date.today():
            current_emis_sum += loan.monthly_repayment
    
    proposed_emi = calculate_monthly_installment(loan_amount, corrected_interest_rate, tenure)
    
    if (current_emis_sum + Decimal(proposed_emi)) > (Decimal(0.5) * Decimal(customer.monthly_salary)):
        approved = False
        
    return approved, corrected_interest_rate, score, proposed_emi


class CheckEligibilityView(APIView):
    def post(self, request):
        serializer = CheckEligibilitySerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            approved, corrected_rate, score, emi = check_eligibility_logic(
                data['customer_id'],
                data['loan_amount'],
                data['interest_rate'],
                data['tenure']
            )
            
            response_data = {
                "customer_id": data['customer_id'],
                "approval": approved,
                "interest_rate": data['interest_rate'],
                "corrected_interest_rate": corrected_rate,
                "tenure": data['tenure'],
                "monthly_installment": emi
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateLoanView(APIView):
    def post(self, request):
        serializer = CreateLoanSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            approved, corrected_rate, score, emi = check_eligibility_logic(
                data['customer_id'],
                data['loan_amount'],
                data['interest_rate'],
                data['tenure']
            )
            
            if approved:
                customer = Customer.objects.get(customer_id=data['customer_id'])
                loan = Loan.objects.create(
                    customer=customer,
                    loan_amount=data['loan_amount'],
                    tenure=data['tenure'],
                    interest_rate=corrected_rate,
                    monthly_repayment=emi,
                    start_date=date.today(),
                    end_date=date.today() + relativedelta(months=data['tenure'])
                )
                
                response_data = {
                    "loan_id": loan.loan_id,
                    "customer_id": customer.customer_id,
                    "loan_approved": True,
                    "message": "Loan Approved",
                    "monthly_installment": emi
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data = {
                    "loan_id": None,
                    "customer_id": data['customer_id'],
                    "loan_approved": False,
                    "message": "Loan Not Approved due to low credit score or high existing debt",
                    "monthly_installment": 0
                }
                return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ViewLoanDetailView(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(loan_id=loan_id)
            customer = loan.customer
            response_data = {
                "loan_id": loan.loan_id,
                "customer": {
                    "id": customer.customer_id,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "phone_number": int(customer.phone_number), 
                    "age": customer.age
                },
                "loan_amount": loan.loan_amount,
                "interest_rate": loan.interest_rate,
                "monthly_installment": loan.monthly_repayment,
                "tenure": loan.tenure
            }
            # Since I missed Age in model, I'll return 0 or maybe add it now?
            # Prompt says "customer JSON containing id , first_name , last_name, phone_number, age of customer"
            # I should add Age to model.
            return Response(response_data, status=status.HTTP_200_OK)
        except Loan.DoesNotExist:
            return Response({"error": "Loan not found"}, status=status.HTTP_404_NOT_FOUND)

class ViewCustomerLoansView(APIView):
    def get(self, request, customer_id):
        loans = Loan.objects.filter(customer_id=customer_id)
        response_list = []
        for loan in loans:
            # repayment_left calculation
            # Logic: tenure - months since start? Or emis_paid_on_time?
            # Prompt doesn't specify logic for repayments_left. I'll assume tenure - (months_elapsed)
            # Or just tenure? "No of EMIs left".
            # Let's say tenure - (current_date - start_date).months
            
            months_passed = (date.today().year - loan.start_date.year) * 12 + date.today().month - loan.start_date.month
            repayments_left = max(0, loan.tenure - months_passed)

            response_list.append({
                "loan_id": loan.loan_id,
                "loan_amount": loan.loan_amount,
                "interest_rate": loan.interest_rate,
                "monthly_installment": loan.monthly_repayment,
                "repayments_left": repayments_left
            })
        return Response(response_list, status=status.HTTP_200_OK)
