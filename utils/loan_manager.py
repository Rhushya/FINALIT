import os
import json
import re
from typing import Dict, Any, List, Optional
import pandas as pd
from utils.config import settings

class LoanDataManager:
    def __init__(self):
        # Initialize with sample loan data
        # In a production system, this would load from a database or API
        self.loan_data = self._load_sample_loan_data()
        
    def _load_sample_loan_data(self) -> Dict[str, Any]:
        """Load sample loan data for different loan types"""
        # This is a simplified implementation with sample data
        # In a production system, this would load from a database or external API
        
        loan_types = {
            "home": {
                "id": "home",
                "name": "Home Loan",
                "description": "Loans for purchasing, constructing, or renovating residential property.",
                "eligibility": "Indian resident, Age 21-65, Minimum income: ₹25,000/month, Good credit score (700+)",
                "interest_rate_range": "6.5% - 9.5% per annum",
                "processing_fee": "0.5% - 1% of loan amount",
                "loan_amount_range": "₹10 lakhs - ₹5 crores",
                "tenure_range": "5 - 30 years",
                "documents_required": [
                    "Identity proof (Aadhaar, PAN)", 
                    "Address proof", 
                    "Income proof (Salary slips, ITR)", 
                    "Property documents", 
                    "Bank statements (6 months)"
                ],
                "benefits": [
                    "Tax benefits under Section 80C and 24(b)",
                    "Lower interest rates compared to personal loans",
                    "Long repayment tenure",
                    "Option for balance transfer"
                ],
                "popular_lenders": [
                    "State Bank of India", 
                    "HDFC Bank", 
                    "ICICI Bank", 
                    "Axis Bank", 
                    "LIC Housing Finance"
                ]
            },
            "personal": {
                "id": "personal",
                "name": "Personal Loan",
                "description": "Unsecured loans for personal expenses like medical emergencies, travel, or debt consolidation.",
                "eligibility": "Indian resident, Age 21-60, Minimum income: ₹20,000/month, Credit score (650+)",
                "interest_rate_range": "10.5% - 18% per annum",
                "processing_fee": "1% - 3% of loan amount",
                "loan_amount_range": "₹50,000 - ₹40 lakhs",
                "tenure_range": "1 - 5 years",
                "documents_required": [
                    "Identity proof (Aadhaar, PAN)", 
                    "Address proof", 
                    "Income proof (Salary slips, ITR)", 
                    "Bank statements (3 months)"
                ],
                "benefits": [
                    "No collateral required",
                    "Quick disbursement (24-72 hours)",
                    "Flexible usage",
                    "Minimal documentation"
                ],
                "popular_lenders": [
                    "HDFC Bank", 
                    "ICICI Bank", 
                    "Bajaj Finserv", 
                    "Tata Capital", 
                    "State Bank of India"
                ]
            },
            "education": {
                "id": "education",
                "name": "Education Loan",
                "description": "Loans for higher education expenses in India or abroad.",
                "eligibility": "Indian resident, Admission to recognized institution, Co-applicant (parent/guardian)",
                "interest_rate_range": "7.5% - 14% per annum",
                "processing_fee": "0% - 1% of loan amount",
                "loan_amount_range": "Up to ₹75 lakhs for abroad, Up to ₹20 lakhs for India",
                "tenure_range": "5 - 15 years",
                "documents_required": [
                    "Identity proof (Aadhaar, PAN)", 
                    "Address proof", 
                    "Admission letter", 
                    "Course fee structure", 
                    "Academic records", 
                    "Co-applicant documents"
                ],
                "benefits": [
                    "Tax benefits under Section 80E",
                    "Moratorium period during study",
                    "Collateral not required for loans up to ₹7.5 lakhs",
                    "Covers tuition, accommodation, and other expenses"
                ],
                "popular_lenders": [
                    "State Bank of India", 
                    "Bank of Baroda", 
                    "Canara Bank", 
                    "HDFC Credila", 
                    "Axis Bank"
                ]
            },
            "business": {
                "id": "business",
                "name": "Business Loan",
                "description": "Loans for starting or expanding business operations, working capital, or equipment purchase.",
                "eligibility": "Business age: 2+ years, Minimum annual turnover: ₹10 lakhs, Good credit score (700+)",
                "interest_rate_range": "11% - 16% per annum",
                "processing_fee": "1% - 3% of loan amount",
                "loan_amount_range": "₹5 lakhs - ₹5 crores",
                "tenure_range": "1 - 7 years",
                "documents_required": [
                    "Business registration documents", 
                    "GST registration", 
                    "Income Tax Returns (2 years)", 
                    "Bank statements (6 months)", 
                    "Business financial statements"
                ],
                "benefits": [
                    "Collateral not required for smaller amounts",
                    "Flexible repayment options",
                    "Quick disbursement",
                    "Tax benefits on interest paid"
                ],
                "popular_lenders": [
                    "HDFC Bank", 
                    "ICICI Bank", 
                    "State Bank of India", 
                    "Bajaj Finserv", 
                    "Tata Capital"
                ]
            },
            "car": {
                "id": "car",
                "name": "Car Loan",
                "description": "Loans for purchasing new or used cars.",
                "eligibility": "Indian resident, Age 21-65, Minimum income: ₹20,000/month, Good credit score (650+)",
                "interest_rate_range": "7.25% - 12% per annum",
                "processing_fee": "0.5% - 1.5% of loan amount",
                "loan_amount_range": "Up to 90% of car value (new), Up to 80% of car value (used)",
                "tenure_range": "1 - 7 years",
                "documents_required": [
                    "Identity proof (Aadhaar, PAN)", 
                    "Address proof", 
                    "Income proof (Salary slips, ITR)", 
                    "Bank statements (3 months)", 
                    "Car quotation/invoice"
                ],
                "benefits": [
                    "Quick approval and disbursement",
                    "Competitive interest rates",
                    "Flexible repayment options",
                    "Option for balance transfer"
                ],
                "popular_lenders": [
                    "HDFC Bank", 
                    "ICICI Bank", 
                    "State Bank of India", 
                    "Axis Bank", 
                    "Tata Capital"
                ]
            },
            "gold": {
                "id": "gold",
                "name": "Gold Loan",
                "description": "Loans against gold jewelry or ornaments as collateral.",
                "eligibility": "Indian resident, Age 21+, Ownership of gold jewelry/ornaments",
                "interest_rate_range": "7% - 15% per annum",
                "processing_fee": "0% - 1% of loan amount",
                "loan_amount_range": "Up to 75% of gold value",
                "tenure_range": "3 months - 3 years",
                "documents_required": [
                    "Identity proof (Aadhaar, PAN)", 
                    "Address proof", 
                    "Gold jewelry/ornaments"
                ],
                "benefits": [
                    "Quick disbursement (within hours)",
                    "Minimal documentation",
                    "No credit score check",
                    "Lower interest rates compared to personal loans"
                ],
                "popular_lenders": [
                    "Muthoot Finance", 
                    "Manappuram Finance", 
                    "State Bank of India", 
                    "ICICI Bank", 
                    "HDFC Bank"
                ]
            },
            "agriculture": {
                "id": "agriculture",
                "name": "Agriculture Loan",
                "description": "Loans for farmers and agricultural activities like crop production, equipment purchase, or land development.",
                "eligibility": "Farmers, landowners, or agricultural entrepreneurs",
                "interest_rate_range": "7% - 12% per annum (with subsidies as low as 4%)",
                "processing_fee": "0% - 0.5% of loan amount",
                "loan_amount_range": "Varies based on purpose (₹50,000 - ₹50 lakhs)",
                "tenure_range": "1 - 15 years (depending on purpose)",
                "documents_required": [
                    "Identity proof (Aadhaar, PAN)", 
                    "Address proof", 
                    "Land records", 
                    "Crop details", 
                    "Bank statements"
                ],
                "benefits": [
                    "Subsidized interest rates under government schemes",
                    "Flexible repayment aligned with harvest cycles",
                    "Kisan Credit Card facility",
                    "Insurance coverage options"
                ],
                "popular_lenders": [
                    "NABARD", 
                    "State Bank of India", 
                    "Punjab National Bank", 
                    "Bank of Baroda", 
                    "Regional Rural Banks"
                ]
            },
            "microfinance": {
                "id": "microfinance",
                "name": "Microfinance Loan",
                "description": "Small loans for low-income individuals, often for small businesses or income-generating activities.",
                "eligibility": "Low-income individuals, Often women in rural/semi-urban areas, Group lending model",
                "interest_rate_range": "18% - 24% per annum",
                "processing_fee": "1% - 2% of loan amount",
                "loan_amount_range": "₹10,000 - ₹1 lakh",
                "tenure_range": "6 months - 2 years",
                "documents_required": [
                    "Identity proof (Aadhaar)", 
                    "Address proof", 
                    "Group formation documents (if applicable)"
                ],
                "benefits": [
                    "No collateral required",
                    "Weekly/bi-weekly repayment options",
                    "Financial inclusion for underserved populations",
                    "Access to subsequent larger loans with good repayment history"
                ],
                "popular_lenders": [
                    "Bandhan Bank", 
                    "Ujjivan Small Finance Bank", 
                    "Satin Creditcare", 
                    "Spandana Sphoorty", 
                    "Arohan Financial Services"
                ]
            },
            "credit_card": {
                "id": "credit_card",
                "name": "Credit Card",
                "description": "Revolving credit facility for purchases and cash advances.",
                "eligibility": "Indian resident, Age 21-65, Minimum income: ₹15,000/month, Good credit score (650+)",
                "interest_rate_range": "24% - 42% per annum on outstanding balance",
                "processing_fee": "₹0 - ₹1,000 (one-time)",
                "loan_amount_range": "Credit limit: ₹20,000 - ₹10 lakhs (based on profile)",
                "tenure_range": "Revolving credit with minimum monthly payments",
                "documents_required": [
                    "Identity proof (Aadhaar, PAN)", 
                    "Address proof", 
                    "Income proof (Salary slips, ITR)", 
                    "Bank statements (3 months)"
                ],
                "benefits": [
                    "Interest-free period (up to 50 days)",
                    "Reward points and cashback",
                    "EMI conversion facility",
                    "Insurance and travel benefits",
                    "Discounts and offers"
                ],
                "popular_lenders": [
                    "HDFC Bank", 
                    "SBI Card", 
                    "ICICI Bank", 
                    "Axis Bank", 
                    "American Express"
                ]
            }
        }
        
        return loan_types
    
    def get_loan_types(self) -> List[Dict[str, str]]:
        """Get all available loan types"""
        loan_types = []
        for loan_id, loan_data in self.loan_data.items():
            loan_types.append({
                "id": loan_id,
                "name": loan_data["name"],
                "description": loan_data["description"]
            })
        return loan_types
    
    def get_loan_details(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific loan type"""
        return self.loan_data.get(loan_id)
    
    def get_relevant_loan_data(self, query: str) -> Dict[str, Any]:
        """Get loan data relevant to the user's query"""
        # This is a simplified implementation
        # In a production system, this would use more sophisticated NLP techniques
        
        query = query.lower()
        relevant_loans = {}
        
        # Check for specific loan type mentions
        for loan_id, loan_data in self.loan_data.items():
            if loan_id in query or loan_data["name"].lower() in query:
                relevant_loans[loan_id] = loan_data
        
        # Check for related terms
        if not relevant_loans:
            # Home loan related terms
            if any(term in query for term in ["house", "flat", "apartment", "property", "real estate", "home"]):
                relevant_loans["home"] = self.loan_data["home"]
            
            # Personal loan related terms
            if any(term in query for term in ["personal", "emergency", "medical", "wedding", "travel", "vacation"]):
                relevant_loans["personal"] = self.loan_data["personal"]
            
            # Education loan related terms
            if any(term in query for term in ["education", "study", "college", "university", "school", "course", "degree"]):
                relevant_loans["education"] = self.loan_data["education"]
            
            # Business loan related terms
            if any(term in query for term in ["business", "startup", "entrepreneur", "company", "enterprise", "shop"]):
                relevant_loans["business"] = self.loan_data["business"]
            
            # Car loan related terms
            if any(term in query for term in ["car", "vehicle", "automobile", "four wheeler"]):
                relevant_loans["car"] = self.loan_data["car"]
            
            # Gold loan related terms
            if any(term in query for term in ["gold", "jewelry", "ornament"]):
                relevant_loans["gold"] = self.loan_data["gold"]
            
            # Agriculture loan related terms
            if any(term in query for term in ["farm", "agriculture", "crop", "farming", "tractor"]):
                relevant_loans["agriculture"] = self.loan_data["agriculture"]
            
            # Microfinance related terms
            if any(term in query for term in ["micro", "small business", "self help group", "shg", "women entrepreneur"]):
                relevant_loans["microfinance"] = self.loan_data["microfinance"]
            
            # Credit card related terms
            if any(term in query for term in ["credit card", "card", "credit", "cashback", "reward"]):
                relevant_loans["credit_card"] = self.loan_data["credit_card"]
        
        # If still no relevant loans found, return general information about all loans
        if not relevant_loans:
            # Check for general terms
            if any(term in query for term in ["interest", "rate", "emi", "eligibility", "document", "apply"]):
                # Return top 3 popular loan types as a fallback
                relevant_loans = {
                    "home": self.loan_data["home"],
                    "personal": self.loan_data["personal"],
                    "education": self.loan_data["education"]
                }
            else:
                # Return a summary of all loan types
                relevant_loans = {loan_id: loan_data for loan_id, loan_data in list(self.loan_data.items())[:3]}
        
        return relevant_loans
    
    def check_loan_eligibility(self, loan_type: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check eligibility for a specific loan type based on user data"""
        loan_details = self.get_loan_details(loan_type)
        if not loan_details:
            return {"eligible": False, "reason": "Invalid loan type"}
        
        result = {
            "eligible": True,
            "loan_type": loan_details["name"],
            "factors": [],
            "tips": []
        }
        
        # Check age
        if "age" in user_data:
            age = user_data["age"]
            if loan_type == "home" and (age < 21 or age > 65):
                result["eligible"] = False
                result["factors"].append(f"Age: {age} (Required: 21-65)")
                result["tips"].append("You must be between 21-65 years to apply for a home loan.")
            elif loan_type == "personal" and (age < 21 or age > 60):
                result["eligible"] = False
                result["factors"].append(f"Age: {age} (Required: 21-60)")
                result["tips"].append("You must be between 21-60 years to apply for a personal loan.")
        
        # Check income
        if "income" in user_data:
            income = user_data["income"]
            if loan_type == "home" and income < 25000:
                result["eligible"] = False
                result["factors"].append(f"Monthly Income: ₹{income} (Required: ₹25,000+)")
                result["tips"].append("Consider adding a co-applicant to increase the household income.")
            elif loan_type == "personal" and income < 20000:
                result["eligible"] = False
                result["factors"].append(f"Monthly Income: ₹{income} (Required: ₹20,000+)")
                result["tips"].append("Look for specialized personal loans with lower income requirements.")
        
        # Check credit score
        if "credit_score" in user_data:
            credit_score = user_data["credit_score"]
            if loan_type == "home" and credit_score < 700:
                result["eligible"] = False
                result["factors"].append(f"Credit Score: {credit_score} (Required: 700+)")
                result["tips"].append("Work on improving your credit score by paying bills on time and reducing existing debt.")
            elif loan_type == "personal" and credit_score < 650:
                result["eligible"] = False
                result["factors"].append(f"Credit Score: {credit_score} (Required: 650+)")
                result["tips"].append("Consider a secured loan option or improve your credit score.")
        
        # Check employment type for certain loans
        if "employment_type" in user_data:
            emp_type = user_data["employment_type"]
            if loan_type == "business" and emp_type != "self_employed":
                result["factors"].append(f"Employment Type: {emp_type} (Business loans are ideal for self-employed)")
                result["tips"].append("Business loans are primarily for business owners. Consider a personal loan instead.")
        
        # Additional eligibility checks can be added based on loan type and available user data
        
        return result
    
    def get_financial_tips(self, context: str = None) -> List[str]:
        """Get financial literacy tips based on context"""
        general_tips = [
            "Maintain an emergency fund with 3-6 months of expenses.",
            "Invest early for retirement, even small amounts can grow significantly over time.",
            "Pay off high-interest debt before investing in low-return instruments.",
            "Review your credit report regularly and dispute any errors.",
            "Automate your savings to ensure consistency.",
            "Follow the 50/30/20 rule: 50% needs, 30% wants, 20% savings/debt repayment.",
            "Consider term insurance for financial protection.",
            "Diversify your investments across different asset classes.",
            "Compare multiple loan options before finalizing one.",
            "Read and understand all terms before signing loan documents."
        ]
        
        credit_score_tips = [
            "Pay your bills on time to build a good credit history.",
            "Keep your credit card utilization below 30% of your limit.",
            "Don't close old credit accounts, even if unused.",
            "Limit the number of new credit applications.",
            "Check your credit report regularly for errors or fraud."
        ]
        
        loan_application_tips = [
            "Gather all required documents before applying to speed up the process.",
            "Don't apply for multiple loans simultaneously as it can hurt your credit score.",
            "Be honest about your financial situation in your application.",
            "Consider a joint loan application to improve eligibility.",
            "Calculate your EMI beforehand to ensure it's within your budget."
        ]
        
        saving_tips = [
            "Set specific financial goals with timelines.",
            "Use automatic transfers to your savings account on payday.",
            "Track your expenses to identify areas where you can cut back.",
            "Consider tax-saving investment options like PPF or ELSS.",
            "Look for high-interest savings accounts or fixed deposits for short-term goals."
        ]
        
        # Return context-specific tips if context is provided
        if context:
            context = context.lower()
            if any(term in context for term in ["credit", "score", "cibil"]):
                return credit_score_tips
            elif any(term in context for term in ["apply", "application", "document", "loan"]):
                return loan_application_tips
            elif any(term in context for term in ["save", "saving", "budget", "money"]):
                return saving_tips
        
        # Return general tips if no context or no match
        return general_tips 