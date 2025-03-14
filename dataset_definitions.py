from typing import List, Tuple, Dict

class DatasetDefinitions:
    """
    A class that defines various example datasets for evaluation.
    """

    @classmethod
    def get_all_datasets(cls) -> Dict[str, List[Tuple[str, str]]]:
        """
        Get all predefined datasets.
        
        Returns:
            Dictionary mapping dataset types to lists of (question, answer) tuples
        """
        return {
            "general_knowledge": cls.general_knowledge(),
            "math": cls.math(),
            "coding": cls.coding(),
            "science": cls.science(),
            "history": cls.history(),
            "literature": cls.literature()
        }

    @staticmethod
    def general_knowledge() -> List[Tuple[str, str]]:
        """
        General knowledge questions and answers.
        
        Returns:
            List of (question, answer) tuples
        """
        return [
            (
                "Which country is Mount Kilimanjaro located in?",
                "Mount Kilimanjaro is located in Tanzania."
            ),
            (
                "What is Earth's lowest point?",
                "Earth's lowest point is The Dead Sea."
            ),
            (
                "What is the largest ocean on Earth?",
                "The Pacific Ocean is the largest ocean on Earth."
            ),
            (
                "Which planet is known as the Red Planet?",
                "Mars is known as the Red Planet."
            ),
            (
                "What is the capital of the moon?",
                "There is no capital on the moon."
            )
        ]

    @staticmethod
    def math() -> List[Tuple[str, str]]:
        """
        Math questions and answers.
        
        Returns:
            List of (question, answer) tuples
        """
        return [
            (
                "What is the square root of 144?",
                "The square root of 144 is 12."
            ),
            (
                "If x + 5 = 12, what is x?",
                "x = 7"
            ),
            (
                "What is the area of a circle with radius 5?",
                "The area of a circle with radius 5 is 78.54 square units (25π)."
            ),
            (
                "What is the formula for the Pythagorean theorem?",
                "The Pythagorean theorem formula is a² + b² = c², where c is the hypotenuse."
            )
        ]

    @staticmethod
    def coding() -> List[Tuple[str, str]]:
        """
        Coding questions and answers.
        
        Returns:
            List of (question, answer) tuples
        """
        return [
            (
                "How do you define a function in Python?",
                "In Python, you define a function using the 'def' keyword followed by the function name, "
                "parameters in parentheses, and a colon. The function body is indented below."
            ),
            (
                "What is the difference between a list and a tuple in Python?",
                "Lists are mutable (can be changed after creation) while tuples are immutable "
                "(cannot be changed after creation). Lists use square brackets [] and tuples use parentheses ()."
            ),
            (
                "What does the 'self' parameter in Python class methods represent?",
                "The 'self' parameter in Python class methods refers to the instance of the class. "
                "It allows access to the attributes and methods of the class."
            ),
            (
                "What is a lambda function in Python?",
                "A lambda function is an anonymous function defined using the 'lambda' keyword. "
                "It can take any number of arguments but can only have one expression."
            )
        ]

    @staticmethod
    def science() -> List[Tuple[str, str]]:
        """
        Science questions and answers.
        
        Returns:
            List of (question, answer) tuples
        """
        return [
            (
                "What is the chemical symbol for gold?",
                "The chemical symbol for gold is Au."
            ),
            (
                "What is the process by which plants make their own food?",
                "Plants make their own food through photosynthesis."
            ),
            (
                "What is Newton's First Law of Motion?",
                "Newton's First Law of Motion states that an object at rest stays at rest and "
                "an object in motion stays in motion with the same speed and direction unless "
                "acted upon by an unbalanced force."
            ),
            (
                "What is the smallest unit of life?",
                "The cell is the smallest unit of life."
            )
        ]
    
    @staticmethod
    def history() -> List[Tuple[str, str]]:
        """
        History questions and answers.
        
        Returns:
            List of (question, answer) tuples
        """
        return [
            (
                "Who was the first President of the United States?",
                "George Washington was the first President of the United States."
            ),
            (
                "In what year did World War II end?",
                "World War II ended in 1945."
            ),
            (
                "What ancient civilization built the pyramids at Giza?",
                "The ancient Egyptians built the pyramids at Giza."
            ),
            (
                "Who wrote the Declaration of Independence?",
                "Thomas Jefferson was the principal author of the Declaration of Independence."
            )
        ]

    @staticmethod
    def literature() -> List[Tuple[str, str]]:
        """
        Literature questions and answers.
        
        Returns:
            List of (question, answer) tuples
        """
        return [
            (
                "What is the capital of France?",
                "The capital of France is Paris."
            ),
            (
                "Who wrote 'Romeo and Juliet'?",
                "William Shakespeare wrote 'Romeo and Juliet'."
            ),
            (
                "Who is the author of 'To Kill a Mockingbird'?",
                "Harper Lee is the author of 'To Kill a Mockingbird'."
            ),
            (
                "What is the first book in J.K. Rowling's wizarding series?",
                "Harry Potter and the Philosopher's Stone (or Sorcerer's Stone in the US) is the first book."
            )
        ]
