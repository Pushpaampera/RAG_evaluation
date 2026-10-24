from laya import Router

print("Loading the local Laya model...")

router = Router()

state = {
    "question": "How many annual leave days are provided?",
    "retrieved_context": (
        "Employees receive 20 days of annual leave each year."
    ),
    "generated_answer": (
        "Employees receive 20 days of annual leave each year."
    ),
}

questions = {
    "faithfulness": {
        "type": "noul",
        "instructions": (
            "Are the factual claims in the generated answer "
            "supported by the retrieved context?"
        ),
    }
}

print("Evaluating the answer...")

result = router.predict(state, questions)

print("\nEvaluation result:")
print(result["answers"]["faithfulness"])

print("\nLocal Laya test completed successfully!")