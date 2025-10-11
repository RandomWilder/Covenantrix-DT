# Market Research Agent Integration - Product Brief

## 1. Project Overview

Integration of the Market Research Agent into the Covenantrix AI Assistant chat interface, enabling conversational rental property analysis with global market data. Users interact with the agent through natural language in the chat panel, where it queries already-processed documents via LightRAG, fetches real-time market data from external sources, and provides contextualized rent recommendations with confidence scoring.

**Scope:** Complete agent lifecycle implementation including data access layer (LightRAG integration), external data integration (Numbeo/OSM/Eurostat), chat-based agent selection, and conversational task execution.

**Geographic Focus:** Global coverage with European emphasis, including US markets.

## 2. Primary Benefits & Features

### Core Features
- **Automated Rent Analysis:** Extract property details from uploaded lease documents and compare against current market rates
- **Multi-Source Market Data:** Aggregate data from Numbeo (500+ global cities), Eurostat (EU statistics), and OpenStreetMap (geocoding)
- **Confidence Scoring:** Rate recommendation reliability based on data quality and availability (0.5-0.9 confidence range)
- **Contextual Recommendations:** Factor in property size, location, bedrooms, and local market trends

### Business Benefits
- **Global Reliability:** Real, validated data from official APIs—no web scraping fragility
- **Market Intelligence:** Cross-reference property against 500+ cities worldwide
- **Legal Compliance:** API-based approach eliminates ToS/scraping legal risks
- **Maintainability:** Stable API interfaces reduce maintenance overhead vs. scraping solutions

## 3. High-Level Architecture

### Backend Architecture (Clean Architecture / DDD)

**Domain Layer:**
- `MarketResearchAgent` (extends `BaseAgent`)
- Agent capabilities and task execution logic
- Business rules for rent calculation and recommendation

**Infrastructure Layer:**
- `AgentDataAccessService` (implements `IAgentDataAccess`)
  - Wraps existing `RAGEngine` and `DocumentService`
  - Queries LightRAG for document content and analytics
  - Provides natural language querying of processed documents
  
- `ExternalDataService` (implements `IExternalDataService`)
  - Numbeo API integration (primary market data)
  - OpenStreetMap Nominatim (address geocoding and validation)
  - Eurostat API (EU housing statistics)
  - Fallback chain with confidence scoring
  - **Street-level granularity:** Fetches market data using both city and street name for neighborhood-specific accuracy

**API Layer:**
- Agent endpoints integrated with ChatService
- Task submission routed through AgentOrchestrator
- RESTful design following existing patterns
- Conversational responses formatted for chat display

### Data Flow (Conversational Agent)
```
User in Chat selects Market Research Agent →
User asks: "Can we raise rent for property in doc-123?" →
ChatService routes to AgentOrchestrator →
MarketResearchAgent receives task →
Agent queries LightRAG for property details from document →
Extract: address, current_rent, size_sqm, bedrooms from RAG response →
Agent calls ExternalDataService with granular location:
  fetch_market_data({"city": "Berlin", "street": "Hauptstraße", "property_type": "apartment"}) →
Agent compares document data vs. market data →
Calculate recommendation with confidence score →
Return conversational response: "Yes, there's a 17% opportunity to raise rent. 
  Current: €1,200/month vs Market average: €1,450/month for similar properties 
  on Hauptstraße, Berlin. Confidence: 0.85"
```

**Key Enhancement:** Agent uses street-level granularity (city + street name) for market data fetching, providing neighborhood-specific accuracy rather than city-wide averages.

### External Dependencies
- **Numbeo API:** Global rent/property price data (free tier: 100 req/day)
- **OpenStreetMap Nominatim:** Free geocoding service
- **Eurostat API:** EU housing statistics (free, unlimited)

### Technology Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic
- **Storage:** JSON-based persistence (existing pattern)
- **Integration:** Async/await for external API calls
- **Frontend:** React/TypeScript with agent selector UI

## 4. Implementation Phases

**Phase 1 (Week 1):** Core infrastructure
- Implement `ExternalDataService` with Numbeo + OSM
- Implement `AgentDataAccessService` 
- Wire dependency injection
- Test with real data

**Phase 2 (Week 2):** Geographic intelligence
- Address normalization and geocoding
- Multi-level fallback (city → region → country)
- Location-based data fetching

**Phase 3 (Week 3):** Multi-source strategy
- Add Eurostat for EU depth
- Implement source priority chain
- Data quality validation

**Phase 4 (Future):** Enhancement
- National API integrations per market
- Response caching strategy
- Performance optimization

## 5. Key Principles

- **No Mock Data:** Real API integration from day one for reliable agent performance
- **Separation of Concerns:** Clean boundaries between domain, infrastructure, and API layers
- **Quality Over Speed:** Prioritize data reliability and agent accuracy over rapid response
- **Graceful Degradation:** Fallback chains ensure partial success when primary sources unavailable
- **Extensibility:** Architecture supports adding new data sources without core changes