import json
import requests
from typing import Dict, Any, List, Optional
import logging
from utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        """Initialize the LLM Service"""
        # In a real application, you would use the GORQ LLM service
        # For demonstration purposes, we're implementing a simplified version
        self.system_prompt = """You are a helpful multilingual loan advisor assistant. Your task is to:
1. Help users understand loan eligibility requirements for different loan types
2. Guide users through the loan application process
3. Provide useful financial literacy tips

Analyze the user's query and determine the intent. Based on the intent, provide relevant information about loans, 
eligibility criteria, application processes, or financial advice. Always be helpful, accurate, and concise.

IMPORTANT: The user query has been translated from their native language to English. 
Your response will be translated back to their language.
"""
        
    def analyze_intent(self, query: str) -> Dict[str, Any]:
        """Analyze the user's intent from their query using keyword matching"""
        intent = {
            "category": "general_inquiry",
            "specific_intent": None,
            "loan_type": None,
            "entities": {},
            "confidence": 0.8
        }
        
        query = query.lower()
        
        # Check for eligibility check intent
        if any(keyword in query for keyword in ["eligible", "eligibility", "qualify", "qualification", "can i get", "am i eligible"]):
            intent["category"] = "eligibility_check"
            
            # Extract loan type if present
            for loan_type in ["home", "personal", "business", "education", "car", "gold", "agriculture", "microfinance"]:
                if loan_type in query or f"{loan_type} loan" in query:
                    intent["loan_type"] = loan_type
                    break
            
            # Extract entities using our entity extraction method
            extracted_entities = self.extract_user_entities(query)
            if extracted_entities:
                intent["entities"] = extracted_entities
        
        # Check for application guidance intent
        elif any(keyword in query for keyword in ["apply", "application", "process", "procedure", "how to get", "documents", "document"]):
            intent["category"] = "application_guidance"
            
            # Extract loan type if present
            for loan_type in ["home", "personal", "business", "education", "car", "gold", "agriculture", "microfinance"]:
                if loan_type in query or f"{loan_type} loan" in query:
                    intent["loan_type"] = loan_type
                    break
        
        # Check for financial literacy intent
        elif any(keyword in query for keyword in ["advice", "tip", "suggestion", "recommend", "improve", "credit score", "saving", "budget"]):
            intent["category"] = "financial_literacy"
            
            # Determine specific financial advice area
            if any(term in query for term in ["credit", "score", "cibil"]):
                intent["specific_intent"] = "credit_score_tips"
            elif any(term in query for term in ["save", "saving", "budget"]):
                intent["specific_intent"] = "saving_tips"
            elif any(term in query for term in ["invest", "investment"]):
                intent["specific_intent"] = "investment_tips"
        
        return intent
    
    def generate_response(self, query: str, language_code: str = "en", user_context: Dict[str, Any] = None) -> str:
        """Generate a response to the user's query"""
        # In a real implementation, this would call the GORQ LLM API
        
        # Analyze intent
        intent = self.analyze_intent(query)
        logger.info(f"Detected intent: {intent}")
        
        # Generate response based on intent
        if intent["category"] == "eligibility_check":
            response = self._handle_eligibility_check(intent, query, user_context)
        elif intent["category"] == "application_guidance":
            response = self._handle_application_guidance(intent, query, user_context)
        elif intent["category"] == "financial_literacy":
            response = self._handle_financial_literacy(intent, query, user_context)
        else:
            # General inquiry
            response = self._handle_general_inquiry(query, user_context)
        
        return response
    
    def _handle_eligibility_check(self, intent: Dict[str, Any], query: str, user_context: Dict[str, Any] = None) -> str:
        """Handle eligibility check intent"""
        from utils.loan_manager import LoanDataManager
        loan_manager = LoanDataManager()
        
        loan_type = intent.get("loan_type")
        if not loan_type:
            # Try to extract from relevant terms
            relevant_loans = loan_manager.get_relevant_loan_data(query)
            if relevant_loans:
                loan_type = list(relevant_loans.keys())[0]
        
        if loan_type:
            loan_details = loan_manager.get_loan_details(loan_type)
            if not loan_details:
                return "I couldn't find information about that specific loan type. Please specify which type of loan you're interested in (e.g., home loan, personal loan, etc.)."
            
            # Collect user data from intent and context
            user_data = {}
            if intent.get("entities"):
                user_data.update(intent["entities"])
            
            if user_context:
                user_data.update(user_context)
            
            # If we have enough data, check eligibility
            if user_data:
                eligibility = loan_manager.check_loan_eligibility(loan_type, user_data)
                
                if eligibility.get("eligible"):
                    response = f"Based on the information provided, you appear to be eligible for a {loan_details['name']}! "
                    response += f"Here's what you need to know:\n\n"
                    response += f"- Interest Rate: {loan_details['interest_rate_range']}\n"
                    response += f"- Loan Amount Range: {loan_details['loan_amount_range']}\n"
                    response += f"- Tenure: {loan_details['tenure_range']}\n\n"
                    
                    response += "Required Documents:\n"
                    for doc in loan_details['documents_required'][:3]:
                        response += f"- {doc}\n"
                    if len(loan_details['documents_required']) > 3:
                        response += "- And more documents based on the lender's requirements\n\n"
                    
                    response += "Would you like me to guide you through the application process?"
                else:
                    response = f"Based on the information provided, you may not be eligible for a {loan_details['name']} at this time. "
                    response += "Here are the factors affecting your eligibility:\n\n"
                    
                    for factor in eligibility.get("factors", []):
                        response += f"- {factor}\n"
                    
                    response += "\nHere are some tips to improve your eligibility:\n"
                    for tip in eligibility.get("tips", []):
                        response += f"- {tip}\n"
            else:
                # Not enough information to determine eligibility
                response = f"To check your eligibility for a {loan_details['name']}, I need some information from you:\n\n"
                response += f"- Your age (should be between {loan_type == 'home' and '21-65' or '21-60'} years)\n"
                response += f"- Your monthly income (minimum requirement varies by loan type)\n"
                response += f"- Your credit score (ideally 650+ for most loans)\n"
                response += f"- Employment status and type\n\n"
                
                response += f"The basic eligibility criteria for a {loan_details['name']} are:\n{loan_details['eligibility']}\n\n"
                response += "Could you please provide this information so I can check your eligibility?"
        else:
            # No loan type specified or extracted
            loan_types = loan_manager.get_loan_types()
            response = "I can help check your eligibility for various loan types. Please specify which type of loan you're interested in:\n\n"
            
            for loan_type in loan_types[:5]:  # Limit to top 5 for brevity
                response += f"- {loan_type['name']}: {loan_type['description']}\n"
            
            response += "\nOnce you let me know which loan you're interested in, I can check your eligibility and provide more details."
        
        return response
    
    def _handle_application_guidance(self, intent: Dict[str, Any], query: str, user_context: Dict[str, Any] = None) -> str:
        """Handle application guidance intent"""
        from utils.loan_manager import LoanDataManager
        loan_manager = LoanDataManager()
        
        loan_type = intent.get("loan_type")
        if not loan_type:
            # Try to extract from relevant terms
            relevant_loans = loan_manager.get_relevant_loan_data(query)
            if relevant_loans:
                loan_type = list(relevant_loans.keys())[0]
        
        if loan_type:
            loan_details = loan_manager.get_loan_details(loan_type)
            if not loan_details:
                return "I couldn't find information about that specific loan type. Please specify which type of loan you're interested in (e.g., home loan, personal loan, etc.)."
            
            response = f"Here's a step-by-step guide to apply for a {loan_details['name']}:\n\n"
            response += "1. **Check Your Eligibility**: Make sure you meet the basic criteria:\n"
            response += f"   {loan_details['eligibility']}\n\n"
            
            response += "2. **Prepare Documents**: You'll need the following documents:\n"
            for doc in loan_details['documents_required']:
                response += f"   - {doc}\n"
            
            response += "\n3. **Compare Lenders**: Consider these popular lenders:\n"
            for lender in loan_details['popular_lenders'][:3]:
                response += f"   - {lender}\n"
            
            response += "\n4. **Application Process**:\n"
            response += "   - Complete the application form (online or at branch)\n"
            response += "   - Submit all required documents\n"
            response += "   - Pay the processing fee\n"
            response += "   - Undergo credit assessment\n"
            
            response += "\n5. **Verification**:\n"
            response += "   - The lender will verify your documents\n"
            response += "   - For secured loans, property/asset valuation will be done\n"
            
            response += "\n6. **Approval & Disbursement**:\n"
            response += "   - After approval, review the loan agreement carefully\n"
            response += "   - Sign the loan agreement\n"
            response += "   - The amount will be disbursed to your account\n\n"
            
            # Add financial tips specific to loan application
            tips = loan_manager.get_financial_tips("application")
            response += "**Financial Tips for Loan Application**:\n"
            for tip in tips[:3]:
                response += f"- {tip}\n"
            
            response += "\nDo you need more specific information about any of these steps?"
        else:
            # No loan type specified or extracted
            loan_types = loan_manager.get_loan_types()
            response = "I can guide you through the application process for various loans. Please specify which type of loan you're interested in:\n\n"
            
            for loan_type in loan_types[:5]:  # Limit to top 5 for brevity
                response += f"- {loan_type['name']}: {loan_type['description']}\n"
            
            response += "\nOnce you let me know which loan you're interested in, I can provide detailed application guidance."
        
        return response
    
    def _handle_financial_literacy(self, intent: Dict[str, Any], query: str, user_context: Dict[str, Any] = None) -> str:
        """Handle financial literacy intent"""
        from utils.loan_manager import LoanDataManager
        loan_manager = LoanDataManager()
        
        specific_intent = intent.get("specific_intent")
        context = specific_intent or query
        
        tips = loan_manager.get_financial_tips(context)
        
        if "credit" in query or specific_intent == "credit_score_tips":
            response = "**Tips to Improve Your Credit Score**:\n\n"
            for tip in tips:
                response += f"- {tip}\n"
            
            response += "\nA good credit score (700+) can help you qualify for better loan terms and lower interest rates. Do you have any specific questions about improving your credit score?"
        
        elif "save" in query or "saving" in query or specific_intent == "saving_tips":
            response = "**Effective Saving Strategies**:\n\n"
            for tip in tips:
                response += f"- {tip}\n"
            
            response += "\nConsistent saving is key to financial stability and achieving your goals. Would you like personalized saving advice based on your financial situation?"
        
        elif "invest" in query or specific_intent == "investment_tips":
            response = "**Investment Tips for Beginners**:\n\n"
            for tip in tips:
                response += f"- {tip}\n"
            
            response += "\nInvesting is essential for long-term wealth building. Remember that all investments carry some risk, so do thorough research before investing."
        
        else:
            response = "**General Financial Literacy Tips**:\n\n"
            for tip in tips:
                response += f"- {tip}\n"
            
            response += "\nGood financial habits can help you achieve your financial goals and prepare for unexpected expenses. Would you like more specific financial advice on a particular topic?"
        
        return response
    
    def _handle_general_inquiry(self, query: str, user_context: Dict[str, Any] = None) -> str:
        """Handle general inquiry"""
        from utils.loan_manager import LoanDataManager
        loan_manager = LoanDataManager()
        
        # Try to extract relevant loan information
        relevant_loans = loan_manager.get_relevant_loan_data(query)
        
        if relevant_loans:
            # User is asking about specific loan types
            loan_id = list(relevant_loans.keys())[0]
            loan_details = relevant_loans[loan_id]
            
            response = f"**{loan_details['name']}**\n\n"
            response += f"{loan_details['description']}\n\n"
            
            response += "**Key Features**:\n"
            response += f"- Interest Rate: {loan_details['interest_rate_range']}\n"
            response += f"- Loan Amount: {loan_details['loan_amount_range']}\n"
            response += f"- Tenure: {loan_details['tenure_range']}\n"
            response += f"- Processing Fee: {loan_details['processing_fee']}\n\n"
            
            response += "**Eligibility**:\n"
            response += f"{loan_details['eligibility']}\n\n"
            
            response += "Would you like to:\n"
            response += "1. Check your eligibility for this loan\n"
            response += "2. Get guidance on the application process\n"
            response += "3. Learn about financial tips related to this loan\n"
            
        else:
            # General loan information
            response = "I'm your multilingual loan advisor assistant. I can help you with:\n\n"
            response += "1. **Loan Eligibility**: Check if you qualify for different types of loans\n"
            response += "2. **Application Guidance**: Get step-by-step guidance for loan applications\n"
            response += "3. **Financial Tips**: Learn helpful financial literacy tips\n\n"
            
            response += "We offer information on various loan types including:\n"
            loan_types = loan_manager.get_loan_types()
            for loan_type in loan_types[:5]:
                response += f"- {loan_type['name']}\n"
            
            response += "\nHow can I assist you today? Feel free to ask in your preferred language!"
        
        return response
    def extract_user_entities(self, text: str) -> Dict[str, Any]:
        """Use LLM capabilities to extract user entities from text"""
        entities = {}
        text = text.lower()
        
        # In a real implementation, this would call the LLM API to extract entities
        # For now, we implement a simple keyword-based approach
        
        # Extract age
        if "age" in text:
            for word in text.split():
                if word.isdigit() and 18 <= int(word) <= 100:
                    # Check if the word "age" is nearby
                    age_index = text.find("age")
                    word_index = text.find(word)
                    if abs(age_index - word_index) < 20:  # If within 20 characters
                        entities["age"] = int(word)
        
        # Extract income
        if any(term in text for term in ["income", "salary", "earn"]):
            words = text.split()
            for i, word in enumerate(words):
                if word.isdigit() and i < len(words) - 1:
                    # Check for k/thousand/lakh indicators
                    if i < len(words) - 1 and "k" in words[i+1].lower():
                        entities["income"] = int(word) * 1000
                    elif i < len(words) - 1 and "thousand" in words[i+1].lower():
                        entities["income"] = int(word) * 1000
                    elif i < len(words) - 1 and "lakh" in words[i+1].lower():
                        entities["income"] = int(word) * 100000
                    else:
                        # If amount seems like a monthly income (between 10,000 and 10,00,000)
                        if 10000 <= int(word) <= 1000000:
                            entities["income"] = int(word)
        
        # Extract credit score
        if any(term in text for term in ["credit", "score", "cibil"]):
            words = text.split()
            for word in words:
                if word.isdigit() and 300 <= int(word) <= 900:
                    entities["credit_score"] = int(word)
        
        # Extract employment type
        if any(term in text for term in ["job", "work", "employment", "profession"]):
            if any(term in text for term in ["business", "self", "entrepreneur"]):
                entities["employment_type"] = "self_employed"
            elif any(term in text for term in ["salaried", "employee"]):
                entities["employment_type"] = "salaried"
        
        return entities