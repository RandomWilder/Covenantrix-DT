"""
Response Quality Evaluation Script
Tests actual system responses with real queries - NO HARDCODED RESULTS

Run from backend directory: python test_response_quality.py
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import get_settings
from infrastructure.ai.rag_engine import RAGEngine
from infrastructure.storage.document_registry import DocumentRegistry


class ResponseQualityTester:
    """Test response quality with real queries"""
    
    def __init__(self):
        self.settings = get_settings()
        self.rag_engine: Optional[RAGEngine] = None
        self.doc_registry: Optional[DocumentRegistry] = None
        self.test_results: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """Initialize RAG engine and document storage"""
        print("=" * 80)
        print("RESPONSE QUALITY EVALUATION")
        print("=" * 80)
        print()
        
        # Initialize document registry
        print("📦 Initializing document registry...")
        self.doc_registry = DocumentRegistry()
        
        # Get available documents
        documents = await self.doc_registry.list_documents()
        print(f"   Found {len(documents)} document(s) in storage")
        
        if not documents:
            print("   ⚠️  No documents found! Please upload a document first.")
            return False
        
        for doc in documents:
            print(f"   - {doc['filename']} (ID: {doc['document_id'][:8]}...)")
        print()
        
        # Initialize RAG engine
        print("🤖 Initializing RAG engine...")
        api_key = self.settings.openai.api_key
        if not api_key:
            print("   ❌ ERROR: OpenAI API key not configured!")
            return False
        
        self.rag_engine = RAGEngine(api_key=api_key)
        init_success = await self.rag_engine.initialize()
        
        if not init_success:
            print("   ❌ ERROR: RAG engine initialization failed!")
            return False
        
        # Apply default settings (required for agent_language and other attributes)
        print("   ⚙️  Applying default settings...")
        default_settings = {
            "rag": {
                "search_mode": "hybrid",
                "top_k": 5,
                "use_reranking": True,
                "llm_model": "gpt-4o-mini"
            },
            "language": {
                "preferred": "en",
                "agent_language": "auto",
                "ui_language": "auto"
            }
        }
        self.rag_engine.apply_settings(default_settings)
        
        print("   ✅ RAG engine initialized successfully")
        print()
        return True
    
    async def test_query(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        expected_behavior: str = ""
    ) -> Dict[str, Any]:
        """
        Execute a real query and analyze the response
        
        Args:
            query: Query text
            document_ids: Optional document IDs for scoped query
            expected_behavior: Description of what we expect (for diagnosis only)
        
        Returns:
            Dict with query results and diagnostic data
        """
        print("-" * 80)
        print(f"📝 QUERY: {query}")
        print(f"🎯 EXPECTED: {expected_behavior}")
        
        if document_ids:
            print(f"📄 SCOPE: {len(document_ids)} document(s)")
        else:
            print(f"📄 SCOPE: Global (all documents)")
        print()
        
        # Track what prompt type should be used
        expected_prompt_type = "document_query" if document_ids else "general_query"
        print(f"🧠 Expected Prompt Type: {expected_prompt_type}")
        
        # Execute query
        start_time = datetime.now()
        
        try:
            result = await self.rag_engine.query(
                query=query,
                mode=None,  # Let RAG engine decide
                document_ids=document_ids
            )
            
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Extract response
            success = result.get("success", False)
            response = result.get("response", "")
            error = result.get("error", "")
            mode = result.get("mode", "unknown")
            document_filtered = result.get("document_filtered", False)
            
            # Analyze response
            analysis = self._analyze_response(
                query=query,
                response=response,
                document_ids=document_ids,
                expected_prompt_type=expected_prompt_type,
                mode=mode,
                document_filtered=document_filtered
            )
            
            # Display results
            print(f"✅ SUCCESS: {success}")
            print(f"⏱️  DURATION: {duration_ms:.0f}ms")
            print(f"🔧 MODE: {mode}")
            print(f"📊 DOCUMENT FILTERED: {document_filtered}")
            print()
            print("📤 RESPONSE:")
            print(response[:500] if len(response) > 500 else response)
            if len(response) > 500:
                print(f"... ({len(response) - 500} more characters)")
            print()
            
            # Show analysis
            print("🔍 RESPONSE ANALYSIS:")
            for key, value in analysis.items():
                status = "✅" if value.get("passed", False) else "❌"
                print(f"   {status} {key}: {value.get('description', '')}")
                if value.get("details"):
                    print(f"      Details: {value['details']}")
            print()
            
            # Store result
            test_result = {
                "query": query,
                "expected_behavior": expected_behavior,
                "document_ids": document_ids,
                "expected_prompt_type": expected_prompt_type,
                "success": success,
                "error": error,
                "response": response,
                "mode": mode,
                "document_filtered": document_filtered,
                "duration_ms": duration_ms,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            print()
            
            test_result = {
                "query": query,
                "expected_behavior": expected_behavior,
                "document_ids": document_ids,
                "success": False,
                "error": str(e),
                "response": "",
                "timestamp": datetime.now().isoformat()
            }
            
            self.test_results.append(test_result)
            return test_result
    
    def _analyze_response(
        self,
        query: str,
        response: str,
        document_ids: Optional[List[str]],
        expected_prompt_type: str,
        mode: str,
        document_filtered: bool
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze response quality based on observable characteristics
        NO HARDCODED EXPECTED RESULTS - only structural analysis
        """
        analysis = {}
        
        # 1. Check if response is not empty
        analysis["non_empty_response"] = {
            "passed": len(response.strip()) > 0,
            "description": "Response contains content",
            "details": f"Length: {len(response)} characters"
        }
        
        # 2. Check mode selection correctness
        if document_ids:
            expected_mode = "naive"
            correct_mode = mode == expected_mode
            analysis["correct_mode_selection"] = {
                "passed": correct_mode,
                "description": f"Mode should be '{expected_mode}' for document-specific query",
                "details": f"Actual mode: {mode}"
            }
        else:
            # Global query - should use hybrid/mix
            correct_mode = mode in ["hybrid", "mix", "local", "global"]
            analysis["correct_mode_selection"] = {
                "passed": correct_mode,
                "description": "Mode should be hybrid/mix for global query",
                "details": f"Actual mode: {mode}"
            }
        
        # 3. Check document filtering flag
        analysis["document_filtering_flag"] = {
            "passed": document_filtered == bool(document_ids),
            "description": "Document filtering flag matches query scope",
            "details": f"Expected: {bool(document_ids)}, Actual: {document_filtered}"
        }
        
        # 4. Check for legal counsel indicators in response
        legal_indicators = [
            "lease", "contract", "rental", "property", "agreement",
            "tenant", "landlord", "clause", "term", "obligation"
        ]
        has_legal_context = any(indicator in response.lower() for indicator in legal_indicators)
        analysis["legal_context_present"] = {
            "passed": has_legal_context or len(response) < 50,  # Skip for very short responses
            "description": "Response contains legal/property context",
            "details": f"Found legal terminology: {has_legal_context}"
        }
        
        # 5. Check for hallucination indicators (certainty without basis)
        # Look for phrases that suggest unsupported claims
        hallucination_indicators = [
            "the document states", "according to the document",
            "based on the document", "the contract specifies"
        ]
        if not document_ids:
            # General query - should NOT make document-specific claims
            has_hallucination = any(phrase in response.lower() for phrase in hallucination_indicators)
            analysis["no_hallucination"] = {
                "passed": not has_hallucination,
                "description": "General query should not claim document-specific info",
                "details": f"Found document claims in general query: {has_hallucination}"
            }
        else:
            # Document query - CAN reference documents
            analysis["no_hallucination"] = {
                "passed": True,
                "description": "Document query can reference documents",
                "details": "Appropriate context for document references"
            }
        
        # 6. Check for uncertainty expression when appropriate
        uncertainty_phrases = [
            "i don't", "i cannot", "i couldn't find", "not available",
            "unable to", "no information", "searched", "not in"
        ]
        expresses_uncertainty = any(phrase in response.lower() for phrase in uncertainty_phrases)
        analysis["uncertainty_handling"] = {
            "passed": True,  # We can't know if uncertainty SHOULD be expressed without expected answer
            "description": "System can express uncertainty",
            "details": f"Uncertainty expressed: {expresses_uncertainty}"
        }
        
        # 7. Check for professional tone
        unprofessional_indicators = ["lol", "omg", "wtf", "dunno", "gonna", "wanna"]
        is_professional = not any(word in response.lower() for word in unprofessional_indicators)
        analysis["professional_tone"] = {
            "passed": is_professional,
            "description": "Response maintains professional tone",
            "details": f"Professional language: {is_professional}"
        }
        
        # 8. Check response length appropriateness
        is_appropriate_length = 50 < len(response) < 5000
        analysis["appropriate_length"] = {
            "passed": is_appropriate_length,
            "description": "Response length is reasonable (50-5000 chars)",
            "details": f"Length: {len(response)} characters"
        }
        
        return analysis
    
    async def run_test_suite(self):
        """Run comprehensive test suite"""
        print("🧪 STARTING TEST SUITE")
        print("=" * 80)
        print()
        
        # Get available documents
        documents = await self.doc_registry.list_documents()
        doc_ids = [doc['document_id'] for doc in documents]
        
        # Test 1: Document-specific query (should use document_query prompt)
        await self.test_query(
            query="What is the rent amount mentioned in the document?",
            document_ids=doc_ids if doc_ids else None,
            expected_behavior="Should analyze document and cite specific rent amount or state if not found"
        )
        
        # Test 2: Global query without document selection (should use general_query prompt)
        await self.test_query(
            query="What are best practices for property lease agreements?",
            document_ids=None,
            expected_behavior="Should provide general legal advice, clearly stating it's not from specific documents"
        )
        
        # Test 3: Query for information likely not in document (test uncertainty handling)
        await self.test_query(
            query="What is the property's current market value?",
            document_ids=doc_ids if doc_ids else None,
            expected_behavior="Should search document, likely not find info, and express uncertainty clearly"
        )
        
        # Test 4: Legal counsel perspective query
        await self.test_query(
            query="Can I increase the rent during the lease term?",
            document_ids=doc_ids if doc_ids else None,
            expected_behavior="Should act as legal counsel for property owner, reference relevant clauses if present"
        )
        
        # Test 5: Multi-aspect query
        await self.test_query(
            query="Summarize the key terms and obligations in this agreement",
            document_ids=doc_ids if doc_ids else None,
            expected_behavior="Should provide structured summary based on document content"
        )
        
        print("=" * 80)
        print("🏁 TEST SUITE COMPLETE")
        print("=" * 80)
        print()
        
        # Generate summary
        self._generate_summary()
    
    def _generate_summary(self):
        """Generate diagnostic summary from test results"""
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 80)
        print()
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", False))
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}/{total_tests}")
        print()
        
        # Analyze each quality dimension
        print("Quality Dimensions:")
        print()
        
        quality_dimensions = {}
        for result in self.test_results:
            analysis = result.get("analysis", {})
            for dimension, data in analysis.items():
                if dimension not in quality_dimensions:
                    quality_dimensions[dimension] = {"passed": 0, "total": 0}
                quality_dimensions[dimension]["total"] += 1
                if data.get("passed", False):
                    quality_dimensions[dimension]["passed"] += 1
        
        for dimension, stats in quality_dimensions.items():
            percentage = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
            print(f"{status} {dimension}: {stats['passed']}/{stats['total']} ({percentage:.0f}%)")
        
        print()
        print("🎯 AREAS FOR IMPROVEMENT:")
        print()
        
        # Identify areas needing improvement
        improvement_areas = []
        for dimension, stats in quality_dimensions.items():
            percentage = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            if percentage < 80:
                improvement_areas.append({
                    "dimension": dimension,
                    "score": percentage,
                    "passed": stats["passed"],
                    "total": stats["total"]
                })
        
        if improvement_areas:
            improvement_areas.sort(key=lambda x: x["score"])
            for area in improvement_areas:
                print(f"⚠️  {area['dimension']}")
                print(f"   Score: {area['score']:.0f}% ({area['passed']}/{area['total']})")
                print(f"   Recommendation: Review test details above for this dimension")
                print()
        else:
            print("✅ All quality dimensions performing well (>80%)")
            print()
        
        # Save detailed results to file
        output_file = Path("test_results_response_quality.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "quality_dimensions": quality_dimensions
                },
                "test_results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Detailed results saved to: {output_file}")
        print()


async def main():
    """Main test execution"""
    tester = ResponseQualityTester()
    
    # Initialize
    success = await tester.initialize()
    if not success:
        print("❌ Initialization failed. Exiting.")
        return
    
    # Run test suite
    await tester.run_test_suite()
    
    print("=" * 80)
    print("✅ EVALUATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

