# string_utils.py
greeting = "Hello"
farewell = "Goodbye"

def to_uppercase(text):
    """Convert text to uppercase."""
    return text.upper()

def to_lowercase(text):
    """Convert text to lowercase."""
    return text.lower()

def reverse_string(text):
    """Reverse the given string."""
    return text[::-1]

def count_vowels(text):
    """Count the number of vowels in a string."""
    vowels = "aeiouAEIOU"
    return sum(1 for char in text if char in vowels)
