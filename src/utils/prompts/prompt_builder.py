from src.utils.prompts.agent_prompts import FORMAT_BLOCK


class PromptBuilder:
    def __init__(
            self,
            base_system_prompt,
            agent_system_prompt,
            format_block,
            policy,
            context_data,
            backend_tools,
            rules_of_speaking
                 ):

        self.policy = policy
        self.base_system_prompt = base_system_prompt
        self.format_block = format_block
        self.context_data = context_data
        self.backend_tools = backend_tools
        self.rules_of_speaking = rules_of_speaking
        self.agent_system_prompt = agent_system_prompt

    def build_system_prompt(self):
        # return f"{self.base_system_prompt}\n\n{self.agent_system_prompt}"
        return self.base_system_prompt

    def build_developer_prompt(self):
        # потом через parts можно будет масштабировать поведение агентов - темперамент, имя, спец поведение и так далее
        parts = [
            f"***Agent role and behavior***\n{self.agent_system_prompt}",
            f"***Output Format***\n{self.format_block}"
            f"***Policy***\npolicy: {self.policy}",
            f"***Rules of speaking***\nrules_of_speaking: {self.rules_of_speaking}"
        ]

        if self.context_data is not None:
            parts.append(f"***Context_data***\ncontext_data: {self.context_data}")

        if self.backend_tools is not None:
            parts.append(f"***Data from API***\nbackend_tools: {self.backend_tools}")

        return "\n\n".join(parts)

    def build_messages(self):
        return [
            {
                "role": "system",
                "content": self.build_system_prompt()
            },

            {
                "role": "developer",
                "content": self.build_developer_prompt()
            }
        ]