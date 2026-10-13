'use client';

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import dynamic from 'next/dynamic';
import './graph.css';
import type { GraphCanvasHandle } from '@/components/graph/GraphCanvas';

import { 
  CaseSummary, 
  EntityNode, 
  RelationshipEdge, 
  GraphViewMode, 
  ReviewItem,
  getEntityCategory,
  ENTITY_CATEGORIES 
} from '@/components/graph/types';
import { graphApi } from '@/components/graph/api';
import { GraphWorkspaceHeader } from '@/components/graph/GraphWorkspaceHeader';
import { GraphSidebar } from '@/components/graph/GraphSidebar';
import { GraphToolbar } from '@/components/graph/GraphToolbar';
import { GraphLegend } from '@/components/graph/GraphLegend';
import { EntityDetailsPanel } from '@/components/graph/EntityDetailsPanel';
import { RelationshipDetailsPanel } from '@/components/graph/RelationshipDetailsPanel';
import { DocumentUploadPanel } from '@/components/graph/DocumentUploadPanel';
import { AddEntityModal } from '@/components/graph/AddEntityModal';
import { AddRelationshipModal } from '@/components/graph/AddRelationshipModal';
import { DeleteConfirmModal } from '@/components/graph/DeleteConfirmModal';

// Dynamically import GraphCanvas without SSR (Cytoscape requires browser window/canvas)
const GraphCanvas = dynamic(
  () => import('@/components/graph/GraphCanvas').then((mod) => mod.GraphCanvas),
  { ssr: false }
);

