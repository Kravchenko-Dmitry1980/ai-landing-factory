from app.schemas.enrichment import SourceTraceItem
from app.schemas.landing import LLMContractOutput


def normalize_source_trace(items: list) -> list[SourceTraceItem]:
    out: list[SourceTraceItem] = []
    for item in items or []:
        if isinstance(item, SourceTraceItem):
            out.append(item)
            continue
        if isinstance(item, dict) and item.get("field"):
            try:
                out.append(SourceTraceItem.model_validate(item))
            except Exception:
                continue
    return out[:30]


def merge_trace_with_files(
    output: LLMContractOutput,
    filenames: list[str],
) -> list[SourceTraceItem]:
    trace = normalize_source_trace(output.source_trace)
    if trace:
        return trace
    if output.essence and filenames:
        return [
            SourceTraceItem(
                field="essence",
                filename=filenames[0],
                evidence=output.essence[:200],
            )
        ]
    return []
