/**
 * Graph API Service
 * Handles knowledge graph-related API calls
 */

import { ApiService } from './ApiService'
import type { 
  GraphData, 
  GraphStats, 
  EntityListResponse, 
  RelationshipListResponse 
} from '../../types/graph'

export class GraphApi extends ApiService {
  /**
   * Fetch complete graph structure
   * @param maxNodes - Maximum number of nodes to return (default: 500)
   */
  async getFullGraph(maxNodes: number = 500): Promise<GraphData> {
    try {
      const response = await this.get<GraphData>(`/api/graph/graph?max_nodes=${maxNodes}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch graph data:', error)
      throw new Error(`Failed to fetch graph data: ${(error as Error).message}`)
    }
  }

  /**
   * Fetch entities with optional filtering
   * @param limit - Maximum number of entities to return
   * @param entityType - Filter by specific entity type
   */
  async getEntities(
    limit?: number, 
    entityType?: string
  ): Promise<EntityListResponse> {
    try {
      const params = new URLSearchParams()
      if (limit !== undefined) {
        params.append('limit', limit.toString())
      }
      if (entityType) {
        params.append('entity_type', entityType)
      }
      
      const queryString = params.toString()
      const endpoint = queryString ? `/api/graph/entities?${queryString}` : '/api/graph/entities'
      
      const response = await this.get<EntityListResponse>(endpoint)
      return response.data
    } catch (error) {
      console.error('Failed to fetch entities:', error)
      throw new Error(`Failed to fetch entities: ${(error as Error).message}`)
    }
  }

  /**
   * Fetch all relationships
   */
  async getRelationships(): Promise<RelationshipListResponse> {
    try {
      const response = await this.get<RelationshipListResponse>('/api/graph/relationships')
      return response.data
    } catch (error) {
      console.error('Failed to fetch relationships:', error)
      throw new Error(`Failed to fetch relationships: ${(error as Error).message}`)
    }
  }

  /**
   * Fetch graph statistics
   */
  async getStats(): Promise<GraphStats> {
    try {
      const response = await this.get<GraphStats>('/api/graph/stats')
      return response.data
    } catch (error) {
      console.error('Failed to fetch graph statistics:', error)
      throw new Error(`Failed to fetch graph statistics: ${(error as Error).message}`)
    }
  }

  /**
   * Fetch list of unique source document IDs
   */
  async getSourceDocuments(): Promise<string[]> {
    try {
      const response = await this.get<string[]>('/api/graph/sources')
      return response.data
    } catch (error) {
      console.error('Failed to fetch source documents:', error)
      throw new Error(`Failed to fetch source documents: ${(error as Error).message}`)
    }
  }
}

