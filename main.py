from langsmith import wrappers, Client
from pydantic import BaseModel, Field
from openai import OpenAI
from dataset_manager import DatasetManager


def main():
    # Initialize clients
    client = Client()
    openai_client = wrappers.wrap_openai(OpenAI())

    dataset_manager = DatasetManager(client)
    dataset_manager.create_dataset_from_examples(
        dataset_name="Coding Dataset",
        dataset_type="coding",
        description="A dataset with coding questions and answers."
    )

    # Run evaluation on the general knowledge dataset
    run_evaluation(
        client=client,
        openai_client=openai_client,
        dataset_name="Coding Dataset"
    )


def target(inputs: dict, openai_client=None) -> dict:
    """
    Target function for evaluation.
    
    Args:
        inputs: Input dictionary with a question
        openai_client: OpenAI client
        
    Returns:
        Dictionary with the model's response
    """
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer the following question accurately"},
            {"role": "user", "content": inputs["question"]},
        ]
    )
    return {"response": response.choices[0].message.content.strip()}


def accuracy(outputs: dict, reference_outputs: dict) -> bool:
    """
    Evaluator function that checks accuracy of model responses.
    
    Args:
        outputs: Output from the target function
        reference_outputs: Reference outputs from the dataset
        
    Returns:
        Boolean indicating whether the response is accurate
    """
    # Define instructions for the LLM judge evaluator
    instructions = """
    Evaluate Student Answer against Ground Truth for conceptual similarity and classify true or false:
    - False: No conceptual match and similarity
    - True: Most or full conceptual match and similarity
    - Key criteria: Concept should match, not exact wording.
    """

    # Define output schema for the LLM judge
    class Grade(BaseModel):
        score: bool = Field(
            description="Boolean that indicates whether the response is accurate relative to the reference answer"
        )

    # Use OpenAI to evaluate
    openai_client = wrappers.wrap_openai(OpenAI())
    response = openai_client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": f"""Ground Truth answer: {reference_outputs["answer"]};
            Student's Answer: {outputs["response"]}"""}
        ],
        response_format=Grade
    )
    return response.choices[0].message.parsed.score


def run_evaluation(client, openai_client, dataset_name):
    """
    Run evaluation on a dataset.
    
    Args:
        client: LangSmith client
        openai_client: OpenAI client
        dataset_name: Name of the dataset to evaluate
    """
    # Create a wrapper for the target function that includes the OpenAI client
    def target_with_client(inputs: dict) -> dict:
        return target(inputs, openai_client)

    # Run the evaluation
    experiment_results = client.evaluate(
        target_with_client,
        data=dataset_name,
        evaluators=[
            accuracy,
            # can add multiple evaluators here
        ],
        experiment_prefix="langsmith-evaluation",
        max_concurrency=2,
    )

    print("Evaluation complete. View results in LangSmith.")
    return experiment_results

if __name__ == "__main__":
    main()
