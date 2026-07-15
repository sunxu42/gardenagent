export interface A2UISampleVariant {
  id: string;
  label: string;
  params: Record<string, unknown>;
}

export interface A2UITemplateCatalogEntry {
  id: string;
  name: string;
  surface_id: string;
  tool_name: string;
  catalog_id: string;
  scenario: string;
  anti_patterns: string[];
  trigger_examples: string[];
  sample_variants: A2UISampleVariant[];
}
