from typing import Dict, Optional

from .base import PromptTemplateConfig
from .t_slip import T_SLIP_TEMPLATE_CONFIG
from .medical_tax_credit import MEDICAL_TAX_CREDIT_TEMPLATE_CONFIG

PROMPT_TEMPLATES: Dict[str, PromptTemplateConfig] = {
    "t_slip_data_extraction": T_SLIP_TEMPLATE_CONFIG,
    "medical_tax_credit": MEDICAL_TAX_CREDIT_TEMPLATE_CONFIG,
}

DEFAULT_PROMPT_TEMPLATE = "t_slip_data_extraction"


def get_prompt_template(template_name: Optional[str] = None) -> PromptTemplateConfig:

    key = template_name or DEFAULT_PROMPT_TEMPLATE

    try:
        return PROMPT_TEMPLATES[key]
    except KeyError as exc:
        raise ValueError(f"Unknown prompt template '{key}'") from exc


def list_prompt_templates():

    templates = []

    for key, config in PROMPT_TEMPLATES.items():

        templates.append({
            "name": key,
            "label": config.name,
            "description": config.description,
            "icon": config.icon,
            "color": config.color,
            "steps": [
                {
                    "name": step.name,
                    "description": step.description,
                    "input_source": step.input_source,
                    "input_file_types": step.input_file_types,
                    "output_format": step.output_format,
                    "output_filename_template": step.output_filename_template,
                    "chunk_strategy": step.chunk_strategy,
                    "merge_chunk_results": step.merge_chunk_results,
                    "enable_web_search": step.enable_web_search,
                    "upload_to_zoho": step.upload_to_zoho,
                    "max_tokens": step.max_tokens,
                    "temperature": step.temperature
                }
                for step in config.steps
            ]
        })

    return templates
