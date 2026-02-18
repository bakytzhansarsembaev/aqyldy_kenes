# from src.utils.policies.policy_loader import IntentPolicy
from src.utils.gpt_utils import ask_gpt
from src.utils.prompts.prompt_builder import PromptBuilder
from src.configs.settings import gpt_5_2
from src.utils.prompts.agent_prompts import base_system_prompt, SYSTEM_PROMPTS, FORMAT_BLOCK


class BaseAgent:
    def __init__(self, intent, subintent, backend_tools, context_data, policy_loader, user_id,
                 previous_intent=None, previous_subintent=None):
        self.intent = intent
        self.subintent = subintent

        # backend APIшки
        self.user_id = user_id
        self.backend_tools = backend_tools

        # user_state
        self.context_data = context_data

        # контекст предыдущего диалога
        self.previous_intent = previous_intent
        self.previous_subintent = previous_subintent

        # загрузчик политик
        self.policy_loader = policy_loader
        self.policy = None

    def load_policy(self):
        self.policy = self.policy_loader.get_for(
            intent=self.intent,
            subintent=self.subintent
        )

        return self.policy

    def get_data_from_api(self):
        # дочерние субагенты будут цеплять инфу
        return {}

    def run_agent(self, user_message, summary):
        self.policy = self.load_policy()
        backend_data = self.get_data_from_api()

        prompt_builder = PromptBuilder(
            base_system_prompt=base_system_prompt,  # notice: добавить base_system_prompt
            agent_system_prompt=SYSTEM_PROMPTS.get((self.intent, self.subintent)),  # notice: добавить agent_system_prompt
            format_block=FORMAT_BLOCK,
            policy=self.policy.policy,
            context_data=self.context_data,
            # notice: переписать usable_context под дефолтные данные(не нужно менять на role, content)
            backend_tools=backend_data,
            rules_of_speaking=self.policy.rules_of_speaking,
            previous_intent=self.previous_intent,
            previous_subintent=self.previous_subintent
                                )

        messages = prompt_builder.build_messages()
        messages.append({"role": "assistant", "content": summary})
        messages.append({"role": "user", "content": user_message})

        # notice: delete after tests
        print("messages: ")
        for x in messages:
            print(x)

        response = ask_gpt(
            messages=messages,
            response_format=None,  # заменить на json_schema
            max_tok=500,
            model_gpt=gpt_5_2
        )

        return {
            "response": response,
            "intent": self.intent,
            "subintent": self.subintent,
            "backend_data": backend_data  # данные от API для сохранения в state
            # для дальнейшей оркестрации нужно добавить поле decision, поле confidence статус агента и т.д.
        }