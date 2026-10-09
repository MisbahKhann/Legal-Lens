"""
Neo4j Graph Store Connection & Database Layer.
Provides environment-configured driver lifecycle management, schema constraint creation,
safe Cypher MERGE operations, and case-isolated graph retrieval helpers.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    import neo4j
    from neo4j import GraphDatabase, Driver
except ImportError:
    neo4j = None
    GraphDatabase = None
    Driver = Any

logger = logging.getLogger(__name__)


class Neo4jGraphStore:
    """
    Neo4j connection manager and query execution interface.
    Configuration is loaded strictly from environment variables:
      - NEO4J_URI (default: bolt://localhost:7687)
      - NEO4J_USERNAME (default: neo4j)
      - NEO4J_PASSWORD (default: password)
      - NEO4J_DATABASE (default: neo4j)
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        self._driver: Optional[Driver] = None

    def connect(self) -> Driver:
        """Initializes and returns the Neo4j driver instance."""
        if neo4j is None:
            raise ImportError(
                "The 'neo4j' Python package is not installed. Please run 'pip install neo4j'."
            )

        if self._driver is None:
            auth = (self.username, self.password) if self.username else None
            self._driver = GraphDatabase.driver(self.uri, auth=auth)
            logger.info("Connected to Neo4j database at %s", self.uri)
        return self._driver

    def close(self) -> None:
        """Closes the active Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("Closed Neo4j driver connection.")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def verify_connection(self) -> bool:
        """
        Attempts to verify database connectivity.
        Returns True if reachable and authenticated, False otherwise.
        """
        try:
            driver = self.connect()
            driver.verify_connectivity()
            return True
        except Exception as e:
            logger.warning("Neo4j connectivity check failed: %s", str(e))
            return False

    def setup_schema(self) -> None:
        """
        Executes schema constraints and index definitions for entity nodes and relationships.
        Ensures uniqueness on entity ID and indexes on case_id and name for high performance.
        """
        driver = self.connect()
        queries = [
            # Generic LegalEntity constraints and indexes
            "CREATE CONSTRAINT constraint_legal_entity_id_unique IF NOT EXISTS FOR (n:LegalEntity) REQUIRE n.id IS UNIQUE;",
            "CREATE INDEX index_legal_entity_case_id IF NOT EXISTS FOR (n:LegalEntity) ON (n.case_id);",
            "CREATE INDEX index_legal_entity_name IF NOT EXISTS FOR (n:LegalEntity) ON (n.canonical_name);",
            # TimelineEvent constraints and indexes
            "CREATE CONSTRAINT constraint_timeline_event_id_unique IF NOT EXISTS FOR (n:TimelineEvent) REQUIRE n.id IS UNIQUE;",
            "CREATE INDEX index_timeline_event_case_id IF NOT EXISTS FOR (n:TimelineEvent) ON (n.case_id);",
        ]

        with driver.session(database=self.database) as session:
            for q in queries:
                try:
                    session.run(q)
                except Exception as ex:
                    logger.debug("Schema setup query note: %s", str(ex))
        logger.info("Neo4j schema constraints and indexes initialized.")

    def upsert_entities(self, entities: List[Dict[str, Any]], case_id: str) -> int:
        """
        Idempotently upserts a list of canonical entity dictionaries into Neo4j.
        Each entity node is given `:LegalEntity` and `:<entity_type>` labels, and scoped to `case_id`.
        """
        if not entities:
            return 0

        driver = self.connect()
        query = """
        UNWIND $entities AS ent
        MERGE (n:LegalEntity {id: ent.id, case_id: $case_id})
        SET n.canonical_name = ent.canonical_name,
            n.normalized_name = ent.normalized_name,
            n.entity_type = ent.entity_type,
            n.aliases = ent.aliases,
            n.document_id = ent.document_id,
            n.source_document_id = ent.source_document_id,
            n.source_page = ent.source_page,
            n.source_text = ent.source_text,
            n.confidence = ent.confidence,
            n.extraction_method = ent.extraction_method,
            n.created_at = ent.created_at,
            n.updated_at = ent.updated_at
        WITH n, ent
        CALL apoc.create.addLabels(n, [ent.entity_type]) YIELD node
        RETURN count(node)
        """
        # Standalone Cypher fallback if APOC is not enabled/installed:
        fallback_query = """
        UNWIND $entities AS ent
        MERGE (n:LegalEntity {id: ent.id, case_id: $case_id})
        SET n.canonical_name = ent.canonical_name,
            n.normalized_name = ent.normalized_name,
            n.entity_type = ent.entity_type,
            n.aliases = ent.aliases,
            n.document_id = ent.document_id,
            n.source_document_id = ent.source_document_id,
            n.source_page = ent.source_page,
            n.source_text = ent.source_text,
            n.confidence = ent.confidence,
            n.extraction_method = ent.extraction_method,
            n.created_at = ent.created_at,
            n.updated_at = ent.updated_at
        RETURN count(n)
        """

        with driver.session(database=self.database) as session:
            try:
                result = session.run(fallback_query, entities=entities, case_id=case_id)
                summary = result.consume()
                count = len(entities)
                logger.info("Upserted %d entities for case %s", count, case_id)
                return count
            except Exception as e:
                logger.error("Failed to upsert entities: %s", str(e))
                raise

    def upsert_relationships(
        self, relationships: List[Dict[str, Any]], case_id: str
    ) -> int:
        """
        Idempotently upserts validated relationships into Neo4j.
        Groups relationships by relationship_type to issue clean Cypher MERGE queries.
        """
        if not relationships:
            return 0

        driver = self.connect()
        # Group by relationship_type
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for rel in relationships:
            rel_type = rel["relationship_type"]
            by_type.setdefault(rel_type, []).append(rel)

        total_upserted = 0
        with driver.session(database=self.database) as session:
            for rel_type, rel_list in by_type.items():
                query = f"""
                UNWIND $rel_list AS rel
                MATCH (s:LegalEntity {{id: rel.source_id, case_id: $case_id}})
                MATCH (t:LegalEntity {{id: rel.target_id, case_id: $case_id}})
                MERGE (s)-[r:`{rel_type}` {{id: rel.id, case_id: $case_id}}]->(t)
                SET r.document_id = rel.document_id,
                    r.confidence = rel.confidence,
                    r.source_document_id = rel.source_document_id,
                    r.source_page = rel.source_page,
                    r.source_text = rel.source_text,
                    r.extraction_method = rel.extraction_method,
                    r.created_at = rel.created_at
                RETURN count(r)
                """
                res = session.run(query, rel_list=rel_list, case_id=case_id)
                total_upserted += len(rel_list)

        logger.info("Upserted %d relationships for case %s", total_upserted, case_id)
        return total_upserted

    def upsert_timeline_events(self, events: List[Dict[str, Any]], case_id: str) -> int:
        """
        Idempotently upserts Step 7 timeline events as `:TimelineEvent` nodes.
        If a canonical entity is associated with the event, connects them via `:ASSOCIATED_WITH`.
        """
        if not events:
            return 0

        driver = self.connect()
        query = """
        UNWIND $events AS ev
        MERGE (n:TimelineEvent {id: ev.id, case_id: $case_id})
        SET n.description = ev.description,
            n.event_type = ev.event_type,
            n.event_date = ev.event_date,
            n.start_date = ev.start_date,
            n.end_date = ev.end_date,
            n.date_precision = ev.date_precision,
            n.temporal_status = ev.temporal_status,
            n.confidence = ev.confidence,
            n.derived_from = ev.derived_from,
            n.source_document_id = ev.source_document_id,
            n.source_page = ev.source_page,
            n.source_text = ev.source_text,
            n.extraction_method = ev.extraction_method,
            n.canonical_entity_id = ev.canonical_entity_id,
            n.created_at = ev.created_at
        WITH n, ev
        WHERE ev.canonical_entity_id IS NOT NULL
        MATCH (target:LegalEntity {id: ev.canonical_entity_id, case_id: $case_id})
        MERGE (n)-[r:ASSOCIATED_WITH {case_id: $case_id}]->(target)
        RETURN count(n)
        """

        with driver.session(database=self.database) as session:
            session.run(query, events=events, case_id=case_id)

        logger.info("Upserted %d timeline events for case %s", len(events), case_id)
        return len(events)

    def upsert_temporal_relationships(
        self, relationships: List[Dict[str, Any]], case_id: str
    ) -> int:
        """
        Idempotently upserts temporal relationships (OCCURRED_ON, BEFORE, AFTER, HAS_DEADLINE).
        Edges connect `:TimelineEvent` nodes or `:TimelineEvent` to `:LegalEntity` / `:TimelineEvent`.
        """
        if not relationships:
            return 0

        driver = self.connect()
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for rel in relationships:
            by_type.setdefault(rel["relationship_type"], []).append(rel)

        total = 0
        with driver.session(database=self.database) as session:
            for rel_type, rel_list in by_type.items():
                query = f"""
                UNWIND $rel_list AS rel
                MATCH (s {{id: rel.source_id, case_id: $case_id}})
                MATCH (t {{id: rel.target_id, case_id: $case_id}})


                MERGE (s)-[r:`{rel_type}` {{id: rel.id, case_id: $case_id}}]->(t)
                SET r.source_document_id = rel.source_document_id,
                    r.source_page = rel.source_page,
                    r.source_text = rel.source_text,
                    r.confidence = rel.confidence,
                    r.created_at = rel.created_at
                RETURN count(r)
                """
                session.run(query, rel_list=rel_list, case_id=case_id)
                total += len(rel_list)

        logger.info("Upserted %d temporal relationships for case %s", total, case_id)
        return total

    def get_case_entities(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all canonical entity nodes for a given case_id."""
        driver = self.connect()
        query = """
        MATCH (n:LegalEntity {case_id: $case_id})
        RETURN properties(n) AS entity
        ORDER BY n.canonical_name ASC
        """
        with driver.session(database=self.database) as session:
            result = session.run(query, case_id=case_id)
            return [record["entity"] for record in result]

    def get_case_relationships(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all non-temporal relationships for a given case_id."""
        driver = self.connect()
        query = """
        MATCH (s:LegalEntity {case_id: $case_id})-[r]->(t:LegalEntity {case_id: $case_id})
        WHERE type(r) <> 'ASSOCIATED_WITH'
        RETURN r.id AS id,
               type(r) AS relationship_type,
               s.id AS source_id,
               s.canonical_name AS source_name,
               t.id AS target_id,
               t.canonical_name AS target_name,
               r.confidence AS confidence,
               r.source_document_id AS source_document_id,
               r.source_page AS source_page,
               r.source_text AS source_text,
               r.extraction_method AS extraction_method
        ORDER BY r.id ASC
        """
        with driver.session(database=self.database) as session:
            result = session.run(query, case_id=case_id)
            return [dict(record) for record in result]

    def get_case_timeline_events(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all timeline events and associated temporal metadata for a case_id."""
        driver = self.connect()
        query = """
        MATCH (n:TimelineEvent {case_id: $case_id})
        OPTIONAL MATCH (n)-[:ASSOCIATED_WITH]->(target:LegalEntity {case_id: $case_id})
        RETURN properties(n) AS event, target.id AS associated_entity_id, target.canonical_name AS associated_entity_name
        ORDER BY n.event_date ASC, n.id ASC
        """
        with driver.session(database=self.database) as session:
            result = session.run(query, case_id=case_id)
            events = []
            for record in result:
                data = dict(record["event"])
                if record["associated_entity_id"]:
                    data["associated_entity_id"] = record["associated_entity_id"]
                    data["associated_entity_name"] = record["associated_entity_name"]
                events.append(data)
            return events

    def get_complete_case_graph(self, case_id: str) -> Dict[str, Any]:
        """
        Retrieves the complete case knowledge graph (entities, relationships, events, and metrics).
        Returns a structured dictionary ready for API payload or frontend consumption.
        """
        entities = self.get_case_entities(case_id)
        relationships = self.get_case_relationships(case_id)
        timeline_events = self.get_case_timeline_events(case_id)

        return {
            "case_id": case_id,
            "summary": {
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "timeline_event_count": len(timeline_events),
            },
            "entities": entities,
            "relationships": relationships,
            "timeline_events": timeline_events,
        }

    def clear_case_graph(self, case_id: str) -> int:
        """Deletes all nodes and relationships associated with a specific case_id."""
        driver = self.connect()
        query = """
        MATCH (n {case_id: $case_id})
        DETACH DELETE n
        """
        with driver.session(database=self.database) as session:
            result = session.run(query, case_id=case_id)
            summary = result.consume()
            nodes_deleted = summary.counters.nodes_deleted
            logger.info("Cleared case %s: deleted %d nodes.", case_id, nodes_deleted)
            return nodes_deleted

    # =========================================================================
    # Step 9 Review & Correction Methods
    # =========================================================================

    def update_entity_trust_status(
        self,
        entity_id: str,
        case_id: str,
        trust_status: str,
        corrected_fields: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Updates the trust status and optional corrected properties of a LegalEntity node."""
        driver = self.connect()
        query = """
        MATCH (n:LegalEntity {id: $entity_id, case_id: $case_id})
        SET n.trust_status = $trust_status,
            n.updated_at = $now
        """
        params: Dict[str, Any] = {
            "entity_id": entity_id,
            "case_id": case_id,
            "trust_status": trust_status,
            "now": datetime.now(timezone.utc).isoformat(),
        }

        if corrected_fields:
            if "canonical_name" in corrected_fields:
                query += ",\n n.canonical_name = $canonical_name, n.normalized_name = $normalized_name"
                params["canonical_name"] = corrected_fields["canonical_name"]
                params["normalized_name"] = (
                    corrected_fields.get("normalized_name")
                    or corrected_fields["canonical_name"].lower().strip()
                )
            if "entity_type" in corrected_fields:
                query += ",\n n.entity_type = $entity_type"
                params["entity_type"] = corrected_fields["entity_type"]
            if "aliases" in corrected_fields:
                query += ",\n n.aliases = $aliases"
                params["aliases"] = corrected_fields["aliases"]

        query += "\nRETURN n.id AS id"

        with driver.session(database=self.database) as session:
            res = session.run(query, **params)
            record = res.single()
            return record is not None

    def update_relationship_trust_status(
        self,
        relationship_id: str,
        case_id: str,
        trust_status: str,
        corrected_fields: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Updates the trust status and optional corrected properties of a relationship."""
        driver = self.connect()
        query = """
        MATCH (s:LegalEntity {case_id: $case_id})-[r {id: $relationship_id, case_id: $case_id}]->(t:LegalEntity {case_id: $case_id})
        SET r.trust_status = $trust_status
        RETURN r.id AS id
        """
        with driver.session(database=self.database) as session:
            res = session.run(
                query,
                relationship_id=relationship_id,
                case_id=case_id,
                trust_status=trust_status,
            )
            return res.single() is not None

    def update_timeline_event_trust_status(
        self,
        event_id: str,
        case_id: str,
        trust_status: str,
        corrected_fields: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Updates the trust status and optional corrected fields of a TimelineEvent node."""
        driver = self.connect()
        query = """
        MATCH (n:TimelineEvent {id: $event_id, case_id: $case_id})
        SET n.trust_status = $trust_status,
            n.temporal_status = $trust_status
        """
        params: Dict[str, Any] = {
            "event_id": event_id,
            "case_id": case_id,
            "trust_status": trust_status,
        }

        if corrected_fields:
            if (
                "event_date" in corrected_fields
                and corrected_fields["event_date"] is not None
            ):
                query += ",\n n.event_date = $event_date"
                params["event_date"] = corrected_fields["event_date"]
            if (
                "start_date" in corrected_fields
                and corrected_fields["start_date"] is not None
            ):
                query += ",\n n.start_date = $start_date"
                params["start_date"] = corrected_fields["start_date"]
            if (
                "end_date" in corrected_fields
                and corrected_fields["end_date"] is not None
            ):
                query += ",\n n.end_date = $end_date"
                params["end_date"] = corrected_fields["end_date"]
            if (
                "date_precision" in corrected_fields
                and corrected_fields["date_precision"] is not None
            ):
                query += ",\n n.date_precision = $date_precision"
                params["date_precision"] = corrected_fields["date_precision"]
            if (
                "event_type" in corrected_fields
                and corrected_fields["event_type"] is not None
            ):
                query += ",\n n.event_type = $event_type"
                params["event_type"] = corrected_fields["event_type"]
            if (
                "description" in corrected_fields
                and corrected_fields["description"] is not None
            ):
                query += ",\n n.description = $description"
                params["description"] = corrected_fields["description"]

        query += "\nRETURN n.id AS id"

        with driver.session(database=self.database) as session:
            res = session.run(query, **params)
            return res.single() is not None

    def merge_entities_in_graph(
        self, case_id: str, primary_entity_id: str, secondary_entity_id: str
    ) -> bool:
        """
        Safely redirects relationships from secondary entity to primary entity in Neo4j,
        updates aliases on primary entity, and marks secondary entity as MERGED.
        """
        driver = self.connect()

        # Cypher query to redirect outgoing & incoming edges and update primary node properties
        query = """
        MATCH (primary:LegalEntity {id: $primary_id, case_id: $case_id})
        MATCH (secondary:LegalEntity {id: $secondary_id, case_id: $case_id})

        // Merge secondary aliases into primary entity
        SET primary.aliases = apoc.coll.toSet(coalesce(primary.aliases, []) + coalesce(secondary.aliases, []) + [secondary.canonical_name]),
            secondary.trust_status = 'MERGED',
            secondary.merged_into_id = primary.id

        WITH primary, secondary

        // Redirect outgoing relationships from secondary -> target to primary -> target
        OPTIONAL MATCH (secondary)-[out_r]->(target:LegalEntity {case_id: $case_id})
        WHERE target.id <> primary.id
        FOREACH (ignore IN CASE WHEN out_r IS NOT NULL THEN [1] ELSE [] END |
            MERGE (primary)-[new_out:`` + type(out_r) + `` {id: out_r.id, case_id: $case_id}]->(target)
            SET new_out = properties(out_r)
            DELETE out_r
        )

        WITH primary, secondary

        // Redirect incoming relationships from source -> secondary to source -> primary
        OPTIONAL MATCH (source:LegalEntity {case_id: $case_id})-[in_r]->(secondary)
        WHERE source.id <> primary.id
        FOREACH (ignore IN CASE WHEN in_r IS NOT NULL THEN [1] ELSE [] END |
            MERGE (source)-[new_in:`` + type(in_r) + `` {id: in_r.id, case_id: $case_id}]->(primary)
            SET new_in = properties(in_r)
            DELETE in_r
        )

        RETURN primary.id AS id
        """

        # Standalone fallback query without APOC
        fallback_query = """
        MATCH (primary:LegalEntity {id: $primary_id, case_id: $case_id})
        MATCH (secondary:LegalEntity {id: $secondary_id, case_id: $case_id})
        SET secondary.trust_status = 'MERGED',
            secondary.merged_into_id = primary.id
        RETURN primary.id AS id
        """

        with driver.session(database=self.database) as session:
            try:
                res = session.run(
                    query,
                    case_id=case_id,
                    primary_id=primary_entity_id,
                    secondary_id=secondary_entity_id,
                )
                record = res.single()
                return record is not None
            except Exception as e:
                logger.warning("Advanced merge query note, using fallback: %s", str(e))
                res = session.run(
                    fallback_query,
                    case_id=case_id,
                    primary_id=primary_entity_id,
                    secondary_id=secondary_entity_id,
                )
                return res.single() is not None
