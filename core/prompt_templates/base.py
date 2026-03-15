from dataclasses import dataclass, field
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate


@dataclass(frozen=True)
class PromptTemplateStep:

    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    input_source: str
    output_format: str
    output_filename_template: str
    chunk_strategy: str
    merge_chunk_results: bool
    enable_web_search: bool
    upload_to_zoho: bool
    max_tokens: int
    temperature: float
    input_file_types: Optional[str] = None
    max_pages_per_chunk: Optional[int] = None
    chat_prompt: ChatPromptTemplate = field(init=False)

    def __post_init__(self):

        human_prompt = (
            "You are provided with aggregated document summaries generated from the map stage.\n"
            "{summaries}\n\n"
            f"{self.user_prompt_template.strip()}\n\n"
            "Additional user instruction (may be blank):\n{user_instruction}"
        )

        object.__setattr__(
            self,
            "chat_prompt",
            ChatPromptTemplate.from_messages([
                ("system", self.system_prompt.strip()),
                ("human", human_prompt)
            ])
        )

    def format_messages(self, summaries: str, user_instruction: Optional[str]):

        return self.chat_prompt.format_messages(
            summaries=summaries,
            user_instruction=(user_instruction or "").strip()
        )


@dataclass(frozen=True)
class PromptTemplateConfig:

    name: str
    description: str
    icon: str
    color: str
    steps: List[PromptTemplateStep]

    @property
    def primary_step(self) -> PromptTemplateStep:

        return self.steps[0]
