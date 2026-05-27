export type LandingStylePreset = "minimal" | "corporate" | "tech" | "bold";

export interface LandingBlock {
  key: string;
  title: string;
  content: string;
  bullets: string[];
}

export interface ConfidenceScores {
  title: number;
  client: number;
  team: number;
  stack: number;
  results: number;
}

export interface SourceTraceItem {
  field: string;
  filename: string | null;
  evidence: string;
}

export type PrivacyMode = "local_only" | "hybrid_safe" | "cloud_unsafe_dev";

export type PIIRiskLevel = "low" | "medium" | "high" | "critical" | "unknown";

export type PIIEntityType =
  | "person_name"
  | "email"
  | "phone"
  | "address"
  | "url"
  | "organization"
  | "medical_data"
  | "passport_id"
  | "telegram"
  | "role_person";

export interface PIIEntityPublic {
  type: PIIEntityType;
  placeholder: string;
  confidence: number;
  source_file: string | null;
  detector: string;
  context_preview_redacted: string | null;
}

export interface PIIReportPublic {
  project_id: string;
  has_pii: boolean;
  entities: PIIEntityPublic[];
  redaction_count: number;
  risk_level: PIIRiskLevel;
  privacy_mode: PrivacyMode;
  detectors_used: string[];
  detected_at: string | null;
  expires_at: string | null;
  source_files: string[];
  safe_for_cloud: boolean;
  warnings: string[];
}

export interface PiiSummary {
  has_pii: boolean;
  risk_level: PIIRiskLevel;
  redaction_count: number;
  safe_for_cloud_current_mode: boolean;
  detectors_used: string[];
  warnings: string[];
}

export interface SafeCloudPayloadPreview {
  project_id: string;
  privacy_mode: PrivacyMode;
  safe_for_cloud: boolean;
  unsafe: boolean;
  chars_count: number;
  files: string[];
  preview_text_redacted: string;
  blocked_reason: string | null;
  pii_summary: PiiSummary | null;
  warnings: string[];
}

export interface StoragePolicy {
  ttl_hours: number;
  encrypt_reports: boolean;
  raw_pii_logging: boolean;
  cleanup_enabled: boolean;
  storage_paths: string[];
}

export interface PiiCleanupResponse {
  deleted_reports: number;
  deleted_artifacts: number;
  message: string;
}

export interface PrivacyStatusResponse {
  privacy_mode: PrivacyMode;
  enable_pii_detection: boolean;
  enable_rehydration: boolean;
  llm_enabled: boolean;
  cloud_allowed: boolean;
  cloud_unsafe_warning: boolean;
  storage_policy: StoragePolicy | null;
}

export interface EnrichmentMetadata {
  confidence: ConfidenceScores;
  missing_fields: string[];
  assumptions: string[];
  source_trace: SourceTraceItem[];
  provider: string;
  llm_enabled: boolean;
  fallback_used: boolean;
  enriched_at: string | null;
  privacy_mode?: string | null;
  pii_detected?: boolean;
  pii_redaction_count?: number;
  cloud_payload_safe?: boolean;
  cloud_unsafe_warning?: boolean;
}

export interface LandingModule {
  name: string;
  description: string;
  type: string;
}

export interface TeamMember {
  name: string;
  role: string;
  project_area: string;
  contributions: string[];
}

export interface DetectionResult {
  is_structured_landing: boolean;
  confidence: number;
  detected_sections: string[];
  missing_sections: string[];
  reason: string;
}

export interface ContractCompletenessReport {
  score: number;
  missing_fields: string[];
  weak_fields: string[];
  warnings: string[];
  recommended_action: string;
  complete: boolean;
  export_incomplete: boolean;
}

export type EvidenceCoverage = "missing" | "weak" | "strong";
export type SourceStatus = "used" | "weak" | "ignored" | "empty";

export interface FieldSourceTrace {
  field_name: string;
  source_filename: string;
  location_type: string;
  location_index: number | null;
  reason: string;
  confidence: number;
}

export interface SourceInventoryItem {
  source_id: string;
  filename: string;
  file_type: string;
  char_count: number;
  slide_count: number | null;
  page_count: number | null;
  detected_source_type: string;
  source_role: string;
  confidence: number;
  warnings: string[];
}

export interface FieldEvidence {
  field_name: string;
  confidence: number;
  coverage: EvidenceCoverage;
  selected_texts: string[];
  source_refs: string[];
}

