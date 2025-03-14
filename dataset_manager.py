from typing import List, Any, Tuple
from langsmith import Client
from dataset_definitions import DatasetDefinitions

class DatasetManager:
    """
    A class to manage LangSmith datasets.
    """

    def __init__(self, client: Client = None):
        """
        Initialize the DatasetManager with a LangSmith client.
        
        Args:
            client: LangSmith client. If None, a new client will be created.
        """
        self.client = client or Client()
        self.example_datasets = DatasetDefinitions.get_all_datasets()


    def get_or_create_dataset(
            self,
            dataset_name: str,
            description: str = None
        ) -> Any:
        """
        Get an existing dataset by name or create a new one if it doesn't exist.
        
        Args:
            dataset_name: Name of the dataset to find or create
            description: Description for the new dataset if created
            
        Returns:
            Tuple of (dataset object, is_new flag)
        """
        dataset = next((ds for ds in self.client.list_datasets(dataset_name=dataset_name)), None)
        if dataset:
            print(f"Using existing dataset: {dataset.name} (ID: {dataset.id})")
            return dataset, False
        else:
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description=description or f"Dataset: {dataset_name}"
            )
            print(f"Created new dataset: {dataset.name} (ID: {dataset.id})")
            return dataset, True


    def add_examples(
            self,
            dataset_id: str,
            examples: List[Tuple[str, str]],
            input_key: str = "question",
            output_key: str = "answer"
        ) -> None:
        """
        Add examples to a dataset.
        
        Args:
            dataset_id: ID of the dataset to add examples to
            examples: List of (input, output) tuples
            input_key: Key for the input in the dataset
            output_key: Key for the output in the dataset
        """
        inputs = [{input_key: input_text} for input_text, _ in examples]
        outputs = [{output_key: output_text} for _, output_text in examples]

        self.client.create_examples(inputs=inputs, outputs=outputs, dataset_id=dataset_id)
        print(f"Added {len(examples)} examples to dataset")


    def list_datasets(
            self,
            name_filter: str = None
        ) -> List[Any]:
        """
        List all datasets, optionally filtered by name.
        
        Args:
            name_filter: Optional string to filter dataset names
            
        Returns:
            List of dataset objects
        """
        datasets = list(self.client.list_datasets(dataset_name=name_filter))
        return datasets


    def get_example_dataset(
            self,
            dataset_type: str
        ) -> List[Tuple[str, str]]:
        """
        Get a predefined example dataset by type.
        
        Args:
            dataset_type: Type of dataset to retrieve (e.g., "general_knowledge", "math", "coding")
            
        Returns:
            List of (input, output) tuples for the requested dataset type
        """
        if dataset_type not in self.example_datasets:
            available_types = ", ".join(self.example_datasets.keys())
            raise ValueError(
                f"Dataset type '{dataset_type}' not found. Available types: {available_types}"
            )

        return self.example_datasets[dataset_type]


    def create_dataset_from_examples(
            self,
            dataset_name: str,
            dataset_type: str,
            description: str = None
        ) -> Any:
        """
        Create a dataset using predefined examples.
        
        Args:
            dataset_name: Name for the dataset
            dataset_type: Type of predefined examples to use
            description: Optional description for the dataset
            
        Returns:
            The created dataset object
        """
        # Get the dataset or create it if it doesn't exist
        dataset, is_new = self.get_or_create_dataset(dataset_name, description)

        # Check if the dataset has examples
        examples_count = 0
        try:
            # Try to get the first example to check if the dataset has any
            examples_list = list(self.client.list_examples(dataset_id=dataset.id, limit=1))
            examples_count = len(examples_list)
        except Exception:
            # If there's an error, assume there are no examples
            examples_count = 0

        # Add examples if the dataset is new or has no examples
        if is_new or examples_count == 0:
            examples = self.get_example_dataset(dataset_type)
            self.add_examples(dataset.id, examples)
            print(f"Added {len(examples)} examples from '{dataset_type}' to dataset '{dataset_name}'")
        else:
            print(f"Dataset '{dataset_name}' already exists with examples. Skipping adding examples to avoid duplicates.")
        
        return dataset


    def add_custom_example_dataset(
            self,
            dataset_type: str,
            examples: List[Tuple[str, str]]
        ) -> None:
        """
        Add a custom example dataset to the available example datasets.
        
        Args:
            dataset_type: Name/type for the custom dataset
            examples: List of (input, output) tuples
        """
        self.example_datasets[dataset_type] = examples
        print(f"Added custom example dataset '{dataset_type}' with {len(examples)} examples")
