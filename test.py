from src.utils.policies.policy_loader import PolicyLoader

loader = PolicyLoader()

# Тест 1: Главный агент
policy1 = loader.get_for("task_problems", None)
print(f"Main policy: {policy1.description}")
assert policy1.policy.routing_logic is not None

# Тест 2: Helper агент
policy2 = loader.get_for("task_problems", "task_problems")
print(f"Helper policy: {policy2.description}")
assert len(policy2.policy.forbidden_actions) > 0

# Тест 3: Changer агент
policy3 = loader.get_for("task_problems", "change_task")
print(f"Changer policy: {policy3.description}")
assert len(policy3.policy.available_options) > 0

print("✅ Все политики загружены корректно!")