export default function KnowledgeGraphPage() {
  // Cases State
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('');

  // Graph Data State
  const [entities, setEntities] = useState<EntityNode[]>([]);
  const [relationships, setRelationships] = useState<RelationshipEdge[]>([]);
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([]);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState<number | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const canvasRef = useRef<GraphCanvasHandle | null>(null);

  // View & Presentation State
  const [viewMode, setViewMode] = useState<GraphViewMode>('overview');
  const [layoutMode, setLayoutMode] = useState<string>('cose');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>(Object.keys(ENTITY_CATEGORIES));
  const [selectedRelTypes, setSelectedRelTypes] = useState<string[]>([]);
  const [neighborhoodDepth, setNeighborhoodDepth] = useState<number>(0);

  // Modals State
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isAddEntityOpen, setIsAddEntityOpen] = useState(false);
  const [isAddRelationshipOpen, setIsAddRelationshipOpen] = useState(false);
  const [deleteTargetEntity, setDeleteTargetEntity] = useState<EntityNode | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // 1. Initial Load: Fetch Cases
  const refreshCases = useCallback(async () => {
    try {
      const caseList = await graphApi.getCases();
      setCases(caseList);
      if (caseList.length > 0) {
        setSelectedCaseId((prev) => prev || caseList[0].case_id);
      }
    } catch (err: unknown) {
      console.warn('Could not load cases from backend:', err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    async function init() {
      try {
        const caseList = await graphApi.getCases();
        if (!ignore) {
          setCases(caseList);
          if (caseList.length > 0) {
            setSelectedCaseId((prev) => prev || caseList[0].case_id);
          }
        }
      } catch (err: unknown) {
        if (!ignore) {
          console.warn('Could not load cases from backend:', err instanceof Error ? err.message : String(err));
        }
      }
    }
    init();
    return () => {
      ignore = true;
    };
  }, []);

  // 2. Fetch Graph & Review Items when Case Changes
  const refreshCaseData = useCallback(async (caseId: string) => {
    if (!caseId) return;
    setIsLoadingGraph(true);
    setErrorMessage(null);
    setSelectedNodeId(null);
    setSelectedEdgeId(null);

    try {
      const [graphData, reviewList] = await Promise.all([
        graphApi.getCaseGraph(caseId),
        graphApi.getReviewItems(caseId).catch(() => []),
      ]);

      setEntities(graphData.entities || []);
      setRelationships(graphData.relationships || []);
      setReviewItems(reviewList || []);

      const relTypes = Array.from(new Set((graphData.relationships || []).map((r) => r.relationship_type)));
      setSelectedRelTypes(relTypes);

      if (graphData.preferences?.preferred_layout) {
        setLayoutMode(graphData.preferences.preferred_layout as string);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(`Failed to load knowledge graph: ${msg}`);
    } finally {
      setIsLoadingGraph(false);
    }
  }, []);

  useEffect(() => {
    if (!selectedCaseId) return;
    let ignore = false;
    async function fetchCase() {
      setIsLoadingGraph(true);
      try {
        const [graphData, reviewList] = await Promise.all([
          graphApi.getCaseGraph(selectedCaseId),
          graphApi.getReviewItems(selectedCaseId).catch(() => []),
        ]);

        if (!ignore) {
          setEntities(graphData.entities || []);
          setRelationships(graphData.relationships || []);
          setReviewItems(reviewList || []);

          const relTypes = Array.from(new Set((graphData.relationships || []).map((r) => r.relationship_type)));
          setSelectedRelTypes(relTypes);

          if (graphData.preferences?.preferred_layout) {
            setLayoutMode(graphData.preferences.preferred_layout as string);
          }
        }
      } catch (err: unknown) {
        if (!ignore) {
          const msg = err instanceof Error ? err.message : String(err);
          setErrorMessage(`Failed to load knowledge graph: ${msg}`);
        }
      } finally {
        if (!ignore) {
          setIsLoadingGraph(false);
        }
      }
    }
    fetchCase();
    return () => {
      ignore = true;
    };
  }, [selectedCaseId]);

  // 3. Filtered Entities and Relationships based on View Mode, Categories, and Neighborhood Depth
  const filteredData = useMemo(() => {
    let resultEntities = [...entities];

    // Filter by View Mode
    if (viewMode === 'evidence') {
      resultEntities = resultEntities.filter((e) => getEntityCategory(e.entity_type) === 'DOCUMENTARY_EVIDENCE');
    } else if (viewMode === 'people') {
      resultEntities = resultEntities.filter((e) => getEntityCategory(e.entity_type) === 'PARTY_LEGAL_ACTOR');
    } else if (viewMode === 'authorities') {
      resultEntities = resultEntities.filter((e) => getEntityCategory(e.entity_type) === 'LEGAL_SOURCE_NORMATIVE');
    } else if (viewMode === 'timeline') {
      resultEntities = resultEntities.filter((e) => getEntityCategory(e.entity_type) === 'TEMPORAL_EVENT');
    }

    // Filter by Selected Categories
    resultEntities = resultEntities.filter((e) => selectedCategories.includes(getEntityCategory(e.entity_type)));

    // Progressive Neighborhood Depth Filtering if a node is focused
    if (neighborhoodDepth > 0 && selectedNodeId) {
      const hop1Neighbors = new Set<string>([selectedNodeId]);
      relationships.forEach((r) => {
        if (r.source_id === selectedNodeId) hop1Neighbors.add(r.target_id);
        if (r.target_id === selectedNodeId) hop1Neighbors.add(r.source_id);
      });

      if (neighborhoodDepth === 1) {
        resultEntities = resultEntities.filter((e) => hop1Neighbors.has(e.id));
      } else {
        const hop2Neighbors = new Set<string>(hop1Neighbors);
        relationships.forEach((r) => {
          if (hop1Neighbors.has(r.source_id)) hop2Neighbors.add(r.target_id);
          if (hop1Neighbors.has(r.target_id)) hop2Neighbors.add(r.source_id);
        });
        resultEntities = resultEntities.filter((e) => hop2Neighbors.has(e.id));
      }
    }

    const visibleNodeIds = new Set(resultEntities.map((e) => e.id));

    // Filter Relationships (both source and target must be in visible nodes, and rel_type must be checked)
    const resultRelationships = relationships.filter(
      (r) =>
        visibleNodeIds.has(r.source_id) &&
        visibleNodeIds.has(r.target_id) &&
        (selectedRelTypes.length === 0 || selectedRelTypes.includes(r.relationship_type))
    );

    return { entities: resultEntities, relationships: resultRelationships };
  }, [entities, relationships, viewMode, selectedCategories, selectedRelTypes, neighborhoodDepth, selectedNodeId]);

  // Selected Entity and Relationship objects
  const selectedEntity = useMemo(
    () => entities.find((e) => e.id === selectedNodeId) || null,
    [entities, selectedNodeId]
  );

  const selectedRelationship = useMemo(
    () => relationships.find((r) => r.id === selectedEdgeId) || null,
    [relationships, selectedEdgeId]
  );

  const selectedReviewItem = useMemo(() => {
    if (selectedNodeId) {
      return reviewItems.find((r) => r.entity_id === selectedNodeId) || null;
    }
    if (selectedEdgeId) {
      return reviewItems.find((r) => r.relationship_id === selectedEdgeId) || null;
    }
    return null;
  }, [reviewItems, selectedNodeId, selectedEdgeId]);

  // Category Toggle
  const handleToggleCategory = (cat: string) => {
    setSelectedCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  // Relationship Type Toggle
  const handleToggleRelType = (relType: string) => {
    setSelectedRelTypes((prev) =>
      prev.includes(relType) ? prev.filter((r) => r !== relType) : [...prev, relType]
    );
  };

  const handleResetFilters = () => {
    setSelectedCategories(Object.keys(ENTITY_CATEGORIES));
    const allRelTypes = Array.from(new Set(relationships.map((r) => r.relationship_type)));
    setSelectedRelTypes(allRelTypes);
    setSearchQuery('');
    setNeighborhoodDepth(0);
    setViewMode('overview');
  };

  // Search Select & Zoom
  const handleSelectSearchEntity = (entityId: string) => {
    setSelectedNodeId(entityId);
    setFocusNodeId(entityId);
  };

  // Color Customization
  const handleChangeNodeColor = async (hex: string) => {
    if (!selectedNodeId || !selectedCaseId) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      setEntities((prev) =>
        prev.map((e) => (e.id === selectedNodeId ? { ...e, custom_color: hex } : e))
      );

      const existingColors = entities.reduce<Record<string, string>>((acc, ent) => {
        if (ent.custom_color) acc[ent.id] = ent.custom_color;
        return acc;
      }, {});
      existingColors[selectedNodeId] = hex;

      await graphApi.savePreferences(selectedCaseId, { custom_colors: existingColors });
      setLastSavedAt(Date.now());
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : 'Could not save color');
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetNodeColor = async () => {
    if (!selectedNodeId || !selectedCaseId) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      setEntities((prev) =>
        prev.map((e) => (e.id === selectedNodeId ? { ...e, custom_color: undefined } : e))
      );
      const existingColors = entities.reduce<Record<string, string>>((acc, ent) => {
        if (ent.id !== selectedNodeId && ent.custom_color) acc[ent.id] = ent.custom_color;
        return acc;
      }, {});
      await graphApi.savePreferences(selectedCaseId, { custom_colors: existingColors });
      setLastSavedAt(Date.now());
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : 'Could not reset color');
    } finally {
      setIsSaving(false);
    }
  };

  // Notes Persistence
  const handleSaveNotes = async (notes: string) => {
    if (!selectedNodeId || !selectedCaseId) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      await graphApi.saveNotes(selectedCaseId, selectedNodeId, notes);
      setEntities((prev) =>
        prev.map((e) => (e.id === selectedNodeId ? { ...e, user_notes: notes } : e))
      );
      setLastSavedAt(Date.now());
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : 'Could not save notes');
      throw err;
    } finally {
      setIsSaving(false);
    }
  };

  // Progressive Neighborhood Expansion from Backend
  const handleExpandNeighbors = async (nodeId: string) => {
    if (!selectedCaseId) return;
    setIsSaving(true);
    try {
      const neighborData = await graphApi.getNeighbors(selectedCaseId, nodeId);
      const existingEntityIds = new Set(entities.map((e) => e.id));
      const existingRelIds = new Set(relationships.map((r) => r.id));

      const newEntities = (neighborData.neighbors || []).filter(
        (n: EntityNode) => !existingEntityIds.has(n.id)
      );
      const newRels = (neighborData.relationships || []).filter(
        (r: RelationshipEdge) => !existingRelIds.has(r.id)
      );

      if (newEntities.length > 0 || newRels.length > 0) {
        setEntities((prev) => [...prev, ...newEntities]);
        setRelationships((prev) => [...prev, ...newRels]);
      }
      setFocusNodeId(nodeId);
    } catch (err: unknown) {
      console.warn('Neighbor expansion error:', err instanceof Error ? err.message : String(err));
    } finally {
      setIsSaving(false);
    }
  };

  // Human Review Actions
  const handleApproveReview = async (reviewId: string) => {
    setIsSaving(true);
    try {
      const updated = await graphApi.approveReviewItem(reviewId);
      setReviewItems((prev) => prev.map((r) => (r.review_id === reviewId ? updated : r)));
      if (updated.entity_id) {
        setEntities((prev) =>
          prev.map((e) => (e.id === updated.entity_id ? { ...e, trust_status: 'APPROVED' } : e))
        );
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleRejectReview = async (reviewId: string) => {
    setIsSaving(true);
    try {
      const updated = await graphApi.rejectReviewItem(reviewId);
      setReviewItems((prev) => prev.map((r) => (r.review_id === reviewId ? updated : r)));
      if (updated.entity_id) {
        setEntities((prev) =>
          prev.map((e) => (e.id === updated.entity_id ? { ...e, trust_status: 'REJECTED' } : e))
        );
      }
    } finally {
      setIsSaving(false);
    }
  };

  // Entity Creation
  const handleCreateEntity = async (data: {
    canonical_name: string;
    entity_type: string;
    aliases?: string[];
    source_text?: string;
  }) => {
    setIsSaving(true);
    try {
      const created = await graphApi.createEntity(selectedCaseId, data);
      setEntities((prev) => [...prev, created]);
      setSelectedNodeId(created.id);
      setFocusNodeId(created.id);
    } finally {
      setIsSaving(false);
    }
  };

  // Entity Deletion
  const handleConfirmDeleteEntity = async () => {
    if (!deleteTargetEntity || !selectedCaseId) return;
    setIsDeleting(true);
    try {
      await graphApi.deleteEntity(selectedCaseId, deleteTargetEntity.id);
      setEntities((prev) => prev.filter((e) => e.id !== deleteTargetEntity.id));
      setRelationships((prev) =>
        prev.filter((r) => r.source_id !== deleteTargetEntity.id && r.target_id !== deleteTargetEntity.id)
      );
      if (selectedNodeId === deleteTargetEntity.id) {
        setSelectedNodeId(null);
      }
      setDeleteTargetEntity(null);
    } finally {
      setIsDeleting(false);
    }
  };

  // Relationship Creation
  const handleCreateRelationship = async (data: {
    source_id: string;
    target_id: string;
    relationship_type: string;
    source_text?: string;
  }) => {
    setIsSaving(true);
    try {
      const created = await graphApi.createRelationship(selectedCaseId, data);
      setRelationships((prev) => [...prev, created]);
      setSelectedEdgeId(created.id);
    } finally {
      setIsSaving(false);
    }
  };

  // Relationship Deletion
  const handleDeleteRelationship = async (relId: string) => {
    if (!selectedCaseId) return;
    setIsSaving(true);
    try {
      await graphApi.deleteRelationship(selectedCaseId, relId);
      setRelationships((prev) => prev.filter((r) => r.id !== relId));
      if (selectedEdgeId === relId) {
        setSelectedEdgeId(null);
      }
    } finally {
      setIsSaving(false);
    }
  };

  // Layout switcher
  const handleChangeLayout = (newLayout: string) => {
    setLayoutMode(newLayout);
    if (selectedCaseId) {
      graphApi.savePreferences(selectedCaseId, { preferred_layout: newLayout }).catch(() => {});
    }
  };

  // Successful Upload Callback
  const handleUploadSuccess = (caseId: string) => {
    refreshCases();
    setSelectedCaseId(caseId);
    refreshCaseData(caseId);
  };

  return (
    <div className="kg-workspace-container">
      {/* 1. Top Navigation Bar */}
      <GraphWorkspaceHeader
        cases={cases}
        selectedCaseId={selectedCaseId}
        onSelectCase={(cid) => setSelectedCaseId(cid)}
        viewMode={viewMode}
        onChangeViewMode={(mode) => setViewMode(mode)}
        isSaving={isSaving}
        lastSavedAt={lastSavedAt}
        saveError={saveError}
        onOpenUpload={() => setIsUploadOpen(true)}
        onOpenAddEntity={() => setIsAddEntityOpen(true)}
        onOpenAddRelationship={() => setIsAddRelationshipOpen(true)}
      />

      {/* 2. Main 3-Pane Body */}
      <div className="kg-body">
        {/* Left Exploration Sidebar */}
        <GraphSidebar
          entities={entities}
          relationships={relationships}
          searchQuery={searchQuery}
          onSearchChange={(q) => setSearchQuery(q)}
          onSelectSearchEntity={handleSelectSearchEntity}
          selectedCategories={selectedCategories}
          onToggleCategory={handleToggleCategory}
          selectedRelTypes={selectedRelTypes}
          onToggleRelType={handleToggleRelType}
          onResetFilters={handleResetFilters}
          neighborhoodDepth={neighborhoodDepth}
          onChangeDepth={(d) => setNeighborhoodDepth(d)}
        />

        {/* Center Interactive Canvas */}
        <div className="kg-graph-pane">
          {filteredData.entities.length > 0 && <GraphLegend />}

          {isLoadingGraph && entities.length === 0 ? (
            <div className="kg-canvas-state kg-canvas-state--loading">
              <div className="kg-spinner" />
              <span>Loading case graph…</span>
            </div>
          ) : filteredData.entities.length === 0 ? (
            <div className="kg-canvas-state">
              <h2 className={errorMessage ? 'kg-canvas-state-title kg-canvas-state-title--error' : 'kg-canvas-state-title'}>
                {errorMessage ? 'Could not load graph' : 'Nothing to show in this view'}
              </h2>
              <p className="kg-canvas-state-body">
                {errorMessage
                  ? errorMessage
                  : entities.length === 0
                  ? 'This case has no extracted entities yet. Upload a document to build the graph from your source material.'
                  : 'Filters are hiding every node. Reset filters to see the full case graph again.'}
              </p>
              <div className="kg-canvas-state-actions">
                {entities.length === 0 ? (
                  <button type="button" className="kg-btn-primary" onClick={() => setIsUploadOpen(true)}>
                    Upload document
                  </button>
                ) : (
                  <button type="button" className="kg-btn-secondary" onClick={handleResetFilters}>
                    Show full graph
                  </button>
                )}
              </div>
            </div>
          ) : (
            <>
              <GraphCanvas
                onMount={(handle) => {
                  canvasRef.current = handle;
                }}
                onUnmount={() => {
                  canvasRef.current = null;
                }}
                entities={filteredData.entities}
                relationships={filteredData.relationships}
                selectedNodeId={selectedNodeId}
                selectedEdgeId={selectedEdgeId}
                onSelectNode={(id) => setSelectedNodeId(id)}
                onSelectEdge={(id) => setSelectedEdgeId(id)}
                onDoubleTapNode={handleExpandNeighbors}
                layoutMode={layoutMode}
                focusNodeId={focusNodeId}
              />
              {isLoadingGraph && (
                <div className="kg-canvas-state kg-canvas-state--overlay kg-canvas-state--loading" aria-live="polite">
                  <div className="kg-spinner" />
                  <span>Loading case graph…</span>
                </div>
              )}
            </>
          )}

          <GraphToolbar
            onZoomIn={() => canvasRef.current?.zoomIn()}
            onZoomOut={() => canvasRef.current?.zoomOut()}
            onFitView={() => canvasRef.current?.fitView()}
            onResetView={handleResetFilters}
            layoutMode={layoutMode}
            onChangeLayout={handleChangeLayout}
          />
        </div>

        {/* Right Inspector Panel */}
        {selectedNodeId && (
          <EntityDetailsPanel
            entity={selectedEntity}
            allEntities={entities}
            relationships={relationships}
            reviewItem={selectedReviewItem}
            onClose={() => setSelectedNodeId(null)}
            onApproveReview={handleApproveReview}
            onRejectReview={handleRejectReview}
            onChangeColor={handleChangeNodeColor}
            onResetColor={handleResetNodeColor}
            onSaveNotes={handleSaveNotes}
            onExpandNeighbors={handleExpandNeighbors}
            onOpenEditModal={() => {}}
            onOpenDeleteModal={(ent) => setDeleteTargetEntity(ent)}
          />
        )}

        {selectedEdgeId && !selectedNodeId && (
          <RelationshipDetailsPanel
            relationship={selectedRelationship}
            reviewItem={selectedReviewItem}
            onClose={() => setSelectedEdgeId(null)}
            onDeleteRelationship={handleDeleteRelationship}
            onApproveReview={handleApproveReview}
            onRejectReview={handleRejectReview}
          />
        )}
      </div>

      {/* 3. Modals */}
      {isUploadOpen && (
        <DocumentUploadPanel
          currentCaseId={selectedCaseId}
          onUploadSuccess={handleUploadSuccess}
          onClose={() => setIsUploadOpen(false)}
        />
      )}

      {isAddEntityOpen && (
        <AddEntityModal
          onClose={() => setIsAddEntityOpen(false)}
          onSubmit={handleCreateEntity}
        />
      )}

      {isAddRelationshipOpen && (
        <AddRelationshipModal
          entities={entities}
          defaultSourceId={selectedNodeId || undefined}
          onClose={() => setIsAddRelationshipOpen(false)}
          onSubmit={handleCreateRelationship}
        />
      )}

      {deleteTargetEntity && (
        <DeleteConfirmModal
          entity={deleteTargetEntity}
          onClose={() => setDeleteTargetEntity(null)}
          onConfirm={handleConfirmDeleteEntity}
          isDeleting={isDeleting}
        />
      )}
    </div>
  );
}
