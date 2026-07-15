import singleSelect from "@a2ui-catalog/single_select.json";
import multiSelect from "@a2ui-catalog/multi_select.json";
import datePicker from "@a2ui-catalog/date_picker.json";
import dataTable from "@a2ui-catalog/data_table.json";
import type { A2UITemplateCatalogEntry } from "./types";

export const A2UI_CATALOG: A2UITemplateCatalogEntry[] = [
  singleSelect as A2UITemplateCatalogEntry,
  multiSelect as A2UITemplateCatalogEntry,
  datePicker as A2UITemplateCatalogEntry,
  dataTable as A2UITemplateCatalogEntry,
];
