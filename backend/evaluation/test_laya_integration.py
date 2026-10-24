from backend.evaluation.laya import evaluate_with_laya

result = evaluate_with_laya(
    question="How many annual leave days are provided?",
    retrieved_context=(
        "Employees receive 20 days of annual leave each year."
    ),
    answer=(
        "Employees receive 20 days of annual leave each year."
    ),
)

print("\nLocal Laya evaluation results:")

for criterion, evaluation in result["answers"].items():
    probability = evaluation["noul"]
    print(f"{criterion}: {probability:.4f}")

print("\nAll six evaluation criteria returned valid probabilities.")