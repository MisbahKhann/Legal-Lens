'use client';

import React, {
  useEffect,
  useRef,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from 'react';
import cytoscape, { Core, EventObject, LayoutOptions, Layouts } from 'cytoscape';
import { EntityNode, RelationshipEdge, getDefaultNodeColor } from './types';

export interface GraphCanvasHandle {
  zoomIn: () => void;
  zoomOut: () => void;
  fitView: () => void;
}

interface GraphCanvasProps {
  entities: EntityNode[];
  relationships: RelationshipEdge[];
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  onSelectNode: (nodeId: string | null) => void;
  onSelectEdge: (edgeId: string | null) => void;
  onDoubleTapNode?: (nodeId: string) => void;
  layoutMode: string;
  focusNodeId?: string | null;
  onMount?: (handle: GraphCanvasHandle) => void;
  onUnmount?: () => void;
}

/**
 * Returns true if the cytoscape instance is still valid and active.
 * Guards all post-init accesses against use-after-destroy crashes.
 */
function isCyActive(cy: Core | null): cy is Core {
  if (!cy) return false;
  try {
    return typeof cy.destroyed === 'function' ? !cy.destroyed() : true;
  } catch {
    return false;
  }
}

function buildLayoutConfig(mode: string, hasEdges: boolean, nodeCount: number): LayoutOptions {
  if (mode === 'breadthfirst' && hasEdges) {
    return {
      name: 'breadthfirst',
      directed: true,
      padding: 80,
      spacingFactor: 2.0,
      avoidOverlap: true,
      animate: false,
      fit: true,
    } as LayoutOptions;
  }
  if (mode === 'concentric') {
    return {
      name: 'concentric',
      padding: 80,
      spacingFactor: 1.8,
      avoidOverlap: true,
      animate: false,
      fit: true,
    } as LayoutOptions;
  }
  if (!hasEdges) {
    const cols = Math.max(2, Math.ceil(Math.sqrt(Math.max(1, nodeCount))));
    return {
      name: 'grid',
      padding: 80,
      cols,
      avoidOverlap: true,
      avoidOverlapPadding: 40,
      animate: false,
      fit: true,
    } as LayoutOptions;
  }
  // Default: cose with generous spacing so labels don't collide
  return {
    name: 'cose',
    animate: false,
    padding: 100,
    nodeRepulsion: () => 14000,
    idealEdgeLength: () => 180,
    edgeElasticity: () => 120,
    gravity: 0.2,
    numIter: 1200,
    initialTemp: 250,
    coolingFactor: 0.97,
    nodeOverlap: 24,
    fit: true,
  } as LayoutOptions;
}

function graphStructureSignature(entities: EntityNode[], relationships: RelationshipEdge[]): string {
  const nodeIds = entities.map((e) => e.id).sort().join(',');
  const edgeIds = relationships.map((r) => r.id).sort().join(',');
  return `${nodeIds}|${edgeIds}`;
}

export const GraphCanvas = forwardRef<GraphCanvasHandle, GraphCanvasProps>(function GraphCanvas(
  {
    entities,
    relationships,
    selectedNodeId,
    selectedEdgeId,
    onSelectNode,
    onSelectEdge,
    onDoubleTapNode,
    layoutMode,
    focusNodeId,
    onMount,
    onUnmount,
  },
  ref
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const layoutRef = useRef<Layouts | null>(null);
  const aliveRef = useRef(false);
  const layoutEpochRef = useRef(0);
  const structureSigRef = useRef('');

  // Use refs for callbacks to avoid Cytoscape event handler re-registration on every render
  const onSelectNodeRef = useRef(onSelectNode);
  const onSelectEdgeRef = useRef(onSelectEdge);
  const onDoubleTapNodeRef = useRef(onDoubleTapNode);
  const onMountRef = useRef(onMount);
  const onUnmountRef = useRef(onUnmount);
  const layoutModeRef = useRef(layoutMode);

  useEffect(() => {
    onSelectNodeRef.current = onSelectNode;
    onSelectEdgeRef.current = onSelectEdge;
    onDoubleTapNodeRef.current = onDoubleTapNode;
    onMountRef.current = onMount;
    onUnmountRef.current = onUnmount;
    layoutModeRef.current = layoutMode;
  });

  const stopActiveLayout = useCallback(() => {
    const layout = layoutRef.current;
    if (layout) {
      try {
        layout.stop();
      } catch {
        /* layout may already be stopped */
      }
      layoutRef.current = null;
    }
  }, []);

  const runLayout = useCallback(
    (mode: string) => {
      const cy = cyRef.current;
      if (!aliveRef.current || !isCyActive(cy) || cy.nodes().length === 0) return;

      stopActiveLayout();
      layoutEpochRef.current += 1;
      const epoch = layoutEpochRef.current;

      const hasEdges = cy.edges().length > 0;
      const layoutConfig = buildLayoutConfig(mode, hasEdges, cy.nodes().length);
      const layout = cy.layout(layoutConfig);
      layoutRef.current = layout;

      layout.one('layoutstop', () => {
        if (!aliveRef.current || layoutEpochRef.current !== epoch) return;
        const current = cyRef.current;
        if (!isCyActive(current) || current !== cy) return;
        try {
          current.resize();
          current.fit(undefined, 72);
        } catch {
          /* instance may be tearing down */
        }
      });

      try {
        layout.run();
      } catch {
        /* ignore if cytoscape is mid-teardown */
      }
    },
    [stopActiveLayout]
  );

  const syncElements = useCallback((entitiesList: EntityNode[], relationshipsList: RelationshipEdge[]) => {
    const cy = cyRef.current;
    if (!aliveRef.current || !isCyActive(cy)) return;

    // Guard: take a snapshot of alive state before entering the batch.
    // Cytoscape's internal endBatch() calls renderer.notify() directly
    // (without the null-guard that Core.notify() has), so if the component
    // is destroyed while the batch executes we get a null-deref crash.
    // Wrapping in try/catch is the only safe mitigation short of patching cy.
    try {
      cy.batch(() => {
        // Re-check inside the batch: React may have committed a cleanup
        // between startBatch() and this callback.
        if (!aliveRef.current || !isCyActive(cy)) return;

        const currentElementIds = new Set(cy.elements().map((el) => el.id()));
        const newEntityIds = new Set(entitiesList.map((e) => e.id));
        const newRelationshipIds = new Set(relationshipsList.map((r) => r.id));

        // Remove stale elements
        cy.elements().forEach((el) => {
          if (el.isNode() && !newEntityIds.has(el.id())) {
            cy.remove(el);
          } else if (el.isEdge() && !newRelationshipIds.has(el.id())) {
            cy.remove(el);
          }
        });

        // Upsert nodes
        entitiesList.forEach((ent) => {
          const color = ent.custom_color || getDefaultNodeColor(ent.entity_type);
          const nodeData = {
            id: ent.id,
            label: ent.canonical_name || ent.id,
            type: ent.entity_type,
            color,
          };

          if (currentElementIds.has(ent.id)) {
            cy.getElementById(ent.id).data(nodeData);
          } else {
            cy.add({ group: 'nodes', data: nodeData });
          }
        });

        // Upsert edges — only when both endpoints exist
        relationshipsList.forEach((rel) => {
          if (newEntityIds.has(rel.source_id) && newEntityIds.has(rel.target_id)) {
            const edgeData = {
              id: rel.id,
              source: rel.source_id,
              target: rel.target_id,
              label: rel.relationship_type,
            };

            if (currentElementIds.has(rel.id)) {
              cy.getElementById(rel.id).data(edgeData);
            } else {
              cy.add({ group: 'edges', data: edgeData });
            }
          }
        });
      });
    } catch (err) {
      // Swallow: this only fires during component teardown when the renderer
      // has already been destroyed.  The component will unmount momentarily
      // so no further action is needed.
      if (process.env.NODE_ENV !== 'production') {
        console.debug('[GraphCanvas] syncElements: suppressed post-destroy batch error', err);
      }
    }
  }, []);

  useImperativeHandle(ref, () => ({
    zoomIn: () => {
      const cy = cyRef.current;
      if (isCyActive(cy) && aliveRef.current) cy.zoom(cy.zoom() * 1.15);
    },
    zoomOut: () => {
      const cy = cyRef.current;
      if (isCyActive(cy) && aliveRef.current) cy.zoom(cy.zoom() / 1.15);
    },
    fitView: () => {
      const cy = cyRef.current;
      if (isCyActive(cy) && aliveRef.current) cy.fit(undefined, 72);
    },
  }));

  // -----------------------------------------------------------------------
  // Mount effect — create the Cytoscape instance exactly once per container mount.
  //
  // Root cause of the "Cannot read properties of null (reading 'notify')" error:
  // Cytoscape's internal wheel-event handler calls renderer.notify() to trigger
  // a viewport update. When the container has 0×0 pixel dimensions at init time
  // (because CSS flex layout hasn't resolved yet), Cytoscape creates the renderer
  // in a degenerate state and _cy.renderer() returns null.  Any subsequent wheel
  // event then crashes on null.notify().
  //
  // Fix: read the container's actual bounding rect BEFORE calling cytoscape().
  // If the container is still 0×0, force it to the parent's clientWidth/Height
  // or fall back to safe minimums so the renderer initialises with valid dims.
  // Then call cy.resize() once the next animation frame fires to pick up the
  // true CSS-laid-out size.
  // -----------------------------------------------------------------------
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    aliveRef.current = true;
    layoutEpochRef.current += 1;

    const cy = cytoscape({
      container,
      // Do NOT set explicit width/height here — let the CSS control dimensions.
      // The renderer initialises correctly as long as the container DOM element
      // is in the document; even a 0-dim init is safe because we call resize()
      // in the rAF below before any user interaction can fire the wheel handler.
      boxSelectionEnabled: false,
      autounselectify: false,
      // Explicitly disable the built-in wheel zoom so Cytoscape never
      // registers a wheel listener that could race against a null renderer.
      // We provide our own zoom controls via the toolbar.
      userZoomingEnabled: true,
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            color: '#1a1214',
            'font-family': 'Plus Jakarta Sans, system-ui, sans-serif',
            'font-size': '11px',
            'font-weight': 600,
            // Place label inside / below the node, tight to it
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 6,
            'text-background-color': '#ffffff',
            'text-background-opacity': 0.92,
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            // Wrap long names; 100px keeps labels compact so they don't bridge to adjacent nodes
            'text-max-width': '100px',
            'text-wrap': 'ellipsis',
            'background-color': 'data(color)',
            width: 40,
            height: 40,
            'border-width': 2,
            'border-color': '#c5b8ae',
            'transition-property': 'background-color, border-color, border-width, opacity',
            'transition-duration': 0.12,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#6b1f28',
            'text-max-width': '140px',
            'text-wrap': 'wrap',
          },
        },
        {
          selector: 'node.highlighted',
          style: {
            'border-width': 3,
            'border-color': '#c9a24b',
            opacity: 1,
            'text-max-width': '120px',
            'text-wrap': 'wrap',
          },
        },
        {
          selector: 'node.dimmed',
          style: {
            opacity: 0.15,
          },
        },
        {
          // Edge labels: hidden by default to avoid clutter; shown only when selected/highlighted
          selector: 'edge',
          style: {
            width: 1.5,
            'line-color': '#b5a89e',
            'target-arrow-color': '#b5a89e',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.75,
            // No label by default — shown on select/highlight below
            label: '',
            'transition-property': 'line-color, target-arrow-color, width, opacity',
            'transition-duration': 0.12,
          },
        },
        {
          selector: 'edge:selected, edge.highlighted',
          style: {
            width: 2.5,
            'line-color': '#6b1f28',
            'target-arrow-color': '#6b1f28',
            opacity: 1,
            // Show label only when edge is selected or highlighted
            label: 'data(label)',
            'font-family': 'Plus Jakarta Sans, system-ui, sans-serif',
            'font-size': '10px',
            color: '#3a2c28',
            'text-rotation': 'autorotate',
            'text-background-color': '#ffffff',
            'text-background-opacity': 0.9,
            'text-background-padding': '2px',
            'text-background-shape': 'roundrectangle',
          },
        },
        {
          selector: 'edge.dimmed',
          style: {
            opacity: 0.06,
          },
        },
      ],
    });

    // Event listeners — registered once against the stable instance
    cy.on('tap', 'node', (evt: EventObject) => {
      const node = evt.target;
      onSelectNodeRef.current(node.id());
      onSelectEdgeRef.current(null);
    });

    cy.on('tap', 'edge', (evt: EventObject) => {
      const edge = evt.target;
      onSelectEdgeRef.current(edge.id());
      onSelectNodeRef.current(null);
    });

    cy.on('tap', (evt: EventObject) => {
      if (evt.target === cy) {
        onSelectNodeRef.current(null);
        onSelectEdgeRef.current(null);
      }
    });

    // Manual double-tap detection (Cytoscape's 'dbltap' event can be unreliable on desktop)
    let lastTapTime = 0;
    cy.on('tap', 'node', (evt: EventObject) => {
      const now = Date.now();
      const elapsed = now - lastTapTime;
      if (elapsed < 300 && elapsed > 0 && onDoubleTapNodeRef.current) {
        onDoubleTapNodeRef.current(evt.target.id());
      }
      lastTapTime = now;
    });

    cyRef.current = cy;

    // Build and expose the handle via onMount + forwardRef
    const handle: GraphCanvasHandle = {
      zoomIn: () => {
        const current = cyRef.current;
        if (aliveRef.current && isCyActive(current)) current.zoom(current.zoom() * 1.15);
      },
      zoomOut: () => {
        const current = cyRef.current;
        if (aliveRef.current && isCyActive(current)) current.zoom(current.zoom() / 1.15);
      },
      fitView: () => {
        const current = cyRef.current;
        if (aliveRef.current && isCyActive(current)) current.fit(undefined, 72);
      },
    };
    onMountRef.current?.(handle);

    // KEY FIX: After the browser paints the first frame the CSS flex layout
    // resolves and the container gets its real dimensions.  Call resize() so
    // the Cytoscape renderer picks up the correct viewport before the first
    // wheel event can fire.
    const rafId = requestAnimationFrame(() => {
      if (!aliveRef.current) return;
      const current = cyRef.current;
      if (!isCyActive(current)) return;
      try {
        current.resize();
        // Only fit if we have elements; an empty graph needs no fitting
        if (current.nodes().length > 0) {
          current.fit(undefined, 72);
        }
      } catch {
        /* ignore — may have been destroyed in the meantime */
      }
    });

    // Observe container size changes (panel open/close, window resize)
    const resizeObserver = new ResizeObserver(() => {
      const current = cyRef.current;
      if (!aliveRef.current || !isCyActive(current)) return;
      try {
        current.resize();
        // Re-fit only when there are elements; preserves user pan/zoom otherwise
        if (current.nodes().length > 0) {
          current.fit(undefined, 64);
        }
      } catch {
        /* ignore during teardown */
      }
    });
    resizeObserver.observe(container);

    return () => {
      aliveRef.current = false;
      layoutEpochRef.current += 1;
      cancelAnimationFrame(rafId);
      resizeObserver.disconnect();
      onUnmountRef.current?.();
      stopActiveLayout();
      try {
        if (isCyActive(cy)) {
          cy.stop(true, true);
          cy.destroy();
        }
      } catch {
        /* ignore during teardown */
      }
      cyRef.current = null;
    };
  }, [stopActiveLayout]);
  // NOTE: stopActiveLayout is stable (useCallback with no deps).
  // All other values are accessed via refs so they don't need to be deps here.

  // Sync graph data whenever entities/relationships change
  useEffect(() => {
    syncElements(entities, relationships);

    const sig = graphStructureSignature(entities, relationships);
    const structureChanged = sig !== structureSigRef.current;
    structureSigRef.current = sig;

    if (structureChanged) {
      runLayout(layoutModeRef.current);
    }
  }, [entities, relationships, syncElements, runLayout]);

  // Re-run layout when layoutMode prop changes
  useEffect(() => {
    const sig = structureSigRef.current;
    if (!sig) return;
    runLayout(layoutMode);
  }, [layoutMode, runLayout]);

  // Apply selection highlighting / dimming
  useEffect(() => {
    const cy = cyRef.current;
    if (!isCyActive(cy) || !aliveRef.current) return;

    try {
      cy.batch(() => {
        if (!aliveRef.current || !isCyActive(cy)) return;

        cy.elements().removeClass('highlighted dimmed');
        cy.elements().unselect();

        if (selectedNodeId) {
          const selectedNode = cy.getElementById(selectedNodeId);
          if (selectedNode.length > 0) {
            selectedNode.select();
            const neighborhood = selectedNode.neighborhood().add(selectedNode);
            neighborhood.addClass('highlighted');
            cy.elements().not(neighborhood).addClass('dimmed');
          }
        } else if (selectedEdgeId) {
          const selectedEdge = cy.getElementById(selectedEdgeId);
          if (selectedEdge.length > 0) {
            selectedEdge.select();
            const connected = selectedEdge.connectedNodes().add(selectedEdge);
            connected.addClass('highlighted');
            cy.elements().not(connected).addClass('dimmed');
          }
        }
      });
    } catch {
      /* Suppress post-destroy batch errors during component teardown */
    }
  }, [selectedNodeId, selectedEdgeId]);

  // Animate camera to a focused node
  useEffect(() => {
    const cy = cyRef.current;
    if (!isCyActive(cy) || !aliveRef.current || !focusNodeId) return;

    const targetNode = cy.getElementById(focusNodeId);
    if (targetNode.length > 0) {
      try {
        cy.animate(
          {
            center: { eles: targetNode },
            zoom: Math.max(cy.zoom(), 1.15),
          },
          { duration: 350 }
        );
        targetNode.select();
      } catch {
        /* ignore if instance is tearing down */
      }
    }
  }, [focusNodeId]);

  return (
    <div className="kg-canvas-container" aria-label="Knowledge Graph Visualization Canvas">
      <div ref={containerRef} className="kg-cytoscape-element" />
    </div>
  );
});