export interface EvidenceAssemblyReport {
  project_id: string | null;
  sources: SourceInventoryItem[];
  total_evidence_items: number;
  fields: Record<string, FieldEvidence>;
  missing_fields: string[];
  weak_fields: string[];
  strong_fields: string[];
  parser_strategy: string;
  confidence: number;
  warnings: string[];
  field_traces: FieldSourceTrace[];
}

export interface EvidenceSourceView {
  source_id: string;
  filename: string;
  file_type: string;
  detected_source_type: string;
  source_role: string;
  evidence_count: number;
  char_count: number;
  slide_count: number | null;
  page_count: number | null;
  status: SourceStatus;
  notes: string[];
}

export interface FieldSourceView {
  field_name: string;
  coverage: EvidenceCoverage;
  confidence: number;
  source_refs: string[];
  reasons: string[];
  selected_snippets: string[];
}

export interface EvidenceVisibility {
  project_id: string;
  parser_mode: string;
  source_count: number;
  evidence_count: number;
  assembly_confidence: number;
  sources: EvidenceSourceView[];
  field_sources: Record<string, FieldSourceView>;
  missing_fields: string[];
  weak_fields: string[];
  strong_fields: string[];
  warnings: string[];
  improvement_hints: string[];
  advanced_diagnostics_enabled?: boolean;
}

export interface TeamReviewSummary {
  total_candidates: number;
  verified_count: number;
  probable_count: number;
  needs_review_count: number;
  rejected_count: number;
  publication_mode: string;
  can_publish_team: boolean;
  warning?: string | null;
}

export interface TeamReviewCandidate {
  id: string;
  raw_name: string;
  display_name: string;
  role?: string | null;
  contributions: string[];
  status: string;
  source: string;
  source_is_ocr: boolean;
  confidence?: number | null;
  warning?: string | null;
}

export interface TeamReviewData {
  project_id: string;
  summary: TeamReviewSummary;
  candidates: TeamReviewCandidate[];
  editable_text: string;
  publication_mode: string;
}

export interface TeamReviewActionResult {
  project_id: string;
  publication_mode: string;
  summary: TeamReviewSummary;
  team_count: number;
}

export interface FidelityMetadata {
  parser_mode: string;
  detection?: DetectionResult | null;
  completeness?: ContractCompletenessReport | null;
  modules: LandingModule[];
  team_structured: TeamMember[];
  tech_stack_grouped: Record<string, string[]>;
  source_count?: number;
  evidence_count?: number;
  source_types?: string[];
  field_sources?: FieldSourceTrace[];
  missing_fields?: string[];
  weak_fields?: string[];
  assembly_confidence?: number;
  evidence_report?: EvidenceAssemblyReport | null;
  team_publication_mode?: string;
  team_review_warning?: string | null;
}

export interface SectionInfo {
  key: string;
  title: string;
  length: number;
  item_count: number;
}

export interface SourceStructureReport {
  parser_mode: string;
  detection: DetectionResult;
  sections: SectionInfo[];
  parser_confidence: number;
  missing_sections: string[];
}

export interface LandingContract {
  project_id: string;
  status: string;
  style: LandingStylePreset;
  title?: string | null;
  client: string | null;
  timeline?: string | null;
  lead?: string | null;
  quote?: string | null;
  goals: string[];
  presentation_style: string | null;
  visual_assets: string[];
  blocks: LandingBlock[];
  enrichment?: EnrichmentMetadata | null;
  fidelity?: FidelityMetadata | null;
  updated_at: string;
  version: number;
}

export interface EnrichmentResponse {
  contract: LandingContract;
  enrichment: EnrichmentMetadata;
  message: string;
}

export interface LandingBlockContent {
  key: string;
  title: string;
  body: string;
  bullets: string[];
}

export interface GeneratedLanding {
  project_id: string;
  style: LandingStylePreset;
  blocks: LandingBlockContent[];
  generated_at: string;
  prompt_version: string;
}

export interface SectionConfidence {
  overall: number;
  factual_grounding: number;
  completeness: number;
}

export interface ArchitectureNode {
  id: string;
  label: string;
  role?: string | null;
  connections: string[];
}

export type DiagramTypeId =
  | "pipeline"
  | "layered"
  | "hub_spoke"
  | "microservices"
  | "dashboard_flow"
  | "research_graph";

export type LayoutStyleId =
  | "vertical_pipeline"
  | "horizontal"
  | "layered"
  | "mesh"
  | "orchestration_map";

export interface TopologyNode {
  id: string;
  label: string;
  node_type: string;
  layer?: string | null;
  confidence: number;
  source: string[];
  inferred: boolean;
}

export interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  label?: string | null;
  flow_type: string;
  confidence: number;
  source_refs: string[];
  inferred: boolean;
}

export interface ArchitectureLayer {
  id: string;
  label: string;
  node_ids: string[];
}

export interface ArchitectureFlow {
  id: string;
  label: string;
  path: string[];
}

export interface ArchitectureTopology {
  diagram_type: DiagramTypeId | string;
  layout: LayoutStyleId | string;
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  layers: ArchitectureLayer[];
  flows: ArchitectureFlow[];
  warnings: string[];
  node_count: number;
  edge_count: number;
  graph_density: number;
  generated_at: string | null;
}

export interface SemanticSection {
  section_type: string;
  semantic_goal: string;
  title: string;
  subtitle?: string | null;
  narrative: string;
  bullets: string[];
  metrics: string[];
  architecture_nodes: ArchitectureNode[];
  risks: string[];
  insights: string[];
  callouts: string[];
  visual_hints: string[];
  confidence: SectionConfidence;
  source_keys: string[];
  missing_data: string[];
  assumptions: string[];
}

export interface SemanticNarrative {
  arc: string;
  problem: string;
  system: string;
  architecture: string;
  modules: string;
  metrics: string;
  roadmap: string;
  tone: string;
}

export interface SemanticSourceTrace {
  field: string;
  section_type: string;
  source_key: string | null;
  evidence: string;
}

export interface SemanticGenerationMetadata {
  provider: string;
  llm_enabled: boolean;
  fallback_used: boolean;
  domain: string;
  layout_preset: string;
  style_profile: string;
  selected_sections: string[];
  missing_fields: string[];
  assumptions: string[];
  hallucination_warnings: string[];
  source_trace: SemanticSourceTrace[];
  privacy_redacted: boolean;
  generated_at: string | null;
  prompt_version: string;
}

export interface GeneratedSemanticLanding {
  project_id: string;
  domain: string;
  layout_preset: string;
  style_profile: string;
  narrative: SemanticNarrative;
  sections: SemanticSection[];
  architecture?: ArchitectureTopology | null;
  metadata: SemanticGenerationMetadata;
  intelligence_domain_profile?: IntelligenceDomainProfile | null;
  system_archetypes?: SystemArchetype[];
  architecture_patterns?: ArchitecturePattern[];
}

export interface IntelligenceDomainProfile {
  primary_domain: string;
  secondary_domains: string[];
  confidence: number;
  evidence: string[];
  warnings: string[];
}

export interface SystemArchetype {
  archetype: string;
  confidence: number;
  reason: string;
  evidence: string[];
}

export interface ArchitecturePattern {
  pattern: string;
  confidence: number;
  detected_from: string;
  evidence: string[];
  related_modules: string[];
}

export interface KnowledgeEntity {
  id: string;
  label: string;
  entity_type: string;
  description: string;
  confidence: number;
  source_fields: string[];
  evidence: string[];
  pii_safe: boolean;
}

export interface ProjectKnowledgeGraph {
  project_id: string;
  domain_profile: IntelligenceDomainProfile;
  system_archetypes: SystemArchetype[];
  architecture_patterns: ArchitecturePattern[];
  entities: KnowledgeEntity[];
  relations: { id: string; source_id: string; target_id: string; relation_type: string; confidence: number; inferred: boolean }[];
  risks: string[];
  metrics: string[];
  constraints: string[];
  recommendations: string[];
  missing_knowledge: string[];
  confidence_summary: {
    overall: number;
    domain: number;
    archetype: number;
    patterns: number;
    entities: number;
    relations: number;
  };
}

export interface DomainIntelligenceReport {
  project_id: string;
  status: string;
  graph: ProjectKnowledgeGraph;
  warnings: string[];
  assumptions: string[];
  created_at: string | null;
}

export interface UnifiedGenerateResponse {
  semantic: GeneratedSemanticLanding | null;
  landing: GeneratedLanding;
  architecture: ArchitectureTopology | null;
  message: string;
}

export interface ArchitectureResponse {
  project_id: string;
  architecture: ArchitectureTopology | null;
  has_topology: boolean;
}

export interface SemanticDebugResponse {
  semantic: GeneratedSemanticLanding;
  architecture: ArchitectureTopology | null;
  topology_warnings: string[];
}

export interface SemanticGenerationResponse {
  semantic: GeneratedSemanticLanding;
  landing: GeneratedLanding;
  message: string;
}

export interface ProjectResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface UploadResponse {
  project_id: string;
  files: { id: string; original_name: string; kind: string }[];
  message: string;
  pii_summary?: PiiSummary | null;
}
