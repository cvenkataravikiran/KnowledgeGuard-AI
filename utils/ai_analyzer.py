"""AI-powered analysis using Groq API"""
import json
from groq import Groq
from typing import List, Dict, Optional
import config


class AIAnalyzer:
    """AI analyzer using Groq API for knowledge extraction and analysis"""
    
    def __init__(self):
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment variables")
        
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities from text using AI
        
        Returns:
            Dictionary with entity types as keys and lists of entities as values
        """
        prompt = f"""Analyze the following text and extract relevant entities.

Text:
{text[:4000]}

Extract and return a JSON object with the following structure:
{{
    "employees": ["list of employee names mentioned"],
    "departments": ["list of departments"],
    "systems": ["list of systems, applications, or technologies"],
    "projects": ["list of project names"],
    "processes": ["list of business processes or procedures"],
    "clients": ["list of client or customer names"],
    "technologies": ["list of specific technologies, tools, or platforms"]
}}

Only include entities that are explicitly mentioned or clearly implied. Return valid JSON only."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing business documents and extracting structured information. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            entities = json.loads(content)
            
            # Clean and deduplicate
            for key in entities:
                if isinstance(entities[key], list):
                    entities[key] = list(set([e.strip() for e in entities[key] if e.strip()]))
            
            return entities
        
        except Exception as e:
            print(f"Error extracting entities: {str(e)}")
            return {
                "employees": [],
                "departments": [],
                "systems": [],
                "projects": [],
                "processes": [],
                "clients": [],
                "technologies": []
            }
    
    def analyze_documentation_gaps(self, context: str) -> List[Dict]:
        """Identify documentation gaps"""
        prompt = f"""Analyze the following organizational context and identify documentation gaps.

Context:
{context[:3000]}

Identify documentation gaps and return a JSON array with this structure:
[
    {{
        "gap_type": "missing_sop|outdated|incomplete",
        "subject": "name of system/process/project",
        "severity": "critical|high|medium|low",
        "description": "description of the gap",
        "recommendation": "what should be done"
    }}
]

Return valid JSON only."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing organizational knowledge and identifying documentation gaps."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            gaps = json.loads(content)
            return gaps if isinstance(gaps, list) else []
        
        except Exception as e:
            print(f"Error analyzing documentation gaps: {str(e)}")
            return []
    
    def generate_risk_assessment(self, employee_name: str, context: str) -> Dict:
        """Generate risk assessment for employee exit scenario"""
        prompt = f"""Analyze the impact if employee '{employee_name}' leaves the organization.

Context:
{context[:3000]}

Generate a risk assessment and return JSON with this structure:
{{
    "risk_score": 0-100,
    "risk_level": "critical|high|medium|low",
    "affected_systems": ["list of systems"],
    "affected_projects": ["list of projects"],
    "affected_processes": ["list of processes"],
    "knowledge_coverage": 0-100,
    "documented_areas": ["list of well-documented areas"],
    "undocumented_areas": ["list of poorly documented areas"],
    "recovery_estimate_days": number,
    "recommendations": ["list of recommendations"]
}}

Return valid JSON only."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at organizational risk assessment and business continuity planning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            assessment = json.loads(content)
            return assessment
        
        except Exception as e:
            print(f"Error generating risk assessment: {str(e)}")
            return {
                "risk_score": 0,
                "risk_level": "unknown",
                "affected_systems": [],
                "affected_projects": [],
                "affected_processes": [],
                "knowledge_coverage": 0,
                "documented_areas": [],
                "undocumented_areas": [],
                "recovery_estimate_days": 0,
                "recommendations": []
            }
    
    def answer_question(self, question: str, context_documents: List[str]) -> Dict[str, any]:
        """
        Answer question using RAG (Retrieval Augmented Generation)
        
        Returns:
            Dictionary with answer, confidence, and sources
        """
        # Combine context
        context = "\n\n".join(context_documents[:5])  # Use top 5 documents
        
        prompt = f"""Answer the following question based on the provided context.

Context:
{context[:4000]}

Question: {question}

Provide a detailed answer based on the context. If the context doesn't contain enough information, say so.
Also cite which parts of the context you used."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that answers questions based on organizational documents. Always cite your sources."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                "answer": answer,
                "confidence": 0.85,  # Could be enhanced with more sophisticated scoring
                "sources_used": len(context_documents)
            }
        
        except Exception as e:
            return {
                "answer": f"Error generating answer: {str(e)}",
                "confidence": 0.0,
                "sources_used": 0
            }


# Global instance
ai_analyzer = AIAnalyzer()
